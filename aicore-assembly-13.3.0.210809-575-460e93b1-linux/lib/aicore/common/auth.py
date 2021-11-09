"""Authentication providers and authenticators."""

from __future__ import annotations

import base64
import binascii
import datetime
import re
import time

from typing import TYPE_CHECKING

import jwcrypto
import jwcrypto.jwk
import jwt
import requests
import tenacity

from aicore.common.constants import ENCODING
from aicore.common.exceptions import AICoreException
from aicore.common.http import HTTPClient, merge_url, parse_retryable_reason
from aicore.common.registry import LogId
from aicore.common.resource import ReadinessDependency
from aicore.common.retry import never_retrying
from aicore.common.tls import ClientTLSConfig, TLSConfigType
from aicore.common.utils import datetime_now


if TYPE_CHECKING:
    from typing import Any, Optional


AUTHORIZATION_HEADER_HTTP_2 = "authorization"  # All-lowercase headers are mandatory in HTTP/2
AUTHORIZATION_HEADER_HTTP_1_1 = "Authorization"
INTERNAL_TOKEN_TYPE = "JWT"
ALG_NONE = "none"

DEFAULT_LEEWAY = 60  # Java has same value (60 seconds), but it's called maxClockSkew


def internal_auth(config, identity: Optional[Identity] = None):
    """Create authentication headers based on JWT token generated from AI Core's private key."""
    jwt_generator = InternalJWTGenerator.from_jwk(config.jwk, config.jwt_expiration)
    jwt_token = create_internal_jwt_header(jwt_generator.generate(identity))[1]

    return {AUTHORIZATION_HEADER_HTTP_1_1: jwt_token}


def bearer_auth(config):
    """Create authentication headers based on JWT token generated by Keycloak from username and password."""
    keycloak_config = KeycloakConfig(config)
    keycloak_config.cache_ttl = 0
    keycloak_config.cache_min_time_between_requests = 0

    tls_config = ClientTLSConfig(TLSConfigType.HTTP, "keycloak", config)

    keycloak_client = KeycloakClient(
        name="temporary_keycloak_client",
        logger=None,
        keycloak_config=keycloak_config,
        tls_config=tls_config,
        onstart_retrying=never_retrying,
    )
    jwt_token = keycloak_client.get_token("admin", "admin")["access_token"]  # Requires the local Keycloak to run

    return {AUTHORIZATION_HEADER_HTTP_1_1: f"Bearer {jwt_token}"}


def basic_auth():
    """Create authentication headers containing Keycloak username and password."""
    payload = base64.b64encode("admin:admin".encode(ENCODING)).decode(ENCODING)

    return {AUTHORIZATION_HEADER_HTTP_1_1: f"Basic {payload}"}


def create_internal_jwt_header(jwt_token):
    """Create fields for internal JWT authorization header."""
    return AUTHORIZATION_HEADER_HTTP_2, f"{InternalJWTAuthenticator.SCHEME} {jwt_token}"


def get_authorization_header(headers):
    """Get value of authorization header from headers."""
    for header, value in headers:
        if header == AUTHORIZATION_HEADER_HTTP_2:
            return value
    return None


class JWKParsingError(AICoreException):
    """Error while parsing JWK."""


