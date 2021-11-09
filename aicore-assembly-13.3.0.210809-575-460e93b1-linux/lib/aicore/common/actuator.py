"""Handling of HTTP/1.1 endpoints in similar way as Java/Spring platform modules."""

from __future__ import annotations

import itertools
import urllib.parse

from typing import TYPE_CHECKING

import requests
import tenacity

from aicore.common.constants import CORRELATION_ID_HEADER
from aicore.common.http import HTTPClient, create_url, parse_retryable_reason
from aicore.common.registry import LogId
from aicore.common.resource import ReadinessDependency, RuntimeState
from aicore.common.tls import ClientTLSConfig, TLSConfigType
from aicore.common.utils import random_correlation_id, timestamp_str


if TYPE_CHECKING:
    from typing import Any, Optional

    from aicore.common.config import Config
    from aicore.common.logging import Logger
    from aicore.common.microservice import Microservice
    from aicore.common.types import CorrelationId, WSGIResponse
    from aicore.common.wsgi import WSGIServer


def microservice_actuator_client(microservice_name: str, config: Config, path: str) -> HTTPClient:
    """Provide a HTTP client for querying microservice's health."""
    host = getattr(config, f"{microservice_name}_host")
    port = getattr(config, f"{microservice_name}_http_port")
    tls_config = ClientTLSConfig(TLSConfigType.HTTP, microservice_name, config)

    url = create_url(host, port, path, tls_config.enabled)
    return HTTPClient(url, tls_config)


def microservice_health_check(microservice_name: str, config: Config, logger: Logger, timeout: int):
    """Check if given microservice is alive."""
    http_client = microservice_actuator_client(microservice_name, config, Actuator.LIVENESS_PATH)

    correlation_id = random_correlation_id()
    headers = {CORRELATION_ID_HEADER: correlation_id}

    try:
        response = http_client.get(headers=headers, timeout=timeout)
    except (requests.ConnectionError, requests.HTTPError, requests.Timeout) as error:
        logger.error(
            "Failed to check the health of microservice {name!r} via {url!r}: {error}",
            name=microservice_name,
            url=http_client.url,
            error=error,
            correlation_id=correlation_id,
            message_id=LogId.health_check_unavailable,
        )

        return False

    is_alive = response.status_code == 200

    if not is_alive:
        logger.error(
            "Microservice {name!r} is not healthy according to {url!r} (status {http_status}): {details!r}",
            name=microservice_name,
            http_status=response.raw.status_code,
            details=response.raw.text,
            correlation_id=correlation_id,
            message_id=LogId.health_check_not_alive,
        )

    return is_alive


