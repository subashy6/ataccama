"""Tools for checking status of AI-Core microservices."""

from __future__ import annotations

import collections
import contextlib

from typing import TYPE_CHECKING

import requests

from aicore.common.actuator import Actuator, microservice_actuator_client
from aicore.common.auth import InternalJWTGenerator
from aicore.common.config import Config
from aicore.common.constants import CORRELATION_ID_HEADER, STATE_CHANGE_TIMEOUT
from aicore.common.graphql import GraphQLClient, GraphQLResponseException
from aicore.common.grpc import GRPCClient, GRPCClientError
from aicore.common.http import HTTPClient
from aicore.common.logging import LogConfig, Logger
from aicore.common.metrics import MetricsDAO
from aicore.common.tls import ClientTLSConfig, TLSConfigType
from aicore.common.utils import random_correlation_id
from aicore.term_suggestions.commands import GetTopKNeighborsCommand


if TYPE_CHECKING:
    from collections import Iterable
    from typing import Any


AuthStatus = collections.namedtuple("AuthStatus", ["status", "details"])
successful_auth_status = AuthStatus("UP", "")


def get_microservice_status(status_client: HTTPClient, timeout: int = 5) -> dict[str, Any]:
    """Query microservice for its status."""
    correlation_id = random_correlation_id()
    headers = {CORRELATION_ID_HEADER: correlation_id}

    response = {}
    with contextlib.suppress(requests.ConnectionError, requests.HTTPError, requests.Timeout):
        response = status_client.get(headers=headers, timeout=timeout).json()

    return response


def parse_microservice_status(microservice_name: str, microservice_status: dict[str, Any]) -> tuple[dict, dict]:
    """Parse status information of a microservice and its dependencies."""
    if not microservice_status:
        return {"Microservice": microservice_name, "Status": "UNAVAILABLE", "Dependencies": ""}, {}

    IGNORED_DEPENDENCIES = [microservice_name, "server", "_grpc_client"]

    dependencies = {}
    for dependency_name, dependency_info in microservice_status["components"].items():
        if any(ignored in dependency_name for ignored in IGNORED_DEPENDENCIES):
            continue

        CLIENT_SUFFIX = "_client"
        if CLIENT_SUFFIX in dependency_name:
            dependency_name = dependency_name.removesuffix(CLIENT_SUFFIX)

        dependencies[dependency_name] = {
            "Dependency": dependency_name,
            "Status": dependency_info["status"],
            # Some exceptions contain tabs that interfere with `tabulate` formatting
            "Details": dependency_info["details"]["details"].replace("\t", ""),
        }

    status = {
        "Microservice": microservice_name,
        "Status": microservice_status["status"],
        "Dependencies": ", ".join(dependency for dependency in dependencies),
    }

    return status, dependencies


def get_microservices_status(microservice_names: Iterable[str], config: Config) -> tuple[list, dict]:
    """Retrieve status of microservices and their dependencies."""
    microservices_status = []
    dependency_status = {}

    for microservice_name in microservice_names:
        status_client = microservice_actuator_client(microservice_name, config, Actuator.HEALTH_PATH)
        microservice_health = get_microservice_status(status_client)

        status, dependencies = parse_microservice_status(microservice_name, microservice_health)
        microservices_status.append(status)
        # Multiple microservices may depend on the same external dependency with the same status/info
        # Since microservices status is retrieved sequentially, the last dependency info is used
        dependency_status |= dependencies

    return microservices_status, dependency_status


def get_authentication_status(config: Config) -> dict[str, Any]:
    """Retrieve status of authentication for internal communication and MMM."""
    name = "authentication_client"

    log_config = LogConfig()
    log_config.mode = {}  # Silence the logger
    logger = Logger(name, log_config)

    jwt_generator = InternalJWTGenerator.from_jwk(config.jwk, config.jwt_expiration)
    metrics = MetricsDAO()

    internal_grpc_auth = attempt_internal_grpc_auth(name, logger, config, jwt_generator, metrics)
    mmm_http_auth = attempt_mmm_http_auth(name, logger, config, jwt_generator, metrics)

    return {
        "Authentication": ["Internal AI-Core gRPC", "MMM HTTP"],
        "Status": [internal_grpc_auth.status, mmm_http_auth.status],
        "Details": [internal_grpc_auth.details, mmm_http_auth.details],
    }


def attempt_mmm_http_auth(
    name: str, logger: Logger, config: Config, jwt_generator: InternalJWTGenerator, metrics: MetricsDAO
) -> AuthStatus:
    """Attempt to authenticate with MMM over HTTP and provide query results."""
    mmm_tls_config = ClientTLSConfig(TLSConfigType.HTTP, "mmm", config)
    graphql_client = GraphQLClient(
        name, logger, config.mmm_host, config.mmm_http_port, jwt_generator, mmm_tls_config, metrics
    )

    try:
        graphql_client.send("{ _modelMetadata { modelHcn } }", random_correlation_id())
    except GraphQLResponseException as error:
        if error.status_code == requests.codes.unauthorized:
            return AuthStatus(error.status_code, error.reason)

    return successful_auth_status


def attempt_internal_grpc_auth(
    name: str, logger: Logger, config: Config, jwt_generator: InternalJWTGenerator, metrics: MetricsDAO
) -> AuthStatus:
    """Attempt to authenticate with a microservice over gRPC and provide query results."""
    neighbors_tls_config = ClientTLSConfig(TLSConfigType.gRPC, "neighbors", config)
    grpc_client = GRPCClient(
        name, logger, config.neighbors_host, config.neighbors_grpc_port, jwt_generator, neighbors_tls_config, metrics
    )

    try:
        with grpc_client.running(STATE_CHANGE_TIMEOUT):
            command = GetTopKNeighborsCommand(attributes=[])
            grpc_client.send(command, random_correlation_id())
    except GRPCClientError as error:
        # Reason for failure should be in the underlying RPC exception
        # See GRPCClient.send() for more info
        return AuthStatus(error.__cause__.code().name, error.__cause__.details())

    return successful_auth_status