class Identity:
    """Identity parsed during authentication when processing incoming request."""

    ID_FIELD = "id"
    USERNAME_FIELD = "username"
    ROLES_FIELD = "roles"
    MODULE_FIELD = "module"
    SERVICE_IDENTITY_FIELD = "serviceIdentity"

    def __init__(self, user_identity_dict, service_identity_dict):
        self.user_identity_dict = user_identity_dict or {}
        self.service_identity_dict = service_identity_dict or {}

    def __repr__(self):
        if self.user_identity_dict and self.service_identity_dict:
            service_identity = self.serialize_identity("ServiceIdentity", self.service_identity_dict)
            user_identity_dict = {**self.user_identity_dict, self.SERVICE_IDENTITY_FIELD: service_identity}

            return self.serialize_identity("ImpersonatedUserIdentity", user_identity_dict)

        if self.service_identity_dict:
            return self.serialize_identity("ServiceIdentity", self.service_identity_dict)

        return self.serialize_identity("SimpleUserIdentity", self.user_identity_dict)

    def __eq__(self, other):
        return (
            isinstance(other, Identity)
            and self.user_identity_dict == other.user_identity_dict
            and self.service_identity_dict == other.service_identity_dict
        )

    @staticmethod
    def serialize_identity(identity_name, fields):
        """Serialize identity similarly as java."""
        serialized_fields = ", ".join([f"{key}={value}" for key, value in fields.items()])
        return f"{identity_name}({serialized_fields})"


class JWK:
    """Wrapper class for jwcrypto.jwk.JWK used for parsing our private/counterparty's public key from config.

    JSON Web Key - https://tools.ietf.org/html/rfc7517
    """

    # possible key types: https://www.iana.org/assignments/jose/jose.xhtml#web-key-types
    SUPPORTED_KEY_TYPES = {"EC", "RSA", "oct"}
    SYMMETRIC_KEY_TYPES = {"oct"}

    def __init__(self, jwk_info: jwcrypto.jwk.JWK):
        self.jwk = jwk_info
        self.key_id = jwk_info.key_id
        self.key_type = jwk_info.key_type
        # possible algorithms: https://www.iana.org/assignments/jose/jose.xhtml#web-signature-encryption-algorithms
        self.algorithm = jwk_info.alg

    @classmethod
    def parse_jwk(cls, jwk_info):
        """Parse JWK from base64-encoded/raw string containing JWK as JSON."""
        try:
            # base64 encoded -> create json
            jwk_json = base64.b64decode(jwk_info)
            jwk_json = jwk_json.decode(ENCODING)
        except (binascii.Error, UnicodeDecodeError):
            # Not base64 encoded -> assume raw json string was passed
            # Remove escaping that is needed in java
            jwk_json = jwk_info.replace("\\", "")

        jwk_parsed = jwcrypto.jwk.JWK.from_json(jwk_json)

        if not jwk_parsed:
            raise JWKParsingError("Malformed private JWK.")
        if jwk_parsed.key_type not in cls.SUPPORTED_KEY_TYPES:
            raise JWKParsingError("Unsupported JWK.")

        return cls(jwk_parsed)

    def to_private_key(self):
        """Export private or symmetric key based on used algorithm."""
        return (
            self.jwk.export_symmetric() if self.symmetric else self.jwk.export_to_pem(private_key=True, password=None)
        )

    def to_public_key(self):
        """Export public or symmetric key based on used algorithm."""
        return self.jwk.export_symmetric() if self.symmetric else self.jwk.export_to_pem()

    @property
    def symmetric(self):
        """If the used cryptographic algorithm is symmetric or not."""
        return self.key_type in self.SYMMETRIC_KEY_TYPES


