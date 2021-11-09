"""Multi-threaded synchronous WSGI HTTP/1.1 server."""

from __future__ import annotations

import json
import socket
import socketserver
import sys
import wsgiref.simple_server

from typing import TYPE_CHECKING

from aicore.common.auth import AuthenticationError
from aicore.common.constants import CORRELATION_ID_HEADER, RESPONSIVENESS_PERIOD
from aicore.common.registry import LogId, WSGIServerMetric
from aicore.common.resource import BackgroundThread, RuntimeState
from aicore.common.tls import HSTS_HEADER_NAME, create_server_ssl_context
from aicore.common.utils import random_correlation_id


if TYPE_CHECKING:
    from typing import Any, ClassVar

    from aicore.common.resource import Health


# Inspired by prometheus_client.exposition._SilentHandler
class SilentHandler(wsgiref.simple_server.WSGIRequestHandler):
    """WSGI handler that does not log requests."""

    def log_message(self, format, *args):
        """Log nothing."""


# Inspired by prometheus_client.exposition.ThreadingWSGIServer
class MultithreadingWSGIServer(socketserver.ThreadingMixIn, wsgiref.simple_server.WSGIServer):
    """Thread per request HTTP server."""

    daemon_threads = True  # Dispose the thread after sending a response

    def __init__(self, server_address, RequestHandlerClass, tls_config, bind_and_activate=True):
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)

        self.ssl_context = create_server_ssl_context(tls_config) if tls_config.enabled else None

    def get_request(self):
        """Get the request and client address from the socket using SSL if configured."""
        if not self.ssl_context:
            return super().get_request()

        original_socket, addr = self.socket.accept()
        ssl_socket = self.ssl_context.wrap_socket(
            sock=original_socket,
            server_side=True,
            do_handshake_on_connect=True,
            suppress_ragged_eofs=True,
        )

        return ssl_socket, addr


class WSGIApplication:
    """Generic WSGI application with pluggable routing."""

    HTTP_CORRELATION_ID_HEADER: ClassVar[str] = f"HTTP_{CORRELATION_ID_HEADER.replace('-', '_').upper()}"

    def __init__(self, logger, tls_config, metrics):
        self.logger = logger
        self.tls_config = tls_config
        self.metrics = metrics
        self.metrics.register(WSGIServerMetric)

        self.handlers = {}  # Keys are routes, values are callbacks
        self.authenticators = {}  # Keys are routes, values are authenticators
        self.no_accesslog = set()  # Keys are routes

    # HTTP status codes: https://en.wikipedia.org/wiki/List_of_HTTP_status_codes

    def handle_200(self, payload, content_type):
        """Serialize given payload to JSON response with status 200."""
        headers = [("Content-Type", content_type)]
        self.metrics.increment(WSGIServerMetric.requests_total, status="200")

        return "200 OK", headers, [payload]

    def handle_json_200(self, payload):
        """Serialize given payload to JSON response with status 200."""
        return self.handle_200(json.dumps(payload).encode("utf-8"), "application/json")

    def handle_401(self, authenticator):
        """Indicate the supported authentication schemes."""
        # See also https://tools.ietf.org/html/rfc7235#section-3.1
        self.metrics.increment(WSGIServerMetric.requests_total, status="401")
        return "401 Unauthorized", [("WWW-Authenticate", method) for method in authenticator.supported_www_methods], ""

    def handle_404(self, _environ):  # Must be compatible with self.handlers which receive the environ
        """Indicate that given URL was not found."""
        self.metrics.increment(WSGIServerMetric.requests_total, status="404")
        return "404 Not Found", [], ""

    def handle_500(self):
        """Indicate that the server raised an unhandled exception."""
        self.metrics.increment(WSGIServerMetric.requests_total, status="500")
        return "500 Internal Server Error", [], ""  # Stacktrace is intentionally not included in the response

    def handle_json_503(self, payload):
        """Serialize given payload to JSON response with status 503."""
        self.metrics.increment(WSGIServerMetric.requests_total, status="503")
        return "503 Service Unavailable", [("Content-Type", "application/json")], [json.dumps(payload).encode("utf-8")]

    def __call__(self, environ, start_response):  # See https://www.python.org/dev/peps/pep-3333
        """Handle the incoming HTTP request according to WSGI standard."""
        path = environ["PATH_INFO"]
        authorization_payload = environ.get("HTTP_AUTHORIZATION")
        correlation_id = environ.get(self.HTTP_CORRELATION_ID_HEADER, random_correlation_id())
        handler = self.handlers.get(path, self.handle_404)  # Requires exact match of the path
        authenticator = self.authenticators.get(path)
        status = ""
        headers: list[tuple[str, str]] = []
        output = ""
        identity = None

        if authenticator:
            try:
                identity = authenticator.authenticate(authorization_payload)
            except AuthenticationError as error:
                self.logger.warning(
                    "WSGI server received request to {path!r} without correct authentication: {error}",
                    message_id=LogId.wsgi_unauthenticated,
                    path=path,
                    error=error,
                    correlation_id=correlation_id,
                )
                status, headers, output = self.handle_401(authenticator)
                self.metrics.increment(WSGIServerMetric.auth_failures_total)

        try:
            if not status:
                status, headers, output = handler(environ)
        except Exception:
            self.logger.exception(
                "WSGI server failed to handle a request to {path!r}",
                message_id=LogId.wsgi_errorlog,
                path=path,
                correlation_id=correlation_id,
                identity=identity,
            )
            status, headers, output = self.handle_500()

        if path not in self.no_accesslog:
            self.logger.info(
                "WSGI server handled a request to {path!r} with status {status_code}",
                message_id=LogId.wsgi_accesslog,
                path=path,
                status_code=status,
                correlation_id=correlation_id,
                identity=identity,
                _color="<red>" if not status.startswith("200") else "<white>",
            )

        # No need to send other response headers that MMM sends, AI Core has no web GUI
        headers.append((CORRELATION_ID_HEADER, correlation_id))
        headers.append((HSTS_HEADER_NAME, self.tls_config.headers_hsts))

        start_response(status, headers)

        return output


