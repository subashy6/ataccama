"""GraphQL client."""

from __future__ import annotations

import inspect
import re

from typing import TYPE_CHECKING

import requests
import tenacity

from aicore.common.auth import create_internal_jwt_header
from aicore.common.constants import AUTHENTICATION_HEADER, CORRELATION_ID_HEADER
from aicore.common.exceptions import AICoreException
from aicore.common.http import HTTPClient, create_url
from aicore.common.logging import WARNING_COLOR
from aicore.common.registry import GraphQLClientMetric, LogId
from aicore.common.retry import never_retrying


if TYPE_CHECKING:
    from typing import Any, Optional

    from aicore.common.auth import InternalJWTGenerator
    from aicore.common.logging import Logger
    from aicore.common.types import CorrelationId


# Header will always contain <auth_type> error=<error>
# Based on Java auth library -> HttpAuthenticationChainFilter
AUTH_FAIL_HEADER_REGEX = re.compile('(\\S+) error="(\\S+)"')


class GraphQLResponseException(AICoreException):
    """Error received in GraphQL response."""

    def __init__(self, reason: Optional[str] = None, status_code: Optional[int] = None):
        self.reason = reason
        self.status_code = status_code


class GraphQLClient:
    """GraphQL client supporting JWT/basic authentication and correlation id."""

    def __init__(
        self,
        name: str,
        logger: Logger,
        host: str,
        port: int,
        jwt_generator: InternalJWTGenerator,
        tls_config,
        metrics,
        timeout: int = 5,
        retrying=never_retrying,
    ):
        self.name = name
        self.logger = logger

        url = create_url(host, port, "graphql", tls_config.enabled)
        self.http_client = HTTPClient(url, tls_config)

        self.jwt_generator = jwt_generator
        self.timeout = timeout  # [s] Abort the HTTP call if socket doesn't receive any bytes until timeout

        retry_exceptions = (requests.ConnectionError, requests.HTTPError, requests.Timeout, ValueError)
        self.retrying = retrying.copy(
            retry=tenacity.retry_if_exception_type(retry_exceptions), before_sleep=self._log_send_attempt, reraise=True
        )

        self.metrics = metrics
        self.metrics.register(GraphQLClientMetric)

    def send(self, query: str, correlation_id: CorrelationId, **retry_kwargs) -> dict[str, Any]:
        """Send given GraphQL query with internal JWT authentication over HTTP/1.1 with retries."""

        def timed_send(*args, **kwargs):
            with self.metrics.measure_time(GraphQLClientMetric.query_seconds):
                return self._send(*args, **kwargs)

        retrying = self.retrying.copy(**retry_kwargs) if retry_kwargs else self.retrying
        return retrying(timed_send, query, correlation_id)

    def _send(self, query: str, correlation_id: CorrelationId) -> dict[str, Any]:
        """Send given GraphQL query with internal JWT authentication over HTTP/1.1."""
        header_name, jwt_token = create_internal_jwt_header(self.jwt_generator.generate())

        response = self.http_client.post(
            json={"query": query},
            headers={header_name: jwt_token, CORRELATION_ID_HEADER: correlation_id},
            timeout=self.timeout,
        )

        return self._verify_response(response, query)

    def _verify_response(self, response: requests.Response, query: str) -> dict:
        """Verify received GraphQL response."""
        # Any GraphQL error must be presented through the response, not the status code
        # http://spec.graphql.org/June2018/#sec-Response
        if response.status_code != requests.codes.ok:
            if response.status_code == requests.codes.unauthorized:
                auth_type, reason, description = self.parse_auth_header(response.headers[AUTHENTICATION_HEADER])
                self.logger.error(
                    "GraphQL request failed - {reason} received for {auth_type} authentication: {description}",
                    auth_type=auth_type,
                    reason=reason,
                    description=description,
                    message_id=LogId.graphql_client_send_error,
                )

                raise GraphQLResponseException(f"{reason}: {description}", response.status_code)

            self.logger.error(
                "Invalid response code for GraphQL request: {status_code}",
                status_code=response.status_code,
                message_id=LogId.graphql_client_send_error,
            )
            raise GraphQLResponseException(response.reason)

        parsed_response = response.json()

        # Human-readable error message must be specified under the `errors.message` entry
        # http://spec.graphql.org/June2018/#sec-Errors
        if "errors" in parsed_response:
            error_message = "; ".join(error["message"] for error in parsed_response["errors"])
            self.logger.error(
                "Submission of GraphQL request failed: {error_message}\nQuery: {query}",
                error_message=error_message,
                query=query,
                message_id=LogId.graphql_client_send_error,
            )
            raise GraphQLResponseException(error_message)

        # Returned non-error data must be under the `data` entry
        # http://spec.graphql.org/June2018/#sec-Data
        try:
            return parsed_response["data"]
        except KeyError:
            self.logger.error(
                "Received malformed response: {response}",
                response=parsed_response,
                message_id=LogId.graphql_client_send_error,
            )
            raise GraphQLResponseException

    def parse_auth_header(self, auth_header_value: str) -> tuple[str, ...]:
        """Parse authentication failure reason."""
        auth_type, reason = re.match(AUTH_FAIL_HEADER_REGEX, auth_header_value).groups()

        # `error_description` is optional and may not be present
        # Based on Java auth library -> HttpAuthenticationChainFilter
        description = "No error description provided"
        if "error_description" in auth_header_value:
            description = re.search('error_description="(.+)"', auth_header_value)[1]

        return auth_type, reason, description

    def _log_send_attempt(self, retry_state: tenacity.RetryCallState):
        """Log failed attempt to send GraphQL request."""
        # Same as Logger.warning + added depth to preserve code location in log
        log_callback = (
            self.logger.logger.opt(capture=True, depth=4).bind(_record_type="message", _color=WARNING_COLOR).warning
        )

        bound_arguments = inspect.signature(self._send).bind(*retry_state.args, **retry_state.kwargs)
        correlation_id = bound_arguments.arguments["correlation_id"]

        error = retry_state.outcome.exception()
        log_callback(
            "GraphQL client {name!r} raised {error_name!r} while sending request at {url!r}, next attempt in {sleep} s",
            name=self.name,
            error=error,
            error_name=type(error).__name__,
            url=self.http_client.url,
            attempt=retry_state.attempt_number,
            sleep=retry_state.next_action.sleep,
            correlation_id=correlation_id,
            event_id=LogId.graphql_client_send_error,
        )