class InternalJWTGenerator:
    """Generates JWT tokens for outgoing requests in peer-to-peer JWT, based on our private key.

    JSON Web Tokens - https://tools.ietf.org/html/rfc7519
    JSON Object Signing and Encryption (JOSE) - https://tools.ietf.org/html/rfc7165
    """

    USER_IDENTITY_CLAIM = "usr"

    def __init__(self, algorithm_name: str, key_id: str, private_key: str, expiration: int):
        self.algorithm_name = algorithm_name
        self.headers = {
            "alg": self.algorithm_name,  # https://tools.ietf.org/html/rfc7515#section-4.1.1
            "typ": INTERNAL_TOKEN_TYPE,  # https://tools.ietf.org/html/rfc7515#section-4.1.9
            "kid": key_id,  # https://tools.ietf.org/html/rfc7515#section-4.1.4
        }
        self.private_key = private_key
        self.expiration_delta = datetime.timedelta(seconds=expiration)

    @classmethod
    def from_jwk(cls, jwk: str, jwt_expiration: int):
        """Parse info from JWK (JSON Web Key)."""
        jwk_parsed = JWK.parse_jwk(jwk)

        algorithm = jwk_parsed.algorithm
        key_id = jwk_parsed.key_id
        private_key = jwk_parsed.to_private_key()

        return cls(algorithm, key_id, private_key, jwt_expiration)

    def generate(self, identity: Optional[Identity] = None):
        """Generate JWT token for internal authentication."""
        now = datetime_now()
        payload: dict[str, Any] = {
            "iat": now,  # https://tools.ietf.org/html/rfc7519#section-4.1.6
            "nbf": now,  # https://tools.ietf.org/html/rfc7519#section-4.1.5
            "exp": now + self.expiration_delta,  # https://tools.ietf.org/html/rfc7519#section-4.1.4
        }
        if identity:
            payload[self.USER_IDENTITY_CLAIM] = identity.user_identity_dict

        return jwt.encode(payload, self.private_key, self.algorithm_name, headers=self.headers)


class JWTKeyError(AICoreException):
    """Error while parsing known JWT keys."""


class AuthenticationError(AICoreException):
    """Error while performing authentication."""


class InternalJWTAuthenticator:
    """Authenticator that checks and validates the signature of received internal JWT token in peer-to-peer auth.

    Signature validation is performed using a public key of the sender.
    """

    SCHEME = "Internal-jwt"
    WWW_AUTHENTICATE = "Internal-jwt"

    def __init__(self, platform_deployments, impersonation_role):
        self.deployments = {}  # Deployments by their names
        self.jwt_keys = []
        self.impersonation_role = impersonation_role
        self.supported_www_methods = {"Internal-jwt"}

        self.update_jwt_keys(platform_deployments)

    def update_jwt_keys(self, platform_deployments):
        """Add new or update existing JWT keys."""
        deployments = platform_deployments or {}
        jwt_keys = []

        for deployment_name, deployment in deployments.items():
            for key_name, key_dict in deployment["jwt_keys"].items():
                try:
                    content = key_dict["content"]
                    fingerprint = key_dict["fingerprint"]
                except KeyError as error:
                    raise JWTKeyError(f"JWT key '{key_name}' is missing required field {error}") from error

                jwk_parsed = JWK.parse_jwk(content)
                public_key = jwk_parsed.to_public_key()

                jwt_keys.append(
                    {
                        "key_id": fingerprint,
                        "public_key": public_key,
                        "is_revoked": key_dict.get("is_revoked", False),
                        "deployment_name": deployment_name,
                    }
                )

        self.deployments = deployments
        self.jwt_keys = jwt_keys

    def authenticate(self, jwt_token) -> Identity:
        """Authenticate successfully or throw exception."""
        if not jwt_token:
            raise AuthenticationError("Missing authentication token in the header")

        header = self.parse_and_validate_header(jwt_token)
        requester_key_id = header.get("kid")
        algorithm = header.get("alg")

        jwt_key = self.get_jwt_key(requester_key_id)
        public_key = jwt_key["public_key"]

        try:
            payload = jwt.decode(
                jwt_token,
                key=public_key,
                verify=True,
                algorithms=[algorithm],
                options={
                    "require": ["iat", "nbf", "exp"],
                    "verify_iat": True,
                    "verify_nbf": True,
                    "verify_exp": True,
                    "verify_signature": True,
                },
                leeway=DEFAULT_LEEWAY,
            )
        except jwt.PyJWTError as error:
            raise AuthenticationError("Malformed JWT token") from error

        deployment_name = jwt_key["deployment_name"]
        deployment = self.deployments[deployment_name]

        identity = self.parse_identity(deployment, payload)

        # Service roles can be None (when defining it as "null" in properties)
        service_roles = identity.service_identity_dict["roles"] or {}

        if identity.user_identity_dict and self.impersonation_role not in service_roles:
            raise AuthenticationError(
                f"Impersonation is not allowed, only '{self.impersonation_role}' is allowed to impersonate"
            )

        return identity

    @staticmethod
    def parse_and_validate_header(jwt_token):
        """Parse header from JWT token and validate it."""
        try:
            header = jwt.get_unverified_header(jwt_token)  # we get info about requester from header part of token
        except jwt.InvalidTokenError as error:
            raise AuthenticationError("Malformed JWT token") from error
        token_type = header.get("typ")
        if token_type != INTERNAL_TOKEN_TYPE:
            raise AuthenticationError(f"Invalid token type {token_type}")
        requester_key_id = header.get("kid")
        if not requester_key_id:
            raise AuthenticationError("Malformed JWT token, missing or empty key id")
        return header

    def get_jwt_key(self, requester_key_id):
        """Get public key from known keys."""
        for jwt_key in self.jwt_keys:
            if jwt_key["key_id"] == requester_key_id:
                found_jwt_key = jwt_key
                break
        else:
            raise AuthenticationError(f"Public key not found for requested kid {requester_key_id}")

        if found_jwt_key["is_revoked"]:
            raise AuthenticationError(f"Public key is revoked for requested kid {requester_key_id}")

        return found_jwt_key

    @classmethod
    def parse_identity(cls, jwt_key_deployment, payload) -> Identity:
        """Parse identity from decoded token in a similar way as in java, but only with important fields."""
        user_identity_dict = payload.get(InternalJWTGenerator.USER_IDENTITY_CLAIM)
        service_identity_dict = {
            Identity.ID_FIELD: jwt_key_deployment["uri"],
            Identity.MODULE_FIELD: jwt_key_deployment["module"],
            Identity.ROLES_FIELD: jwt_key_deployment["roles"],
        }

        return Identity(user_identity_dict, service_identity_dict)

    def process_config_reload(self, new_config):
        """Update JWT keys based on new config."""
        new_config.update_if_changed("platform_deployments", self.update_jwt_keys)


