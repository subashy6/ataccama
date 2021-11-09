"""SSL/TLS related classes and functions."""

from __future__ import annotations

import contextlib
import enum
import os
import ssl
import tempfile

import requests

from aicore.common.certificates import (
    create_asymmetric_keystore,
    generate_self_signed_certificate,
    load_keystore_data,
    parse_common_name,
)


FILE_PREFIX = "file:"

HSTS_HEADER_NAME = "Strict-Transport-Security"


class TLSConfigType(enum.Enum):
    """Possible types of TLS configuration."""

    gRPC = "grpc"
    HTTP = "http"


class ClientTLSConfig:
    """Configuration containing TLS properties for specific gRPC/HTTP client."""

    def __init__(self, client_config_type: TLSConfigType, connection_name: str, config):
        client_type = client_config_type.value
        connection_name = connection_name.replace("_", "")

        communication_protocol_config = getattr(config, f"client_{client_type}_tls")

        connections_configs = config.client_connections or {}
        connection_configs = connections_configs.get(connection_name, {})

        connection_config = connection_configs.get("tls")
        connection_communication_protocol_config = connection_configs.get(f"{client_type}_tls")

        CONFIGS = [
            config,
            communication_protocol_config,
            connection_config,
            connection_communication_protocol_config,
        ]

        for tls_config_option_name in {
            "enabled",
            "trust_all",
            "truststore",
            "truststore_type",
            "truststore_password",
            "mtls",
            "keystore",
            "keystore_type",
            "keystore_password",
            "private_key_alias",
            "private_key_password",
        }:
            config_option_name = f"client_tls_{tls_config_option_name}"
            value = None

            for specific_config in CONFIGS:
                value = getattr(specific_config, config_option_name, value)

            setattr(self, tls_config_option_name, value)

        for path in ["keystore", "truststore"]:
            value = getattr(self, path)
            value = value.lstrip(FILE_PREFIX) if value else None
            setattr(self, path, value)

        self.tmp_path = config.tmp_path


class ServerTLSConfig:
    """Configuration containing TLS properties for gRPC/HTTP server."""

    class MTLSTypes(enum.Enum):
        """Enumeration of mTLS types for gRPC/HTTP server."""

        NONE = ssl.CERT_NONE
        OPTIONAL = ssl.CERT_OPTIONAL
        REQUIRED = ssl.CERT_REQUIRED

    def __init__(self, server_config_type: TLSConfigType, config):
        communication_protocol_config = getattr(config, f"server_{server_config_type.value}_tls")

        CONFIGS = [config, communication_protocol_config]

        for tls_config_option_name in {
            "enabled",
            "keystore",
            "keystore_type",
            "keystore_password",
            "private_key_alias",
            "private_key_password",
            "mtls",
            "truststore",
            "truststore_type",
            "truststore_password",
            "allow_generate",
            "generated_private_key",
            "generated_certificate_chain",
        }:
            config_option_name = f"server_tls_{tls_config_option_name}"
            value = None

            for specific_config in CONFIGS:
                value = getattr(specific_config, config_option_name, value)

            setattr(self, tls_config_option_name, value)

        for path in ["keystore", "truststore", "generated_private_key", "generated_certificate_chain"]:
            value = getattr(self, path)
            value = value.lstrip(FILE_PREFIX) if value else None
            setattr(self, path, value)

        self.headers_hsts = config.headers_hsts
        self.tmp_path = config.tmp_path


class CertificatesLoader:
    """Load private keys and certificates based on client/server TLS Config."""

    def __init__(self, tls_config):
        self.tls_config = tls_config
        self.use_generated_certificate = self.tls_config.enabled and getattr(
            self.tls_config, "allow_generate", False
        )  # ClientTLSConfig doesn't have this flag

        self.generate_certificate_if_missing()

    def generate_certificate_if_missing(self):
        """Generate certificate and persist its public and private key based on TLS config."""
        if (
            self.use_generated_certificate
            and not os.path.exists(self.tls_config.generated_private_key)
            and not os.path.exists(self.tls_config.generated_certificate_chain)
        ):
            key_pem, cert_pem = generate_self_signed_certificate()

            with open(self.tls_config.generated_private_key, "wb") as file:
                file.write(key_pem)
            with open(self.tls_config.generated_certificate_chain, "wb") as file:
                file.write(cert_pem)

    def load_key_and_certificate(self):
        """Load private key and certificate from keystore or generated files."""
        if self.use_generated_certificate:
            files = []
            for path in [self.tls_config.generated_private_key, self.tls_config.generated_certificate_chain]:
                with open(path, "rb") as file:
                    files.append(file.read())

            return tuple(files)

        keystore_data = load_keystore_data(self.tls_config.keystore_type, self.tls_config.keystore)
        keystore = create_asymmetric_keystore(
            self.tls_config.keystore_type, keystore_data, self.tls_config.keystore_password
        )

        private_key, _, certificate = keystore.key_and_certificate(
            encrypt_private_key=False,
            private_key_alias=self.tls_config.private_key_alias,
            private_key_password=self.tls_config.private_key_password,
        )

        return private_key, certificate

    def load_trusted_certificates(self):
        """Load trusted certificates from truststore."""
        if not self.tls_config.truststore:
            return None

        truststore_data = load_keystore_data(self.tls_config.truststore_type, self.tls_config.truststore)
        truststore = create_asymmetric_keystore(
            self.tls_config.truststore_type, truststore_data, self.tls_config.truststore_password
        )

        return truststore.trusted_certificates()

    @contextlib.contextmanager
    def get_key_and_certificate_paths(self):
        """Temporarily persist private key and certificate and return paths."""
        if self.use_generated_certificate:
            yield (
                self.tls_config.generated_private_key,
                None,
                self.tls_config.generated_certificate_chain,
            )

            return

        keystore_data = load_keystore_data(self.tls_config.keystore_type, self.tls_config.keystore)
        keystore = create_asymmetric_keystore(
            self.tls_config.keystore_type, keystore_data, self.tls_config.keystore_password
        )

        private_key, private_key_password, certificate = keystore.key_and_certificate(
            encrypt_private_key=True,
            private_key_alias=self.tls_config.private_key_alias,
            private_key_password=self.tls_config.private_key_password,
        )

        with tmp_file(private_key, self.tls_config.tmp_path) as private_key_path, tmp_file(
            certificate, self.tls_config.tmp_path
        ) as certificate_path:
            yield private_key_path, private_key_password, certificate_path

    @contextlib.contextmanager
    def get_trusted_certificates_path(self):
        """Temporarily persist trusted certificates and return path."""
        trusted_certificates = self.load_trusted_certificates()

        with tmp_file(trusted_certificates, self.tls_config.tmp_path) as trusted_certificates_path:
            yield trusted_certificates_path

    @staticmethod
    def load_server_certificate(host, port):
        """Load server's public certificate."""
        certificate = ssl.get_server_certificate((host, port)).encode()
        common_name = parse_common_name(certificate)

        return common_name, certificate


