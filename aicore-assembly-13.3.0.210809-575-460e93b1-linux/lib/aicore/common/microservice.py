"""Life-cycle management of a microservice and its background threads."""

from __future__ import annotations

import itertools
import json
import platform
import random
import re
import subprocess
import sys
import threading
import time

from typing import TYPE_CHECKING

import tenacity

from aicore.common import docker
from aicore.common.actuator import Actuator, ExternalDependency
from aicore.common.auth import (
    AllowedRolesAuthenticator,
    AuthorizationHeaderAuthenticatorContainer,
    BasicAuthAuthenticator,
    InternalJWTAuthenticator,
    InternalJWTGenerator,
    JWTAuthenticator,
    KeycloakClient,
    KeycloakConfig,
)
from aicore.common.command import ShutdownServiceCommand
from aicore.common.config import ConfigServiceClient, ConfigurationError
from aicore.common.constants import RESPONSIVENESS_PERIOD
from aicore.common.graphql import GraphQLClient
from aicore.common.grpc import GRPCClient, GRPCServer
from aicore.common.logging import LogConfig, Logger
from aicore.common.metrics import MetricsDAO
from aicore.common.registry import LogId, MicroserviceMetric
from aicore.common.resource import (
    BackgroundThread,
    Health,
    Resources,
    ResourceShutdownError,
    ResourceStartError,
    RuntimeState,
)
from aicore.common.retry import EventAwareRetrying
from aicore.common.tls import ClientTLSConfig, ServerTLSConfig, TLSConfigType
from aicore.common.utils import (
    ant_path_to_regex,
    datetime_now,
    datetime_str,
    get_signal_name,
    get_thread_limits,
    load_version,
    random_correlation_id,
    set_dynamic_thread_limits,
)
from aicore.common.wsgi import WSGIServer


if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from aicore.common.resource import Resource