class JWTAuthenticator:
    """Authenticator that validates and verifies signature of JWT token against public keys received from keycloak."""

    SENTINEL = object()

    SCHEME = "Bearer"  # https://tools.ietf.org/html/rfc6750#section-2.1

    def __init__(self, keycloak_client: KeycloakClient, issuer: str, audience: str, expected_algorithm: str):
        self.keycloak_client = keycloak_client
        self.issuer = issuer
        self.audience = audience
        self.expected_algorithm = expected_algorithm
        self.supported_www_methods = {f'Bearer realm="{self.keycloak_client.realm}"'}

        self.jwt_object = jwt.PyJWT()

    def authenticate(self, jwt_token) -> Identity:
        """Authenticate successfully or throw exception.

        Note:
            It seems, that java uses only signed JWT tokens.
            It doesn't set 'jweKeySelector' to DefaultJWTProcessor in TokenValidator.

            java JWTClaimsVerifier - verify expiration, not before, issuer, audience
        """
        if not jwt_token:
            raise AuthenticationError("Missing token in the header")

        try:
            header = jwt.api_jws.get_unverified_header(jwt_token)
        except jwt.InvalidTokenError as error:
            raise AuthenticationError("Malformed JWT token") from error

        algorithm = header.get("alg")
        if not algorithm or algorithm == ALG_NONE:
            raise AuthenticationError("Token must be signed or encrypted")
        if self.expected_algorithm and algorithm != self.expected_algorithm:
            raise AuthenticationError("Signed JWT rejected: Another algorithm expected")

        payload = self.parse_signed_payload(jwt_token)
        self.validate_claims(payload)

        return self.parse_identity(payload)

    def parse_signed_payload(self, jwt_token: str) -> dict[str, Any]:
        """Try different keys from Keycloak to decode the token and return payload if successful."""
        certs = self.keycloak_client.get_certs()
        payload = self._parse_signed_payload(jwt_token, certs)

        if payload != self.SENTINEL:
            return payload

        # Public certificate for key not found - try reload certificates even if cache is still valid
        new_certs = self.keycloak_client.get_certs(force_reload=True)
        if new_certs != certs:
            payload = self._parse_signed_payload(jwt_token, new_certs)

        if payload == self.SENTINEL:
            raise AuthenticationError("Signed JWT rejected: Invalid signature")

        return payload

    def _parse_signed_payload(self, jwt_token: str, certs: dict[str, dict[str, Any]]):
        """Try different keys from Keycloak's certificate cache to decode the token and return payload if successful."""
        keys = [key for key in certs.get("keys", {}) if key["alg"] == self.expected_algorithm]

        for key in keys:
            try:
                return self.parse_signed_payload_for_key(jwt_token, key)
            except jwt.InvalidSignatureError:
                # verification of token signature was not successful with current key -> try different one
                continue
            except jwt.InvalidTokenError as error:
                raise AuthenticationError("Malformed JWT token") from error

        return self.SENTINEL

    def parse_signed_payload_for_key(self, jwt_token: str, key: dict) -> dict[str, Any]:
        """Decode token with supplied key and parse payload if successful."""
        # create public key
        jwk_info = jwcrypto.jwk.JWK(**key)
        jwk_parsed = JWK(jwk_info)
        public_key = jwk_parsed.to_public_key()

        # decode and verify just the signature -> used to find correct public key with no other verification
        return self.jwt_object.decode(
            jwt_token,
            key=public_key,
            verify=True,
            algorithms=[self.expected_algorithm],
            options={
                "require": [],
                "verify_iat": False,
                "verify_nbf": False,
                "verify_exp": False,
                "verify_iss": False,
                "verify_aud": False,
                "verify_signature": True,
            },
        )

    def validate_claims(self, payload: dict):
        """Validate claims in parsed payload."""
        try:
            self.jwt_object._validate_claims(
                payload,
                options={
                    "require": [],
                    "verify_iat": True,
                    "verify_nbf": True,
                    "verify_exp": True,
                    "verify_iss": True if self.issuer else False,
                    "verify_aud": True if self.audience else False,
                },
                audience=self.audience,
                issuer=self.issuer,
            )
        except jwt.InvalidTokenError as error:
            raise AuthenticationError("Claims validation failed") from error

    @classmethod
    def parse_identity(cls, payload) -> Identity:
        """Parse identity from decoded token in a similar way as in java, but only with important fields."""
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Missing 'sub' claim in JWT token")

        username = payload.get("preferred_username")
        if not username:
            raise AuthenticationError("Missing 'preferred_username' claim in JWT token")

        realm_access = payload.get("realm_access", {})
        roles = realm_access.get("roles") or []

        return Identity(
            user_identity_dict={
                Identity.ID_FIELD: user_id,
                Identity.USERNAME_FIELD: username,
                Identity.ROLES_FIELD: roles,
            },
            service_identity_dict=None,
        )

    def process_config_reload(self, new_config):
        """Support for duck typing - no update from new config supported."""
        pass


