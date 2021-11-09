"""Wrapping functions for low-level certificates API."""

from __future__ import annotations

import datetime
import uuid

from typing import TYPE_CHECKING

import cryptography.hazmat.backends
import cryptography.hazmat.primitives.asymmetric.rsa
import cryptography.hazmat.primitives.hashes
import cryptography.hazmat.primitives.serialization
import cryptography.hazmat.primitives.serialization.pkcs12
import cryptography.x509
import jks
import more_itertools

from aicore.common.constants import ENCODING
from aicore.common.exceptions import AICoreException
from aicore.common.utils import datetime_now


if TYPE_CHECKING:
    from typing import Optional


PEM_ENCODING = cryptography.hazmat.primitives.serialization.Encoding.PEM
NO_ENCRYPTION = cryptography.hazmat.primitives.serialization.NoEncryption()
OPEN_SSL_FORMAT = cryptography.hazmat.primitives.serialization.PrivateFormat.TraditionalOpenSSL


def load_keystore_data(keystore_type: str, keystore_path: str):
    """Load Keystore data from file."""
    if not keystore_path:
        raise KeystoreError(f"No path to {keystore_type} keystore supplied.")

    try:
        with open(keystore_path, "rb") as file:
            return file.read()
    except OSError as error:
        raise KeystoreError(f"Failed to load {keystore_type} keystore {keystore_path!r}") from error


def create_asymmetric_keystore(keystore_type: str, keystore_data: bytes, keystore_password: Optional[str] = None):
    """Create Keystore with support for storing private keys and certificates."""
    factory_methods = {"PKCS12": KeystorePKCS12, "JKS": KeystoreJKS, "JCEKS": KeystoreJKS}

    if keystore_type not in factory_methods:
        raise KeystoreError(f"Unsupported keystore type {keystore_type!r}")

    factory_method = factory_methods[keystore_type]

    return factory_method(keystore_type, keystore_data, keystore_password)


def create_symmetric_keystore(keystore_type: str, keystore_data: bytes, keystore_password: Optional[str] = None):
    """Create Keystore with support for storing keys for symmetric encryption."""
    factory_methods = {"JCEKS": KeystoreJKS}

    if keystore_type not in factory_methods:
        raise KeystoreError(f"Unsupported keystore type {keystore_type!r}")

    factory_method = factory_methods[keystore_type]

    return factory_method(keystore_type, keystore_data, keystore_password)


def export_to_pem(private_key, encrypt_private_key: bool):
    """Export private key loaded by cryptography into PEM format."""
    encryption_password = None
    encryption_algorithm = NO_ENCRYPTION

    if encrypt_private_key:
        encryption_password = uuid.uuid4().hex
        encryption_algorithm = cryptography.hazmat.primitives.serialization.BestAvailableEncryption(
            encryption_password.encode(ENCODING)
        )

    private_key = private_key.private_bytes(PEM_ENCODING, OPEN_SSL_FORMAT, encryption_algorithm)

    return private_key, encryption_password


class KeystoreError(AICoreException):
    """Error while working with keystore."""


class KeystorePKCS12:
    """Wrapper for Keystore using PKCS12 format."""

    def __init__(self, keystore_type: str, data: bytes, password: Optional[str] = None):
        self.keystore_type = keystore_type
        self.data = data
        self.password_data = password.encode(ENCODING) if password else None

    def key_and_certificate(self, encrypt_private_key: bool = False, **_kwargs):
        """Return private key and corresponding certificate encoded in PEM format."""
        # Note: pyca/cryptography has only basic support for PKCS12 format
        #   - only one private key can be read - no aliases
        #       - see https://github.com/pyca/pyopenssl/issues/770#issuecomment-400710906
        #       - the returned private key is the one that was inserted into the keystore first
        #   - no support for encrypted private keys
        # The limited support mainly is because of the OpenSSL limitations
        #   (https://www.openssl.org/docs/manmaster/man3/PKCS12_parse.html#BUGS)
        try:
            private_key, certificate, _ = cryptography.hazmat.primitives.serialization.pkcs12.load_key_and_certificates(
                self.data, self.password_data
            )
        except ValueError as error:
            raise KeystoreError(f"Failed to load data from {self.keystore_type!r} keystore") from error

        pem_private_key = None
        encryption_password = None
        pem_certificate = None

        if private_key:
            pem_private_key, encryption_password = export_to_pem(private_key, encrypt_private_key)

        if certificate:
            pem_certificate = certificate.public_bytes(PEM_ENCODING)

        return pem_private_key, encryption_password, pem_certificate

    def trusted_certificates(self):
        """Return trusted certificates encoded as one PEM format."""
        # All certificates (except the private key's public certificate) are returned as additional_certificates
        try:
            additional_certificates = cryptography.hazmat.primitives.serialization.pkcs12.load_key_and_certificates(
                self.data, self.password_data
            )[2]
        except ValueError as error:
            raise KeystoreError(f"Failed to load data from {self.keystore_type} keystore") from error

        certificates = [cert.public_bytes(PEM_ENCODING) for cert in additional_certificates]

        return b"".join(certificates)