class WSGIServer(BackgroundThread):
    """Synchronous HTTP/1.1 WSGI server."""

    def __init__(self, name, host, port, tls_config, logger, metrics, poll_timeout=RESPONSIVENESS_PERIOD):
        super().__init__(name, logger, callback=self.serve_forever)
        self.host = host
        self.port = port
        self.tls_config = tls_config
        self.poll_timeout = poll_timeout

        self.wsgi_server = MultithreadingWSGIServer(
            (self.host, self.port),
            SilentHandler,
            tls_config,
            bind_and_activate=False,  # Do not listen on the socket yet - see TCPServer.__init__()
        )
        self.wsgi_application = WSGIApplication(logger, tls_config, metrics)
        self.wsgi_server.set_app(self.wsgi_application)
        self.wsgi_server.timeout = self.poll_timeout

        # We need to allow reuse of ports in WAIT_TIME state (very recently closed ports).
        # Setting allow_reuse_address = True allows this (by setting the SO_REUSEADDRESS socket option).
        # This works fine on Linux. Unfortunately, on Windows this allows reuse even of currently used ports.
        # So, we leave allow_reuse_address = False for Windows. It seems one can reuse recently closed ports even
        # without the SO_REUSEADDR on Windows. Moreover, we additionally set the SO_EXCLUSIVEADDRUSE to prevent anybody
        # from binding to the same port using a socket with the SO_REUSEADDR option set.
        # See table: https://docs.microsoft.com/en-us/windows/win32/winsock/using-so-reuseaddr-and-so-exclusiveaddruse
        if sys.platform == "win32":
            self.wsgi_server.allow_reuse_address = False
            self.wsgi_server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:
            self.wsgi_server.allow_reuse_address = True

    def __repr__(self):
        tls = " with TLS" if self.tls_config.enabled else ""

        return f"WSGI server {self.name!r} ({self.host}:{self.port}{tls})"

    def prepare_state_change_log_record(self) -> tuple[str, dict[str, Any]]:
        """Return log message and kwargs appropriate for the new state."""
        message = "{self!r} is {health!r}"
        kwargs: dict[str, Any] = {"event_id": LogId.wsgi_server_state_change}

        if self.health.state == RuntimeState.RUNNING:
            message += " and serving with routes {routes!r}"
            kwargs["routes"] = list(self.wsgi_application.handlers.keys())

        return message, kwargs

    def start(self) -> None:
        """Bind, activate and start the background thread."""
        try:
            self.wsgi_server.server_bind()
            self.wsgi_server.server_activate()
        except Exception:
            self.wsgi_server.server_close()
            self.health.stopped(error=True)
            raise

        super().start()

    def serve_forever(self, health: Health) -> None:
        """Handle individual requests until shutdown requested."""
        while health.state == RuntimeState.RUNNING:
            self.wsgi_server.handle_request()
            health.alive()

        self.wsgi_server.server_close()