class BasicAuthAuthenticator:
    """Authenticator that checks Basic Auth against Keycloak."""

    SCHEME = "Basic"  # https://tools.ietf.org/html/rfc7617#section-2

    def __init__(self, keycloak_client: KeycloakClient, jwt_authenticator: JWTAuthenticator):
        self.keycloak_client = keycloak_client
        self.jwt_authenticator = jwt_authenticator
        self.supported_www_methods = {f'Basic realm="{self.keycloak_client.realm}"'}

    def authenticate(self, credentials) -> Identity:
        """Authenticate successfully or throw exception."""
        if not credentials:
            raise AuthenticationError("Missing credentials in the header")

        try:
            credentials_decoded_bytes = base64.b64decode(credentials)
            credentials_decoded = credentials_decoded_bytes.decode(ENCODING)
        except (binascii.Error, UnicodeDecodeError) as error:
            raise AuthenticationError("Credentials are not base64-encoded") from error

        credentials_split = credentials_decoded.split(":", 2)
        if len(credentials_split) != 2:
            raise AuthenticationError("Credentials must contain username and password")

        username, password = credentials_split
        try:
            access_token = self.keycloak_client.get_token(username, password)
            access_token = access_token["access_token"]
        except Exception as error:
            raise AuthenticationError(f"Failed to obtain token for user '{username}'") from error

        return self.jwt_authenticator.authenticate(access_token)

    def process_config_reload(self, new_config):
        """Support for duck typing - no update from new config supported."""
        pass