class KeystoreJKS:
    """Wrapper for Keystore using JKS/JCEKS format."""

    def __init__(self, keystore_type: str, data: bytes, password: Optional[str] = None):
        self.keystore_type = keystore_type

        try:
            self.delegate = jks.KeyStore.loads(data, password)
        except jks.KeystoreException as exception:
            raise KeystoreError(f"Failed to load {self.keystore_type} keystore") from exception

    def key_and_certificate(
        self,
        encrypt_private_key: bool = False,
        private_key_alias: Optional[str] = None,
        private_key_password: Optional[str] = None,
    ):
        """Return private key and corresponding certificate encoded in PEM format."""
        private_key_entry = self.get_key_entry("private_key", private_key_alias, private_key_password)

        try:
            private_key = private_key_entry.pkey
        except jks.KeystoreException as exception:
            raise KeystoreError(
                f"Failed to load private key with alias {private_key_alias!r} from {self.keystore_type} keystore"
            ) from exception

        certificate = private_key_entry.cert_chain
        pem_private_key = None
        encryption_password = None
        pem_certificate = None

        if private_key:
            der_private_key = cryptography.hazmat.primitives.serialization.load_der_private_key(
                private_key, password=None
            )
            pem_private_key, encryption_password = export_to_pem(der_private_key, encrypt_private_key)

        if certificate:
            der_certificate = cryptography.x509.load_der_x509_certificate(certificate[0][1])
            pem_certificate = der_certificate.public_bytes(PEM_ENCODING)

        return pem_private_key, encryption_password, pem_certificate

    def trusted_certificates(self):
        """Return trusted certificates encoded as one PEM format."""
        certificates = [cryptography.x509.load_der_x509_certificate(cert.cert) for cert in self.delegate.certs.values()]
        certificates = [cert.public_bytes(PEM_ENCODING) for cert in certificates]

        return b"".join(certificates)

    def secret_key(
        self,
        secret_key_alias: Optional[str] = None,
        secret_key_password: Optional[str] = None,
    ):
        """Return secret key for given parameters."""
        try:
            return self.get_key_entry("secret_key", secret_key_alias, secret_key_password).key
        except jks.KeystoreException as exception:
            raise KeystoreError(
                f"Failed to load secret key with alias {secret_key_alias!r} from {self.keystore_type} keystore"
            ) from exception

    def get_key_entry(self, key_type: str, key_alias: Optional[str] = None, key_password: Optional[str] = None):
        """Return private or secret key for given parameters."""
        keys_dict = getattr(self.delegate, f"{key_type}s")
        key_name = key_type.replace("_", " ")

        if key_alias:
            if key_alias in keys_dict:
                key_entry = keys_dict[key_alias]
            else:
                raise KeystoreError(
                    f"Key {key_name!r} with alias {key_alias!r} not found in {self.keystore_type} keystore"
                )
        else:
            key_entry = more_itertools.first(sorted(keys_dict.values(), key=lambda entry: entry.timestamp))

        if key_password:
            try:
                key_entry.decrypt(key_password)
            except jks.KeystoreException as exception:
                raise KeystoreError(
                    f"Decryption failed for {key_name!r} with alias {key_alias!r} in {self.keystore_type} keystore"
                ) from exception

        return key_entry


def generate_self_signed_certificate():
    """Generate self signed certificate.

    Note: Most of the values were taken from Ataccama java code.
        See com.ataccama.lib.grpc.server.core.tls.DefaultSslContextProvider in
            https://bitbucket.atc.services/projects/DEV-LIBS/repos/grpc/browse
        See com.ataccama.lib.securityutil.pki.CertificateFactory in
            https://bitbucket.atc.services/projects/DEV-LIBS/repos/security-util/browse
    """
    # Java sets it as "CN=cnName"
    name = cryptography.x509.Name(
        [cryptography.x509.NameAttribute(cryptography.x509.oid.NameOID.COMMON_NAME, "cnName")]
    )
    now = datetime_now()
    year = now + datetime.timedelta(days=365)  # Java makes it valid for a year
    # Java sets it as System.nanoTime() = current value of the running JVM time source, in nanoseconds
    # Current timestamp in milliseconds seems like a good enough unique alternative
    now_milli = int(now.timestamp() * 1000)
    # java states that it should be true for CA, false for EndEntity
    basic_constraints = cryptography.x509.BasicConstraints(ca=True, path_length=0)

    # Java uses SHA256WithRSA = RSA for key-pair generation and the same values
    key = cryptography.hazmat.primitives.asymmetric.rsa.generate_private_key(public_exponent=65537, key_size=2048)

    cert = (
        cryptography.x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(now_milli)
        .not_valid_before(now)
        .not_valid_after(year)
        # Java states that Basic Constraints are usually marked as critical
        .add_extension(basic_constraints, critical=True)
        # Java uses SHA256WithRSA = SHA256 for signing
        .sign(key, cryptography.hazmat.primitives.hashes.SHA256())
    )

    cert_pem = cert.public_bytes(PEM_ENCODING)
    key_pem = key.private_bytes(PEM_ENCODING, OPEN_SSL_FORMAT, NO_ENCRYPTION)

    return key_pem, cert_pem


def parse_common_name(certificate_data):
    """Parse Common Name from public certificate."""
    loaded_crt = cryptography.x509.load_pem_x509_certificate(certificate_data)

    return loaded_crt.subject.get_attributes_for_oid(cryptography.x509.oid.NameOID.COMMON_NAME)[0].value
