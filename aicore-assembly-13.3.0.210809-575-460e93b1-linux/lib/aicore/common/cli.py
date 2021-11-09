"""Command-line utilities for testing microservice."""

from __future__ import annotations

from aicore.common.auth import Identity, basic_auth, bearer_auth, internal_auth
from aicore.common.command import TestCommand
from aicore.common.config import ConfigOptionsBuilder, connection_options, server_options
from aicore.common.constants import CORRELATION_ID_HEADER
from aicore.common.http import HTTPClient, create_url
from aicore.common.microservice import Microservice
from aicore.common.tls import ClientTLSConfig, TLSConfigType
from aicore.common.utils import random_correlation_id


SENTINEL = object()

MOCKED_USER_IDENTITY_DICT = {
    Identity.ID_FIELD: "id",
    Identity.USERNAME_FIELD: "user",
    Identity.ROLES_FIELD: ["role"],
}


class CliService(Microservice):
    """Microservice used in command-line testing."""

    def __init__(self, config, name: str):
        super().__init__(name, config)

        self.grpc_commands = [TestCommand]

        if getattr(self.config, f"{self.name}_server_http_host", None):
            self.test_wsgi_server = self.wsgi_server()
        if getattr(self.config, f"{self.name}_server_grpc_host", None):
            self.test_grpc_server = self.grpc_server(commands=self.grpc_commands)

        if getattr(self.config, "cli_server_grpc_port", None):
            self.test_grpc_client = self.grpc_client("cli_server")
        if getattr(self.config, "cli_graphql_http_port", None):
            self.test_graphql_client = self.graphql_client("cli_graphql")

        if hasattr(self.config, "connection_string") and "null" not in self.config.connection_string:
            self.test_database = self.database()

        self.health.tracks_liveness = False  # REPL doesn't use Microservice.run_forever() so last_alive is not updated

    def http_client(self, connection_name, path):
        """Create HTTP client for given connection name and path."""
        host = getattr(self.config, f"{connection_name}_host")
        port = getattr(self.config, f"{connection_name}_http_port")
        tls_config = ClientTLSConfig(TLSConfigType.HTTP, connection_name, self.config)

        url = create_url(host, port, path, tls_config.enabled)

        return HTTPClient(url, tls_config)

    def http_get(
        self,
        path=None,
        connection_name=None,
        internal=True,
        basic=False,
        bearer=False,
        correlation_id=SENTINEL,
        identity=SENTINEL,
    ):
        """Perform HTTP(S) call based on given parameters."""
        if not connection_name:
            connection_name = "cli_server"

        if not path:
            path = self.actuator.METRICS_PATH

        headers = {}

        if basic:
            headers = basic_auth()
        elif bearer:
            headers = bearer_auth(self.config)
        elif internal:  # Must be last - it is a default fallback
            if identity == SENTINEL:
                identity = Identity(MOCKED_USER_IDENTITY_DICT, service_identity_dict=None)

            headers = internal_auth(self.config, identity)

        if correlation_id == SENTINEL:
            correlation_id = random_correlation_id()

        headers[CORRELATION_ID_HEADER] = correlation_id

        client = self.http_client(connection_name, path)
        return client.get(headers=headers).text

    def grpc_send(self, command=None, connection_name=None, correlation_id=SENTINEL, identity=SENTINEL):
        """Perform gRPC call based on given parameters."""
        if not connection_name:
            connection_name = "cli_server"

        if not command:
            command = TestCommand(["test_input"])

        if correlation_id == SENTINEL:
            correlation_id = random_correlation_id()

        if identity == SENTINEL:
            identity = Identity(MOCKED_USER_IDENTITY_DICT, service_identity_dict=None)

        client = self.contained_resources.resources.get(f"{connection_name}_grpc_client")

        if not client:
            client = self.grpc_client(connection_name)
            client.start()
            client.channel_ready_future.result()

        client.send(command, correlation_id, identity)

        return command


CLIENT_CONFIG_OPTIONS = (
    ConfigOptionsBuilder()
    .common_options("microservice_commons", "db", "mmm")
    .start_section("CLI Client", 1000)
    .create_options(lambda builder: server_options(builder, microservice_name="CLI Client", http_port=9041))
    .create_options(
        lambda builder: connection_options(
            builder, server_name="CLI Server microservice", grpc_port=9540, http_port=9040
        )
    )
    .create_options(lambda builder: connection_options(builder, server_name="CLI Client microservice", http_port=9041))
    .create_options(
        lambda builder: connection_options(builder, server_name="CLI GraphQL", host="localhost", http_port=8021)
    )
    .end_section()
    .options
)


SERVER_CONFIG_OPTIONS = (
    ConfigOptionsBuilder()
    .common_options("microservice_commons")
    .start_section("CLI Server", 1001)
    .create_options(
        lambda builder: server_options(builder, microservice_name="CLI Server", grpc_port=9540, http_port=9040)
    )
    .end_section()
    .options
)