class AuthorizationHeaderAuthenticatorContainer:
    """Container with all supported auth methods that uses value from authorization header to authenticate."""

    def __init__(self, authenticators):
        self.authenticators = authenticators

        supported_www_methods = set()
        for authenticator in self.authenticators.values():
            supported_www_methods = supported_www_methods | authenticator.supported_www_methods

        self.supported_www_methods = supported_www_methods

    def authenticate(self, authorization_header) -> Identity:
        """Authenticate successfully or throw exception."""
        # Ataccama requires authentication, so disabling all modes of it = nobody can access protected stuff
        if not self.authenticators:
            raise AuthenticationError("No authenticators provided")

        if not authorization_header:
            raise AuthenticationError("No authorization header")

        scheme, value = self.parse_scheme_and_value(authorization_header)
        if not scheme or not value:
            raise AuthenticationError(f"Incorrect authorization header {authorization_header}")

        authenticator = self.authenticators.get(scheme)
        if not authenticator:
            raise AuthenticationError(f"No authenticator for scheme {scheme}")

        return authenticator.authenticate(value)

    @staticmethod
    def parse_scheme_and_value(header: str):
        """Parse scheme and value from value from authorization header."""
        header = header.strip()
        split = re.split("\\s+", header)
        return tuple(split) if len(split) == 2 else (None, None)


class AllowedRolesAuthenticator:
    """Authenticator that uses roles from parsed identity to allow access."""

    def __init__(self, allowed_roles: set[str], default_allow: bool, delegate_authenticator):
        self.allowed_roles = allowed_roles
        self.default_allow = default_allow

        self.delegate_authenticator = delegate_authenticator
        self.supported_www_methods = delegate_authenticator.supported_www_methods

    def authenticate(self, authorization_header) -> Identity:
        """Allow access only to specified roles or throw exception."""
        user_identity = self.delegate_authenticator.authenticate(authorization_header)

        if not self.allowed_roles:
            if self.default_allow:
                return user_identity
            else:
                raise AuthenticationError("Nobody can access this endpoint")

        user_roles = user_identity.user_identity_dict.get(Identity.ROLES_FIELD, [])
        service_roles = user_identity.service_identity_dict.get(Identity.ROLES_FIELD, [])
        all_roles = set(user_roles) | set(service_roles)

        if not (self.allowed_roles & all_roles):
            raise AuthenticationError(f"Only {self.allowed_roles} roles can access this endpoint")

        return user_identity


class KeycloakConfig:
    """Wrapper for options used in Keycloak client."""

    def __init__(self, config):
        for keycloak_option_name in [
            "server_url",
            "realm",
            "token_client_id",
            "token_secret",
            "token_key_cache_ttl",
            "token_key_cache_min_time_between_requests",
        ]:
            value = getattr(config, f"keycloak_{keycloak_option_name}")
            setattr(self, keycloak_option_name, value)


class KeycloakError(AICoreException):
    """Exception when making calls to Keycloak API."""