class Microservice:
    """Docker container or bare-metal process handling use cases of a bounded context."""

    def __init__(self, name, config, period=1):
        # Child classes are expected to call super().__init__() before running their own constructor
        # Child classes should not contain any if statements or exception handling (hide them inside the commands)
        self.name = name
        self.config = config
        # Beware - should be less then `config_service_refresh_interval` and `config_service_heartbeat_interval`
        self.period = period  # [s], process_once_per_period() is called at most once during each period

        set_dynamic_thread_limits(self.config.threads)  # Static limits had to be set sooner, before importing NumPy

        self.version = load_version(self.config.artifact_version_txt_location)
        self.logger = Logger(self.name, LogConfig.from_config(self.config), self.version)
        self.operational_resources = Resources()  # Require the microservice to be operational to function
        self.contained_resources = Resources()  # Do not require anything to function
        self.health = Health()

        self.startup_time = datetime_str(datetime_now(), "seconds")
        self.heartbeat_timeout = config.heartbeat_timeout  # [s]

        self.metrics = MetricsDAO()
        self.metrics.register(MicroserviceMetric)
        self.metrics.add_info(
            MicroserviceMetric.microservice, app="one20", component="ai-core", name=self.name, version=self.version
        )

        self.config_service_client: ConfigServiceClient = self.config.properties_loader.config_service_client
        if self.config_service_client:
            self.contained_resources.add(self.config_service_client.grpc_client)

        # Lock between Microservice.process() and Command.process() (in ThreadPool on gRPC server)
        self.process_lock = threading.Lock()

        # Set when microservice is about to shut down (i.e. when shutdown() is called)
        self.about_to_shutdown = threading.Event()
        self.about_to_shutdown_events = [self.about_to_shutdown]

        self.jwt_generator = InternalJWTGenerator.from_jwk(config.jwk, config.jwt_expiration)
        self.keycloak_client = None
        self.enabled_grpc_authenticators = self.enabled_authenticators("grpc")
        self.enabled_http_authenticators = self.enabled_authenticators("http")

        self.background_thread(name=f"{self.name}_processing_thread", callback=self.run_processing_forever)

    def __enter__(self):
        """Start the microservice."""
        with self.logger.action(LogId.microservice_bootstrap, _color="<green><bold>") as action:
            action.start("*** Service {name!r}:{version!r} is starting ***", name=self.name, version=self.version)
            action.info(
                "Platform info: {platform_info}",
                platform_info=self.platform_info(),
                message_id=LogId.microservice_platform_info,
                _color="<white><dim>",
            )
            action.info(
                "PIP packages: {packages}",
                packages=self.installed_packages(),
                message_id=LogId.microservice_pip_packages,
                _color="<white><dim>",
            )
            action.info(
                "Thread limits: {threads} Threadpoolctl, {jobs} Joblib, {omp} OpenMP, {blas} OpenBLAS, effective: {limits!r}",  # noqa: E501
                threads=self.config.threads,
                jobs=self.config.jobs,
                omp=self.config.omp,
                blas=self.config.blas,
                limits=get_thread_limits(),
                message_id=LogId.microservice_thread_limits,
                _color="<white><dim>",
            )

            try:
                self.contained_resources.start(action, self.about_to_shutdown)
                with self.process_lock:
                    self.on_start()
                self.operational_resources.start(action, self.about_to_shutdown)
            except ResourceStartError as error:
                self.shutdown(error=True)
                action.exception(
                    "Resources {resources!r} failed to start",
                    resources=list(error.resource_names),
                    error=error,
                    event_id=LogId.microservice_resources_start_failed,
                )
            except Exception as error:
                self.shutdown(error=True)
                action.exception(
                    "Unhandled exception raised while starting {name!r} service",
                    name=self.name,
                    error=error,
                    event_id=LogId.microservice_start_error,
                )
            else:
                self.health.running()
                action.finish("*** Service {name!r} successfully started and is ready ***", name=self.name)

        return self

    def __exit__(self, exc_type, exc_value, _traceback):
        """Shut down the microservice."""
        if exc_type:
            self.health.shutting_down(error=True)
            self.logger.exception(
                "Service {name!r} raised an unhandled exception",
                name=self.name,
                error=exc_value,
                event_id=LogId.microservice_error,
            )

        with self.logger.action(LogId.microservice_shutdown, _color="<green><bold>") as action:
            self.health.shutting_down()
            action.start("*** Service {name!r} is gracefully shutting down ***", name=self.name)

            cancel_wait = threading.Event()
            self.about_to_shutdown_events.append(cancel_wait)

            try:
                self.operational_resources.shutdown(action, cancel_wait)
                with self.process_lock:
                    self.on_shutdown()
                self.contained_resources.shutdown(action, cancel_wait)
            except ResourceShutdownError as error:
                self.health.stopped(error=True)
                action.exception(
                    "Resource {resources!r} failed to shut down",
                    resources=list(error.resource_names),
                    error=error,
                    event_id=LogId.microservice_resources_shutdown_failed,
                )
            except Exception as error:
                self.health.stopped(error=True)
                action.exception(
                    "Unhandled exception raised while shutting down {name!r} service",
                    name=self.name,
                    error=error,
                    event_id=LogId.microservice_shutdown_error,
                )
            else:
                self.health.stopped()
                action.finish("*** Service {name!r} successfully shut down ***", name=self.name)

        self.logger.shutdown()

        return True  # Do not propagate the exceptions outside of the context

    @property
    def all_resources(self) -> Iterator[Resource]:
        """Return an iterator of all resources of the microservice."""
        return itertools.chain(self.operational_resources, self.contained_resources)

    def background_thread(self, name: str, callback: Callable[[Health], None], tracks_liveness: bool = True):
        """Create a background thread with managed life-cycle and health state."""
        background_thread = BackgroundThread(name, self.logger, callback, tracks_liveness=tracks_liveness)
        # Processing thread needs to start only after all other resources are running,
        # otherwise using the resources will fail (e.g. pulling from DB)
        self.operational_resources.add(background_thread)

        return background_thread

    def grpc_server(self, host=None, port=None, commands=()):
        """Create a gRPC server with managed life-cycle and health state."""
        host = host or getattr(self.config, f"{self.name}_server_grpc_host")
        port = port or getattr(self.config, f"{self.name}_server_grpc_port")
        max_message_size = self.config.server_grpc_max_message_size

        service_commands = [ShutdownServiceCommand]  # always present commands
        authenticator = AuthorizationHeaderAuthenticatorContainer(self.enabled_grpc_authenticators)
        tls_config = ServerTLSConfig(TLSConfigType.gRPC, self.config)

        server = GRPCServer(
            name="grpc_server",
            host=host,
            port=port,
            commands=itertools.chain(commands, service_commands),
            microservice=self,
            logger=self.logger,
            authenticator=authenticator,
            tls_config=tls_config,
            metrics=self.metrics,
            max_message_size=max_message_size,
        )
        self.operational_resources.add(server)

        return server

    def grpc_client(self, connection_name, host=None, port=None):
        """Create a gRPC client with managed life-cycle and health state."""
        name = f"{connection_name}_grpc_client"
        host = host or getattr(self.config, f"{connection_name}_host")
        port = port or getattr(self.config, f"{connection_name}_grpc_port")
        max_message_size = self.config.client_grpc_max_message_size

        tls_config = ClientTLSConfig(TLSConfigType.gRPC, connection_name, self.config)
        client = GRPCClient(
            name,
            self.logger,
            host,
            port,
            self.jwt_generator,
            tls_config,
            self.metrics,
            self.retrying_controller(),
            max_message_size,
        )
        self.contained_resources.add(client)

        return client

    def graphql_client(self, connection_name, host=None, port=None):
        """Create a GraphQL client for given URL."""
        name = f"{connection_name}_graphql_client"
        host = host or getattr(self.config, f"{connection_name}_host")
        port = port or getattr(self.config, f"{connection_name}_http_port")

        tls_config = ClientTLSConfig(TLSConfigType.HTTP, connection_name, self.config)

        return GraphQLClient(
            name,
            self.logger,
            host,
            port,
            self.jwt_generator,
            tls_config,
            self.metrics,
            self.config.connect_timeout,
            self.retrying_controller(),
        )

    def wsgi_server(self, host=None, port=None):
        """Create a synchronous multi-threaded HTTP/1.1 WSGI-compatible server."""
        host = host or getattr(self.config, f"{self.name}_server_http_host")
        port = port or getattr(self.config, f"{self.name}_server_http_port")

        tls_config = ServerTLSConfig(TLSConfigType.HTTP, self.config)

        server = WSGIServer(
            name="wsgi_server",
            host=host,
            port=port,
            tls_config=tls_config,
            logger=self.logger,
            metrics=self.metrics,
        )
        self.contained_resources.add(server)
        self.actuator = Actuator(self, server)

        authenticators = {}
        restricted_public_paths = (
            # Splitting isn't done during the config parsing in order not to influence publicly visible string type
            self.config.public_endpoint_restriction_filter.split(";")
            if self.config.public_endpoint_restriction_filter  # Can be None - property is set to `null`
            else []
        )

        for endpoint in self.actuator.handlers:
            if endpoint not in self.actuator.PUBLIC_PATHS:
                authenticators[endpoint] = self.create_http_authenticator(endpoint)
                continue

            for ant_path in restricted_public_paths:
                pattern = ant_path_to_regex(ant_path)

                if re.search(pattern, endpoint):
                    authenticators[endpoint] = self.create_http_authenticator(endpoint)
                    break

        server.wsgi_application.handlers = self.actuator.handlers
        server.wsgi_application.authenticators = authenticators
        server.wsgi_application.no_accesslog = self.actuator.no_accesslog

        return server

    def create_http_authenticator(self, endpoint_path):
        """Create authenticator for HTTP endpoint."""
        endpoint_authenticators = {}

        for scheme, ant_paths in {
            BasicAuthAuthenticator.SCHEME: self.config.http_auth_basic_filter,
            JWTAuthenticator.SCHEME: self.config.http_auth_bearer_filter,
            InternalJWTAuthenticator.SCHEME: self.config.http_auth_internal_jwt_filter,
        }.items():
            authenticator = self.enabled_http_authenticators.get(scheme)

            if not authenticator:
                continue

            # Splitting isn't done during the config parsing in order not to influence publicly visible string type
            for ant_path in ant_paths.split(";"):
                pattern = ant_path_to_regex(ant_path)

                if re.search(pattern, endpoint_path):
                    endpoint_authenticators[scheme] = authenticator
                    break

        http_acl_endpoints = self.config.http_acl_endpoints or {}
        allowed_roles = set()

        for acl_endpoint in http_acl_endpoints.values():
            if endpoint_path in acl_endpoint["endpoint_paths"]:
                allowed_roles.update(acl_endpoint["allowed_roles"])

        authenticator_container = AuthorizationHeaderAuthenticatorContainer(endpoint_authenticators)

        return AllowedRolesAuthenticator(allowed_roles, self.config.http_acl_default_allow, authenticator_container)

    def enabled_authenticators(self, protocol: str):
        """Create authenticators based on config for given protocol."""
        internal_jwt = getattr(self.config, f"{protocol}_auth_internal_jwt")
        basic = getattr(self.config, f"{protocol}_auth_basic")
        bearer = getattr(self.config, f"{protocol}_auth_bearer")

        authenticators = []

        if internal_jwt:
            internal_authenticator = InternalJWTAuthenticator(
                self.config.platform_deployments, self.config.impersonation_role
            )
            authenticators.append(internal_authenticator)

        jwt_authenticator = None

        if basic or bearer:
            if not self.keycloak_client:
                keycloak_config = KeycloakConfig(self.config)
                tls_config = ClientTLSConfig(TLSConfigType.HTTP, "keycloak", self.config)

                self.keycloak_client = KeycloakClient(
                    "keycloak_client",
                    self.logger,
                    keycloak_config,
                    tls_config,
                    onstart_retrying=self.retrying_controller(on_start=True),
                    retrying=self.retrying_controller(),
                )
                self.contained_resources.add(self.keycloak_client)

            jwt_authenticator = JWTAuthenticator(
                self.keycloak_client,
                self.config.keycloak_token_issuer,
                self.config.keycloak_token_audience,
                self.config.keycloak_token_expected_algorithm,
            )

        if bearer:
            authenticators.append(jwt_authenticator)

        if basic:
            basic_authenticator = BasicAuthAuthenticator(self.keycloak_client, jwt_authenticator)
            authenticators.append(basic_authenticator)

        return {authenticator.SCHEME: authenticator for authenticator in authenticators}

    def retrying_controller(self, on_start: bool = False) -> EventAwareRetrying:
        """Create a retrying controller."""
        if on_start:
            wait_class = getattr(tenacity, self.config.onstart_retrying_wait_type)
            kwargs = {
                "wait": wait_class(**self.config.onstart_retrying_wait_kwargs),
            }
        else:
            wait_class = getattr(tenacity, self.config.retrying_wait_type)
            stop_class = getattr(tenacity, self.config.retrying_stop_type)
            kwargs = {
                "wait": wait_class(**self.config.retrying_wait_kwargs),
                "stop": stop_class(**self.config.retrying_stop_kwargs),
            }

        return EventAwareRetrying(self.about_to_shutdown, **kwargs)

    def add_external_dependency(self, target: str) -> None:
        """Make the microservice wait for readiness of the target when starting."""
        host = getattr(self.config, f"{target}_host")
        port = getattr(self.config, f"{target}_http_port")
        tls_config = ClientTLSConfig(TLSConfigType.HTTP, target, self.config)

        dependency = ExternalDependency(
            target,
            self.logger,
            self.retrying_controller(on_start=True),
            host,
            port,
            tls_config,
            self.config.onstart_health_response_timeout,
        )
        self.contained_resources.add(dependency)

    def database(self):
        """Create a database."""
        # Not all microservice require a DB, so the `common.database` import should be function scoped
        # as to not import sqlalchemy/alembic implicitly (adds extra ~13MB to memory consumption)
        from aicore.common.database import Database, get_latest_schema_version

        database = Database(
            "db",
            self.logger,
            self.config.connection_string,
            get_latest_schema_version(self.config.migrations_path),
            self.metrics,
            onstart_retrying=self.retrying_controller(on_start=True),
            retrying=self.retrying_controller(),
            **self.config.engine_kwargs,
        )
        self.contained_resources.add(database)

        return database

    def process_frequently(self) -> bool:
        """Process a reasonably short unit of work and return True if there is no remaining work to be done."""
        return True  # Template method - optionally to be implemented by child classes

    def process_config_reload(self, new_config):
        """Process changes in configuration and reflect in Config which changes were applied."""
        for authenticator in itertools.chain(
            self.enabled_grpc_authenticators.values(),
            self.enabled_http_authenticators.values(),
        ):
            authenticator.process_config_reload(new_config)

    def process_once_per_period(self) -> None:
        """Perform a reasonably short housekeeping; called at most once per period."""
        pass  # Template method - optionally to be implemented by child classes

    def on_start(self):
        """Start all asynchronous components of the microservice."""
        pass  # Template method - optionally to be implemented by child classes

    def on_shutdown(self):
        """Gracefully shut down all stateful components of the microservice."""
        pass  # Template method - optionally to be implemented by child classes

    def run_forever(self):
        """Periodically check state of resources, ping Config Service and update own health."""
        while self.health.state == RuntimeState.RUNNING:
            period_end = time.monotonic() + self.period

            if self.config_service_client:
                # ConfigServiceClient is created before Config - interval cannot be injected in constructor
                heartbeat_interval = self.config.config_service_heartbeat_interval
                self.config_service_client.heartbeat(heartbeat_interval)

            dead_resources = {
                **self.operational_resources.dead(self.heartbeat_timeout),
                **self.contained_resources.dead(self.heartbeat_timeout),
            }
            if dead_resources:
                self.logger.error(
                    "Some resources are not alive: {dead_resources}",
                    dead_resources=dead_resources,
                    event_id=LogId.microservice_dead_threads,
                )
                self.shutdown()
                return

            self.health.alive()

            period_remaining = period_end - time.monotonic()
            sleep_between_periods(self.health, period_remaining)

    def run_processing_forever(self, processing_thread_health):
        """Process work in fixed-time periods containing a periodic work-unit and one or more frequent work-units."""
        while processing_thread_health.state == RuntimeState.RUNNING:
            period_end = time.monotonic() + self.period

            with self.process_lock:
                self.process_once_per_period()

                if self.config.config_service_host:
                    self.reload_config()

            # Process units of frequent work in the given time window, always at least one (if not shutting down)
            while processing_thread_health.state == RuntimeState.RUNNING:
                with self.process_lock:
                    finished = self.process_frequently()
                if finished or time.monotonic() >= period_end:
                    break  # Stop processing when there is no more work to be done or time ran up

            processing_thread_health.alive()

            period_remaining = period_end - time.monotonic()
            sleep_between_periods(processing_thread_health, period_remaining)

    def reload_config(self):
        """Reload Config and process loaded changes."""
        correlation_id = random_correlation_id()

        try:
            reloaded = self.config.reload(correlation_id)
        except ConfigurationError as error:
            self.logger.warning(
                "Reload of configuration from Config Service failed - {error}",
                error=error,
                message_id=LogId.microservice_config_reload_error,
            )
            return

        if not reloaded:
            return

        self.process_config_reload(self.config)
        self.config.reload_processed(correlation_id)

    def shutdown(self, error=True):
        """Trigger shutdown of the microservice, i.e. break the run_forever loop."""
        self.health.shutting_down(error=error)
        for event in self.about_to_shutdown_events:
            event.set()

    def handle_shutdown_signal(self, signal_num, _stack_frame):
        """Signal handler which triggers shutdown of the microservice."""
        self.shutdown()
        self.logger.info(
            "Service {name!r} handled shutdown signal {signal_name}({signal_num})",
            name=self.name,
            signal_name=get_signal_name(signal_num),
            signal_num=signal_num,
            event_id=LogId.microservice_signal_handled,
        )

    @staticmethod
    def installed_packages():
        """Get versions of all PIP packages available to the Python interpreter."""
        # Python executable name in Docker image may differ from default "python"
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--no-index", "--format=json"], capture_output=True
        )
        packages = json.loads(result.stdout)

        return {package["name"]: package["version"] for package in packages}

    @staticmethod
    def platform_info():
        """Get the parameters of the underlying operating system and HW."""
        return {
            "hostname": platform.node(),
            "docker_container_id": docker.get_container_id(),
            "architecture": platform.machine(),
            "python": platform.python_version(),
            "os": f"{platform.system()} {platform.release()}",
        }


def sleep_between_periods(health: Health, sleep: float):
    """Sleep between periods, interrupt the sleeping if shutdown is requested."""
    # De-synchronize microservices that started at the same time to spread the load over time
    jitter = sleep * random.uniform(-0.1, 0.1)
    sleep_end = time.monotonic() + sleep + jitter

    while True:
        remaining = sleep_end - time.monotonic()
        if remaining <= 0 or health.state != RuntimeState.RUNNING:
            return

        time.sleep(min(RESPONSIVENESS_PERIOD, remaining))
        health.alive()