@contextlib.contextmanager
def tmp_file(data: bytes, tmp_dir):
    """Temporarily persist private key and certificates."""
    if not data:
        yield None
        return

    # We need to close the file first, otherwise SSLContext cannot open it on windows (permission denied)
    with tempfile.NamedTemporaryFile("wb", dir=tmp_dir, delete=False) as file:
        file.write(data)

    yield file.name

    os.remove(file.name)


def create_default_ssl_context():
    """Create default SSL context with support for TLS v1.2 and higher."""
    # For ssl context creation see https://www.openssl.org/docs/man1.1.1/man3/SSL_CTX_new.html

    # No specific version should be set, use just common protocol flag
    # See https://docs.python.org/3.9/library/ssl.html#ssl.PROTOCOL_TLSv1_2
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)

    # Minimum and maximum versions should be used instead of preventing specific versions
    # See https://docs.python.org/3.9/library/ssl.html#ssl.OP_NO_TLSv1
    context.minimum_version = ssl.TLSVersion.TLSv1_2

    return context


def create_server_ssl_context(tls_config):
    """Create SSLContext used in HTTP server."""
    # Higher version of TLS than in default implementation
    context = create_default_ssl_context()

    context.verify_mode = tls_config.mtls.value

    context.load_default_certs(ssl.Purpose.CLIENT_AUTH)

    # Cannot supply private key/certificates directly - temporary file creation
    # PyOpenSSL can do it directly, but it uses deprecated way for SSL Context creation
    #   See https://github.com/pyca/pyopenssl/issues/860
    #   See https://www.openssl.org/docs/man1.1.1/man3/SSL_CTX_new.html
    certificates_loader = CertificatesLoader(tls_config)

    with certificates_loader.get_key_and_certificate_paths() as (
        private_key_path,
        private_key_password,
        certificate_path,
    ):
        context.load_cert_chain(certificate_path, private_key_path, private_key_password)

    with certificates_loader.get_trusted_certificates_path() as trusted_certificates_path:
        if trusted_certificates_path:
            # These need to be CAs, in the case of self-signed certificate following must be set:
            #   basicConstraints = CA:TRUE
            #   keyUsage = keyCertSign  # noqa: E800
            context.load_verify_locations(trusted_certificates_path)

    return context


def create_client_ssl_context(tls_config):
    """Create SSLContext used in HTTP client."""
    # Higher version of TLS than in default implementation
    context = create_default_ssl_context()

    if tls_config.trust_all:
        context.verify_mode = ssl.CERT_OPTIONAL
        context.check_hostname = False
    else:
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = True

    context.load_default_certs(ssl.Purpose.SERVER_AUTH)

    # Cannot supply private key/certificates directly - temporary file creation
    # PyOpenSSL can do it directly, but it uses deprecated way for SSL Context creation
    #   See https://github.com/pyca/pyopenssl/issues/860
    #   See https://www.openssl.org/docs/man1.1.1/man3/SSL_CTX_new.html
    certificates_loader = CertificatesLoader(tls_config)

    with certificates_loader.get_trusted_certificates_path() as trusted_certificates_path:
        if trusted_certificates_path:
            # These need to be CAs, in the case of self-signed certificate following must be set:
            #   basicConstraints = CA:TRUE
            #   keyUsage = keyCertSign  # noqa: E800
            context.load_verify_locations(trusted_certificates_path)

    if tls_config.mtls:
        with certificates_loader.get_key_and_certificate_paths() as (
            private_key_path,
            private_key_password,
            certificate_path,
        ):
            context.load_cert_chain(certificate_path, private_key_path, private_key_password)

    return context


class SSLContextAdapter(requests.adapters.HTTPAdapter):
    """A Transport Adapter that allows to pass custom SSLContext.

    Note: Source for this code was found here: https://lukasa.co.uk/2017/02/Configuring_TLS_With_Requests/
    """

    def __init__(self, ssl_context):
        self.ssl_context = ssl_context
        super(SSLContextAdapter, self).__init__()

    def init_poolmanager(self, *args, **kwargs):
        """Set custom SSLContext before initializing a urllib3 PoolManager."""
        if self.ssl_context:
            kwargs["ssl_context"] = self.ssl_context

        return super(SSLContextAdapter, self).init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        """Set custom SSLContext before returning urllib3 ProxyManager for the given proxy."""
        if self.ssl_context:
            kwargs["ssl_context"] = self.ssl_context

        return super(SSLContextAdapter, self).proxy_manager_for(*args, **kwargs)