class Actuator:
    """Handle HTTP/1.1 endpoints in similar way as Spring Boot."""

    ACTUATOR_PATH = "/actuator"
    INFO_PATH = "/actuator/info"
    METRICS_PATH = "/actuator/prometheus"
    HEALTH_PATH = "/actuator/health"
    LIVENESS_PATH = "/actuator/health/liveness"
    READINESS_PATH = "/actuator/health/readiness"

    PUBLIC_PATHS = {ACTUATOR_PATH, INFO_PATH, HEALTH_PATH, LIVENESS_PATH, READINESS_PATH}

    PATHS = {
        "self": ACTUATOR_PATH,
        "info": INFO_PATH,
        "prometheus": METRICS_PATH,
        "health": HEALTH_PATH,
        "liveness": LIVENESS_PATH,
        "readiness": READINESS_PATH,
    }

    def __init__(self, microservice: Microservice, wsgi_server: WSGIServer):
        self.microservice = microservice
        self.wsgi_server = wsgi_server

        self.wsgi_application = self.wsgi_server.wsgi_application  # Handles the generic HTTP boilerplate
        # See also https://spring.io/blog/2020/03/25/liveness-and-readiness-probes-with-spring-boot
        self.handlers = {
            self.ACTUATOR_PATH: self.handle_actuator,
            self.INFO_PATH: self.handle_info,
            self.HEALTH_PATH: self.handle_health,
            self.LIVENESS_PATH: self.handle_liveness,
            self.READINESS_PATH: self.handle_readiness,
            self.METRICS_PATH: self.handle_metrics,
        }

        self.no_accesslog = {self.LIVENESS_PATH, self.READINESS_PATH, self.METRICS_PATH}  # Prevent spamming the log

    def url(self, path: str) -> str:
        """Provide URL for given path."""
        host = getattr(self.microservice.config, f"{self.microservice.name}_host")
        port = getattr(self.microservice.config, f"{self.microservice.name}_server_http_port")

        return f"{'https' if self.wsgi_server.tls_config.enabled else 'http'}://{host}:{port}{path}"

    def handle_actuator(self, _environ: dict[str, Any]) -> WSGIResponse:
        """Handle the actuator endpoint."""
        # See https://spring.io/guides/topicals/spring-on-kubernetes/
        payload = {"_links": {name: {"href": self.url(path), "templated": False} for name, path in self.PATHS.items()}}

        return self.wsgi_application.handle_json_200(payload)

    def handle_info(self, _environ: dict[str, Any]) -> WSGIResponse:
        """Handle the info endpoint."""
        # See https://www.baeldung.com/spring-boot-info-actuator-custom
        payload = {
            "app": {
                "description": f"Ataccama One 2.0 - AI Core - {self.microservice.name}",
                "version": self.microservice.version,
                "microservice": self.microservice.name,
            }
        }

        return self.wsgi_application.handle_json_200(payload)

    def handle_health(self, _environ: dict[str, Any]) -> WSGIResponse:
        """Handle the health endpoint."""
        components = {}
        ready = True

        for resource in itertools.chain(self.microservice.all_resources, [self.microservice]):
            if resource.health.state == RuntimeState.RUNNING:
                status = "UP"
            else:
                status = "OUT_OF_SERVICE"
                ready = False

            last_alive = timestamp_str(resource.health.last_alive)
            components[resource.name] = {
                "status": status,
                "details": {
                    "lastAlive": last_alive,
                    "details": resource.health.details,
                },
            }

        # Not used by Kubernetes, may be manually called by operator, contains additional details
        payload = {
            "status": "UP" if ready else "OUT_OF_SERVICE",
            "startupDate": self.microservice.startup_time,
            "components": components,
            "groups": ["liveness", "readiness"],
        }

        # HTTP code doesn't depend on the readiness of the microservice
        return self.wsgi_application.handle_json_200(payload)

    def handle_liveness(self, _environ: dict[str, Any]) -> WSGIResponse:
        """Handle the liveness endpoint."""
        components = {}

        for resource in itertools.chain(self.microservice.all_resources, [self.microservice]):
            if resource.health.tracks_liveness:
                components[resource.name] = {
                    "status": "UP",  # Spring treats not ready service as "UP" (alive)
                    "details": {"lastAlive": timestamp_str(resource.health.last_alive)},
                }

        # Emulation of Spring Boot, not machine-parsed (response code is the only thing that matters to Kubernetes)
        payload = {"status": "UP", "components": components}

        # Microservice able to reply is alive, not alive microservice shuts itself down
        return self.wsgi_application.handle_json_200(payload)

    def handle_readiness(self, _environ: dict[str, Any]) -> WSGIResponse:
        """Handle the readiness endpoint."""
        components = {}
        ready = True
        handler = self.wsgi_application.handle_json_200

        for resource in itertools.chain(self.microservice.all_resources, [self.microservice]):
            if resource.health.state == RuntimeState.RUNNING:
                status = "UP"
            else:
                status = "OUT_OF_SERVICE"
                ready = False
                handler = self.wsgi_application.handle_json_503

            last_alive = timestamp_str(resource.health.last_alive)
            components[resource.name] = {"status": status, "details": {"lastAlive": last_alive}}

        # Emulation of Spring Boot, not machine-parsed (response code is the only thing that matters to Kubernetes)
        payload = {"status": "UP" if ready else "OUT_OF_SERVICE", "components": components}

        return handler(payload)

    # Based on prometheus_client.exposition.make_wsgi_app.prometheus_app()
    def handle_metrics(self, environ: dict[str, Any]) -> WSGIResponse:
        """Handle the metrics endpoint."""
        requested_formats = environ.get("HTTP_ACCEPT", "")
        query = urllib.parse.parse_qs(environ.get("QUERY_STRING", ""))

        format_type = "prometheus_plaintext"  # Preferred (but the customers may insist on OpenMetrics)
        for format_types in requested_formats.split(","):
            if format_types.split(";")[0].strip() == "application/openmetrics-text":
                format_type = "openmetrics_plaintext"
                break

        payload, content_type = self.microservice.metrics.dump(format_type, query)

        return self.wsgi_application.handle_200(payload, content_type)


class ExternalDependency(ReadinessDependency):
    """Wait until an external service gets ready."""

    def __init__(
        self,
        name: str,
        logger: Logger,
        onstart_retrying: tenacity.Retrying,
        host: str,
        port: str,
        tls_config: ClientTLSConfig,
        get_timeout: float,
    ):
        super().__init__(name, logger, onstart_retrying, readiness_predicate=self.is_ready, tracks_liveness=False)

        self.host = host
        self.port = port
        self.tls_config = tls_config
        self.get_timeout = get_timeout

        url = create_url(self.host, self.port, Actuator.READINESS_PATH, self.tls_config.enabled)
        self.http_client = HTTPClient(url, self.tls_config)

        self.correlation_id: Optional[CorrelationId] = None

    def __repr__(self):
        return f"External dependency {self.name!r} ({self.http_client.url!r})"

    def is_ready(self) -> bool:
        """Return True if the external service reports itself as ready."""
        self.correlation_id = random_correlation_id()
        headers = {CORRELATION_ID_HEADER: self.correlation_id}

        try:
            result = self.http_client.get(headers=headers, timeout=self.get_timeout)
        except requests.RequestException as error:
            reason = parse_retryable_reason(error)

            if not reason:
                raise error

            self.health.not_ready(reason)
            return False

        # See https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#container-probes
        if not 200 <= result.status_code < 400:
            self.health.not_ready(f"Status code is {result.status_code}, should be >= 200 and < 400.")
            return False

        return True

    def prepare_state_change_log_record(self) -> tuple[str, dict[str, Any]]:
        """Return log message and kwargs appropriate for the new state the dependency is in."""
        if self.health.state not in {RuntimeState.NOT_READY, RuntimeState.RUNNING}:
            return "", {}  # Don't log anything in other states

        kwargs = {"event_id": LogId.dependency_state_change}
        if self.correlation_id:
            kwargs["correlation_id"] = self.correlation_id

        return "{self!r} is {health!r}", kwargs