class KeycloakClient(ReadinessDependency):
    """Keycloak client wrapper with retrying."""

    URL_TOKEN = "/protocol/openid-connect/token"
    URL_CERTS = "/protocol/openid-connect/certs"

    def __init__(
        self,
        name: str,
        logger,
        keycloak_config: KeycloakConfig,
        tls_config: ClientTLSConfig,
        onstart_retrying: tenacity.Retrying,
        retrying: tenacity.Retrying = never_retrying,
    ):
        super().__init__(name, logger, onstart_retrying, readiness_predicate=self.is_ready, tracks_liveness=False)

        self.realm = keycloak_config.realm
        self.client_id = keycloak_config.token_client_id
        self.client_secret_key = keycloak_config.token_secret

        url = keycloak_config.server_url.rstrip("/")
        url = f"{url}/realms/{self.realm}"

        self.http_realm_client = HTTPClient(url, tls_config)

        self.cache_ttl = keycloak_config.token_key_cache_ttl
        # For DDoS prevention against requests with unknown keys
        self.cache_min_time_between_requests = keycloak_config.token_key_cache_min_time_between_requests

        self.certs_cache: dict[str, dict[str, Any]] = {}
        self._last_certs_fetch_time = 0

        retry_exceptions = (requests.ConnectionError, requests.Timeout)
        self.retrying = retrying.copy(
            retry=tenacity.retry_if_exception_type(retry_exceptions),
            before_sleep=self._log_send_attempt,
            reraise=True,
        )

    def __repr__(self):
        return f"Keycloak client {self.name!r} ({self.http_realm_client.url!r})"

    def get_token(self, username: str, password: str):
        """Get token from Keycloak for given credentials with retrying."""
        payload = {
            "username": username,
            "password": password,
            "client_id": self.client_id,
            "client_secret": self.client_secret_key,
            "grant_type": ["password"],
        }
        return self.retrying(self._send, "POST", path=self.URL_TOKEN, data=payload)

    def get_certs(self, force_reload: bool = False):
        """Get JWK public keys from Keycloak with retrying."""
        last_cache_reload_interval = time.monotonic() - self._last_certs_fetch_time

        if last_cache_reload_interval >= self.cache_min_time_between_requests and (
            force_reload or last_cache_reload_interval >= self.cache_ttl
        ):
            self.certs_cache = self.retrying(self._send, "GET", path=self.URL_CERTS)
            self._last_certs_fetch_time = time.monotonic()

        return self.certs_cache

    def prepare_state_change_log_record(self) -> tuple[str, dict[str, Any]]:
        """Return log message and kwargs appropriate for the new state the Keycloak client is in."""
        return "{self!r} is {health!r}", {"event_id": LogId.keycloak_client_state_change}

    def is_ready(self) -> bool:
        """Return True if the Keycloak connection was established."""
        try:
            self._send("GET")
        except requests.RequestException as error:
            reason = parse_retryable_reason(error)

            if not reason:
                raise error

            self.health.not_ready(reason)
            return False

        return True

    def _send(self, method, **kwargs):
        if method == "GET":
            send_function = self.http_realm_client.get
        elif method == "POST":
            send_function = self.http_realm_client.post
        else:
            raise KeycloakError(f"Unknown method {method}")

        result = send_function(**kwargs)
        result.raise_for_status()

        return result.json()

    def _log_send_attempt(self, retry_state: tenacity.RetryCallState):
        """Log failed attempt to send request to Keycloak."""
        path = retry_state.kwargs.get("path")
        url = merge_url(self.http_realm_client.url, path)

        error = retry_state.outcome.exception()

        self.logger.warning(
            "Keycloak client raised {error_name!r} while sending request at {url}, next attempt in {sleep} s",
            error=error,
            error_name=type(error).__name__,
            url=url,
            attempt=retry_state.attempt_number,
            sleep=retry_state.next_action.sleep,
            message_id=LogId.keycloak_client_send,
        )
