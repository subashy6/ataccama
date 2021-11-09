"""HTTP related logic."""

from __future__ import annotations

import re

import requests

from aicore.common.tls import SSLContextAdapter, create_client_ssl_context


def create_url(host: str, port: int, path: str, tls: bool) -> str:
    """Create HTTP Client for given url parts."""
    scheme = "https" if tls else "http"
    path = path.lstrip("/")

    if port:
        return f"{scheme}://{host}:{port}/{path}"

    return f"{scheme}://{host}/{path}"


def merge_url(base_url: str, path: str) -> str:
    """Create url by merging base url and given path."""
    if not path:
        return base_url

    url = base_url.rstrip("/")
    path = path.lstrip("/")

    return f"{url}/{path}"


def parse_retryable_reason(error: requests.RequestException):
    """Parse reason why the HTTP call failed (but can be retried) based on raised exception."""
    if isinstance(error, requests.ConnectionError):
        # ConnectionError usually has reason, that contains connection object that changes for every request
        #   e.g. <urllib3.connection.HTTPConnection object at 0x000002AA33726280>
        if error.args and hasattr(error.args[0], "reason"):
            reason = str(error.args[0].reason)
            return re.sub("<[^>]*>: ", "", reason)

        return str(error)

    if isinstance(error, requests.Timeout):
        return str(error)

    if isinstance(error, requests.HTTPError) and 500 <= error.response.status_code < 600:
        return str(error)

    return None


class HTTPClient:
    """HTTP client that can use TLS for GET/POST HTTP calls."""

    def __init__(self, url: str, tls_config):
        self.url = url

        self.ssl_context = None
        self.verify = None

        if tls_config.enabled:
            self.ssl_context = create_client_ssl_context(tls_config)
            self.verify = not tls_config.trust_all

    def get(self, path=None, headers=None, timeout=None):
        """Execute HTTP GET method."""
        with requests.Session() as session:
            url = merge_url(self.url, path)

            session.mount(url, SSLContextAdapter(self.ssl_context))

            return session.get(url, headers=headers, timeout=timeout, verify=self.verify)

    def post(self, path=None, data=None, json=None, headers=None, timeout=None):
        """Execute HTTP POST method."""
        with requests.Session() as session:
            url = merge_url(self.url, path)

            session.mount(url, SSLContextAdapter(self.ssl_context))

            return session.post(url, data=data, json=json, headers=headers, timeout=timeout, verify=self.verify)
