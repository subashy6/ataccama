"""Log ids and metrics of this package."""

from __future__ import annotations

import enum

from aicore.common.metrics import MetricEnum, MetricType


class LogId(enum.Enum):
    """Enum for all action, message and event ids used in logging."""

    config_service_not_specified = enum.auto()
    config_service_connection_reestablished = enum.auto()
    db_create = enum.auto()
    db_drop = enum.auto()
    db_execute = enum.auto()
    db_migration = enum.auto()
    db_state_change = enum.auto()
    db_truncate = enum.auto()
    dependency_state_change = enum.auto()
    graphql_client_send_error = enum.auto()
    grpc_client_inconsistent_correlation_id = enum.auto()
    grpc_client_missing_correlation_id = enum.auto()
    grpc_client_process_command_error = enum.auto()
    grpc_client_send_error = enum.auto()
    grpc_client_state_change = enum.auto()
    grpc_server_command_error = enum.auto()
    grpc_server_missing_correlation_id = enum.auto()
    grpc_server_process = enum.auto()
    grpc_server_process_error = enum.auto()
    grpc_server_state_change = enum.auto()
    grpc_server_unauthenticated = enum.auto()
    grpc_server_unsupported_method = enum.auto()
    health_check_not_alive = enum.auto()
    health_check_unavailable = enum.auto()
    keycloak_client_send = enum.auto()
    keycloak_client_state_change = enum.auto()
    microservice_bootstrap = enum.auto()
    microservice_config_reload_error = enum.auto()
    microservice_dead_threads = enum.auto()
    microservice_error = enum.auto()
    microservice_pip_packages = enum.auto()
    microservice_platform_info = enum.auto()
    microservice_resources_shutdown_failed = enum.auto()
    microservice_resources_start_failed = enum.auto()
    microservice_shutdown = enum.auto()
    microservice_shutdown_error = enum.auto()
    microservice_shutdown_requested_via_grpc = enum.auto()
    microservice_signal_handled = enum.auto()
    microservice_start_error = enum.auto()
    microservice_thread_limits = enum.auto()
    process_alive = enum.auto()
    process_alive_and_ready = enum.auto()
    process_already_dead = enum.auto()
    process_killed = enum.auto()
    process_not_alive = enum.auto()
    process_not_running = enum.auto()
    process_respawn_count = enum.auto()
    process_shutdown = enum.auto()
    process_spawned = enum.auto()
    process_stopped_being_ready = enum.auto()
    readiness_wait_error = enum.auto()
    resource_shutdown = enum.auto()
    resource_start = enum.auto()
    resource_state_change = enum.auto()
    resource_unhandled_exception = enum.auto()
    resources_wait = enum.auto()
    supervisor_captured_microservices = enum.auto()
    supervisor_controlled_microservices = enum.auto()
    supervisor_get_process_health_error = enum.auto()
    supervisor_invalid_process_health_response = enum.auto()
    supervisor_shutdown_signal_sent = enum.auto()
    supervisor_unknown_captured_microservice = enum.auto()
    wsgi_accesslog = enum.auto()
    wsgi_errorlog = enum.auto()
    wsgi_server_state_change = enum.auto()
    wsgi_unauthenticated = enum.auto()

    def __repr__(self):
        return self.name


class DatabaseMetric(MetricEnum):
    """Metrics measured by the Database."""

    __name_prefix__ = "database"

    query_seconds = (MetricType.summary, "The number of seconds a database query takes to complete.", ["operation"])


class GraphQLClientMetric(MetricEnum):
    """Metrics measured by the GraphQL client."""

    __name_prefix__ = "graphql_client"

    query_seconds = (MetricType.summary, "The number of seconds a GraphQL query takes to complete.")


class GRPCClientMetric(MetricEnum):
    """Metrics measured by the gRPC client."""

    __name_prefix__ = "grpc_client"

    query_seconds = (MetricType.summary, "The number of seconds a gRPC query takes to complete.")


class GRPCServerMetric(MetricEnum):
    """Metrics measured by the gRPC server."""

    __name_prefix__ = "grpc_server"

    auth_failures_total = (MetricType.counter, "The total number of gRPC requests with authentication failures.")
    commands_total = (MetricType.counter, "The total number of gRPC commands received.", ["type"])
    processing_seconds = (MetricType.summary, "The processing time of a gRPC request, expressed in seconds.", ["stage"])
    queue_size = (MetricType.gauge, "The number of active RPCs, either queued or currently processed.")


class MicroserviceMetric(MetricEnum):
    """Metrics measured by the base Microservice."""

    __name_prefix__ = "microservice"

    microservice = (MetricType.info, "The microservice details.")


class WSGIServerMetric(MetricEnum):
    """Metrics measured by the WSGI server."""

    __name_prefix__ = "wsgi_server"

    auth_failures_total = (MetricType.counter, "The total number of HTTP requests with authentication failures.")
    requests_total = (MetricType.counter, "The total number of HTTP request status codes. ", ["status"])


METRICS = [
    DatabaseMetric,
    GraphQLClientMetric,
    GRPCClientMetric,
    GRPCServerMetric,
    MicroserviceMetric,
    WSGIServerMetric,
]
