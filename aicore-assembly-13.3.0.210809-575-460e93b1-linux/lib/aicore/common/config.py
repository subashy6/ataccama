"""Centrally-managed configuration for all microservices."""

from __future__ import annotations

import contextlib
import enum
import json
import os
import re
import time
import uuid

from typing import TYPE_CHECKING

import more_itertools

from aicore.common.actuator import Actuator
from aicore.common.auth import InternalJWTGenerator
from aicore.common.certificates import create_symmetric_keystore, load_keystore_data
from aicore.common.command import (
    ConfigServiceHeartbeatCommand,
    GetLatestPropertiesCommand,
    GetLatestPropertiesVersionCommand,
    PropertiesAppliedCommand,
    PropertiesNothingToApplyCommand,
)
from aicore.common.constants import SUPPORTED_DIALECTS
from aicore.common.encryption import ENCRYPTION_PREFIX, SUPPORTED_CONTEXTS, decrypt_value, parse_encrypted_property_info
from aicore.common.exceptions import AICoreException
from aicore.common.grpc import GRPCClient, GRPCClientError
from aicore.common.logging import LogConfig, Logger
from aicore.common.metrics import MetricsDAO
from aicore.common.registry import LogId
from aicore.common.tls import ClientTLSConfig, ServerTLSConfig, TLSConfigType
from aicore.common.utils import random_correlation_id


if TYPE_CHECKING:
    from typing import Any, Generator, Optional

    from aicore.common.types import CorrelationId


REFERENCE_MATCH_PATTERN = re.compile(".*\\${(.*)}.*")
REFERENCE_FIND_PATTERN = re.compile("\\${([^}]*)}")


class ConfigurationError(AICoreException):
    """The configuration is invalid."""


def get_config(*module_configs: dict, microservice_name: str = "dummy_microservice"):
    """Load the configuration for given modules and corresponding options."""
    all_config_options = {}

    for config_options in module_configs:
        all_config_options.update(config_options)

    # Not used in production code - no microservice
    return Config.from_all_sources(microservice_name, all_config_options)


def json_path(dictionary, path):
    """Get value from given path in the nested dictionary."""
    current_position = dictionary

    for path_element in normalize_property_key(path).split("."):
        try:
            current_position = current_position[path_element]
        except KeyError as error:
            raise ConfigurationError(f"Configuration path {path!r} not found") from error

    return current_position


def normalize_property_key(key):
    """Normalize property key from every source."""
    # ATACCAMA_PROPERTY_MYPROPERTY -> ataccama.property.myproperty
    # ataccama.property.my-property -> ataccama.property.myproperty
    normalized = key.strip().lower().replace("_", ".").replace("-", "")

    # ataccama.property[1].myproperty[1] -> ataccama.property[1].myproperty.1
    end_list_match = re.match("(.*)\\[([0-9]+)\\]$", normalized)

    if end_list_match:
        prefix = end_list_match[1]
        index = end_list_match[2]

        normalized = f"{prefix}.{index}"

    return normalized


def properties_to_nested_dict(flat_properties: dict[str, str]) -> dict[str, Any]:
    """Make properties nested in dictionary."""
    transformed_properties: dict[str, Any] = {}

    for key, value in flat_properties.items():
        *inner_key_parts, last_key_part = key.split(".")
        key_properties = transformed_properties

        for key_part in inner_key_parts:
            # Replace "null" with empty dict for dynamically created properties, example of why:
            #   1. ataccama.client.connection=null - "null" is set as a value for connections in the first place
            #   2. ataccama.client.connection.mmm...=... - "null" has to be replaced by dict for connections
            if key_properties.get(key_part, "null") == "null":
                key_properties[key_part] = {}
            key_properties = key_properties[key_part]

        # Not assigning directly because
        #   - of the dynamically created properties, example:
        #      1. ataccama.client.connection.mmm...=... - connections contain dict
        #      2. ataccama.client.connection=null - "null" shouldn't replace already existing dict for connections
        #   - lists in the format ataccama.property.1=... (or ATACCAMA_PROPERTY_1=...)
        with contextlib.suppress(ValueError):
            last_key_part = int(last_key_part)

        key_properties.setdefault(last_key_part, value)

    return transformed_properties


def resolve_references(flat_dictionary: dict[str, str]):
    """Resolve property values for properties that reference other properties."""
    resolved_references = {}

    for key, value in flat_dictionary.items():
        while REFERENCE_MATCH_PATTERN.match(value):  # Resolve references to references
            not_resolved_value = value
            value = resolve_single_property_references(key, value, flat_dictionary)

            if not_resolved_value == value:
                # We didn't resolve anything in this round -> stop
                break

        resolved_references[key] = value

    flat_dictionary.update(resolved_references)


def resolve_single_property_references(key, value_to_resolve, flat_dictionary: dict[str, str]):
    """Resolve property values for single property that references other properties."""
    references = REFERENCE_FIND_PATTERN.findall(value_to_resolve)

    resolved_value = value_to_resolve
    for reference in references:
        normalized_reference = normalize_property_key(reference)

        if normalized_reference == key:
            raise ConfigurationError(f"Property '{key}' references itself")

        if normalized_reference in flat_dictionary:
            reference_value = flat_dictionary[normalized_reference]
            resolved_value = resolved_value.replace(f"${{{reference}}}", reference_value)

    return resolved_value


def property_value(flat_properties: dict[str, str], config_option, microservice_name):
    """Get property value from already loaded properties."""
    property_key = normalize_property_key(config_option["key"])

    if property_key not in flat_properties:
        raise ConfigurationError(f"Configuration path {property_key!r} not found")

    value = flat_properties[property_key]
    property_deserializer = config_option["deserializer"]

    return deserialize_property_value(value, property_deserializer, microservice_name)


def parse_list(value):
    """Parse list from multiple available list definitions."""
    if isinstance(value, list):
        return value

    if isinstance(value, dict):
        parsed_list = []
        max_index = max(value.keys())

        for index in range(max_index + 1):
            if index not in value:
                raise ConfigurationError(f"Index '{index}' not defined")

            parsed_list.append(value[index])

        return parsed_list

    return json.loads(value)


TYPE_TRANSFORMATIONS = {
    list: parse_list,
    dict: lambda value: value if isinstance(value, dict) else json.loads(value),
    bool: lambda value: value if isinstance(value, bool) else value.lower() == "true",
}


def deserialize_property_value(value, deserializer, microservice_name):
    """Deserialize single property value with given property deserializer."""
    if value == "null":
        return None

    deserializer = TYPE_TRANSFORMATIONS.get(deserializer, deserializer)

    if (
        hasattr(deserializer, "__code__") and "microservice_name" in deserializer.__code__.co_varnames
    ):  # Hack: Special deserializers (e.g. channel_tls) also need the microservice name
        return deserializer(value, microservice_name=microservice_name)

    return deserializer(value)


def create_config_logger(microservice_name, properties):
    """Create temporary logger that will be used to log info during first Config initialization."""
    logging_options = ConfigOptionsBuilder().common_options("paths", "logging").options

    # Temporary config => doesn't have to be reloadable - explicitly setting None value
    logging_config = Config(microservice_name, logging_options, properties_loader=None)
    logging_config.from_dict(properties)

    return Logger("config_logger", LogConfig.from_config(logging_config))


class ConfigServiceClient:
    """Client used for communication with Config Service."""

    def __init__(self, replica_id, grpc_client, logger):
        self.replica_id = replica_id
        self.grpc_client = grpc_client
        self.logger = logger

        self.last_call_successful = True

        self.last_heartbeat = 0

        self.last_properties_poll = 0
        self.last_properties_version = None

    def heartbeat(self, heartbeat_interval: int, correlation_id: Optional[CorrelationId] = None) -> None:
        """Ping Config Service with heartbeat for current replica."""
        if self.last_heartbeat + heartbeat_interval > time.monotonic():
            return

        command = ConfigServiceHeartbeatCommand(self.replica_id)
        correlation_id = correlation_id or random_correlation_id()

        self.send_or_fail_silently(command, correlation_id)
        self.last_heartbeat = time.monotonic()

    def poll_latest_properties_version(self, correlation_id: CorrelationId) -> Optional[str]:
        """Poll latest version of properties from Config Service."""
        command = GetLatestPropertiesVersionCommand()

        self.send_or_fail_silently(command, correlation_id)
        self.last_properties_poll = time.monotonic()

        return command.version

    def poll_latest_properties(self, correlation_id: CorrelationId) -> Optional[dict[str, Any]]:
        """Poll new properties from Config Service."""
        command = GetLatestPropertiesCommand()

        self.send_or_fail_silently(command, correlation_id)
        self.last_properties_poll = time.monotonic()

        # Version is empty when there is an empty initial deployment in Config Service without any properties
        if not command.version:
            return None

        self.last_properties_version = command.version

        return command.properties

    def notify_properties_applied(self, correlation_id: CorrelationId) -> None:
        """Let Config Service know that lastly reloaded properties were applied."""
        command = PropertiesAppliedCommand(self.replica_id, self.last_properties_version)
        self.send_or_fail_silently(command, correlation_id)

    def notify_properties_nothing_to_apply(self, correlation_id: CorrelationId) -> None:
        """Let Config Service know that there was nothing to apply for the last reload."""
        command = PropertiesNothingToApplyCommand(self.replica_id)
        self.send_or_fail_silently(command, correlation_id)

    def send_or_fail_silently(self, command, correlation_id):
        """Send gRPC request to Config Service with suppressing communication errors."""
        try:
            self.grpc_client.send(command, correlation_id, log_rpc_error=self.last_call_successful)

            if not self.last_call_successful:
                self.logger.info(
                    f"Connection with {self.grpc_client.name} re-established.",
                    message_id=LogId.config_service_connection_reestablished,
                    correlation_id=correlation_id,
                )

            self.last_call_successful = True
        except GRPCClientError:  # Suppress only communication errors
            # Java just logs the error, nothing else - already logged by GRPCClient
            self.last_call_successful = False

    def is_properties_interval_exceeded(self, refresh_interval: int) -> bool:
        """Check whether we exceeded interval for contacting Config Service for new properties."""
        return not self.last_properties_version or self.last_properties_poll + refresh_interval <= time.monotonic()

    @contextlib.contextmanager
    def running(self, timeout: float) -> Generator[ConfigServiceClient]:
        """Context manager for a running grpc client."""
        with self.grpc_client.running(timeout):
            yield self


class PropertiesLoader:
    """Loader for loading properties from multiple sources."""

    def __init__(self, microservice_name):
        self.microservice_name = microservice_name

        suffix = uuid.uuid4().hex  # Java uses the same suffix
        self.replica_id = f"aicore_{self.microservice_name}_{suffix}"

        self.env_properties: dict[str, str] = {}
        self.default_file_properties: dict[str, str] = {}
        self.etc_file_properties: dict[str, str] = {}
        self.config_service_properties: dict[str, str] = {}

        self.config_service_client: Optional[ConfigServiceClient] = None

    def load_all_sources(self) -> dict[str, str]:
        """Load properties from all supported sources - ENV, application.properties files and Configuration Service."""
        # Properties in etc/application.properties can contain Config Service url -> load it first
        for load_method in [
            self.load_env_properties,
            self.load_default_file_properties,
            self.load_etc_file_properties,
            self.load_config_service_properties,
        ]:
            load_method()

        merged_properties = self.merge_loaded_properties(self.config_service_override)
        resolve_references(merged_properties)

        return merged_properties

    @property
    def config_service_override(self):
        """Flag determining whether Config Service properties should override the ones in etc/application.properties."""
        # Copy properties since we want to do final reference resolution only after everything is loaded
        config_service_properties = self.config_service_properties.copy()
        # Resolve property reference just in case the override flag references something in Config Service
        resolve_references(config_service_properties)

        config_service_override_option = CONFIGURATION_SERVICE_DOCUMENT_OPTIONS["config_service_override_local"]
        try:
            return property_value(config_service_properties, config_service_override_option, self.microservice_name)
        except ConfigurationError:
            return config_service_override_option["default_value"]

    def load_env_properties(self):
        """Load and update internal state with Ataccama properties from env variables."""
        self.env_properties = {
            normalize_property_key(key): value for key, value in os.environ.items() if key.startswith("ATACCAMA")
        }

        # If these properties are not defined in ENV, their default values are used
        # These properties are necessary to load the default application.properties
        for option in [
            PATHS_OPTIONS["root_path"],
            PATHS_OPTIONS["lib_path"],
            PATHS_OPTIONS["default_properties_location"],
        ]:
            normalized_key = normalize_property_key(option["key"])
            if normalized_key in self.env_properties:
                continue
            self.env_properties[normalized_key] = option["default_value"]

    def load_default_file_properties(self):
        """Load and update internal state with properties from file like application.properties."""
        # Config Service properties not loaded yet - value of override flag doesn't matter
        loaded_properties = self.merge_loaded_properties(config_service_override=False)
        resolve_references(loaded_properties)

        file_path = property_value(
            loaded_properties, PATHS_OPTIONS["default_properties_location"], self.microservice_name
        )
        self.default_file_properties = self.load_properties_from_file(file_path)

    def load_etc_file_properties(self):
        """Load and update internal state with properties from file like application.properties in etc/ folder."""
        # Config Service properties not loaded yet - value of override flag doesn't matter
        loaded_properties = self.merge_loaded_properties(config_service_override=False)
        resolve_references(loaded_properties)

        etc_file_path = property_value(
            loaded_properties, PATHS_OPTIONS["etc_properties_location"], self.microservice_name
        )
        self.etc_file_properties = self.load_properties_from_file(etc_file_path)

    def load_config_service_properties(self):
        """Load and update internal state with with properties from Config Service."""
        loaded_properties = self.merge_loaded_properties(self.config_service_override)
        resolve_references(loaded_properties)

        config_service_host = property_value(
            loaded_properties, CONFIGURATION_SERVICE_OPTIONS["config_service_host"], self.microservice_name
        )
        config_service_port = property_value(
            loaded_properties, CONFIGURATION_SERVICE_OPTIONS["config_service_grpc_port"], self.microservice_name
        )

        if not config_service_host or not config_service_port:
            logger = create_config_logger(self.microservice_name, loaded_properties)
            logger.info("Configuration Service connection not specified", message_id=LogId.config_service_not_specified)
            return

        self.config_service_client = self.create_config_service_client(loaded_properties)
        client_timeout = property_value(
            loaded_properties, READINESS_WAIT_CONFIG_OPTIONS["onstart_health_response_timeout"], self.microservice_name
        )

        # Wait indefinitely for Config Service to be ready - easy temporary solution with Resource.running
        with self.config_service_client.running(timeout=client_timeout):
            correlation_id = random_correlation_id()

            # Need to call heartbeat before first load of properties
            # Otherwise the replica will be shown as Pending in Config Service
            self.config_service_client.heartbeat(heartbeat_interval=0, correlation_id=correlation_id)

            reloaded_properties = self.reload_config_service_properties(
                refresh_interval=0, correlation_id=correlation_id
            )

            if reloaded_properties:
                self.config_service_client.notify_properties_applied(correlation_id)

        updated_properties = self.merge_loaded_properties(self.config_service_override)
        resolve_references(updated_properties)

        # Re-initialize Config Service gRPC client because:
        #   - it was shut down before (waiting for readiness was done using contextmanager)
        #   - use new properties from Config Service (mainly logging and JWT token expiration)
        self.config_service_client = self.create_config_service_client(updated_properties)

    def should_reload_config_service_properties(self, refresh_interval: int, correlation_id: CorrelationId) -> bool:
        """Check whether there is a new configuration in Config Service."""
        if not self.config_service_client or not self.config_service_client.is_properties_interval_exceeded(
            refresh_interval
        ):
            return False

        last_properties_version = self.config_service_client.last_properties_version
        new_version = self.config_service_client.poll_latest_properties_version(correlation_id)

        # There can be communication error - no new version is received
        return new_version and last_properties_version != new_version

    def reload_config_service_properties(
        self, refresh_interval: int, correlation_id: CorrelationId
    ) -> Optional[dict[str, str]]:
        """Reload properties that come from Config Service."""
        if not self.should_reload_config_service_properties(refresh_interval, correlation_id):
            return None

        new_properties = self.config_service_client.poll_latest_properties(correlation_id)

        if not new_properties:
            return None

        self.config_service_properties = {normalize_property_key(key): value for key, value in new_properties.items()}

        merged_properties = self.merge_loaded_properties(self.config_service_override)
        resolve_references(merged_properties)

        return merged_properties

    def reload_processed(self, status: ConfigChangeStatus, correlation_id: CorrelationId) -> None:
        """Notify Config Service that reload of configuration was processed with the resulted status."""
        STATUS_METHODS = {
            ConfigChangeStatus.APPLIED: self.config_service_client.notify_properties_applied,
            ConfigChangeStatus.NOTHING_TO_APPLY: self.config_service_client.notify_properties_nothing_to_apply,
            # There is no endpoint in Config Service corresponding to CANNOT_APPLY status
            ConfigChangeStatus.CANNOT_APPLY: lambda _: None,
        }

        STATUS_METHODS[status](correlation_id)

    def merge_loaded_properties(self, config_service_override: bool) -> dict[str, str]:
        """Merge properties from all supported sources."""
        merged_properties: dict[str, str] = {}

        # Config Service can override etc/application.properties or vice versa
        if config_service_override:
            MERGE_ORDER = [
                self.default_file_properties,
                self.etc_file_properties,
                self.config_service_properties,
                self.env_properties,
            ]
        else:
            MERGE_ORDER = [
                self.default_file_properties,
                self.config_service_properties,
                self.etc_file_properties,
                self.env_properties,
            ]

        for properties_source in MERGE_ORDER:
            merged_properties.update(properties_source)

        return merged_properties

    def create_config_service_client(self, properties) -> ConfigServiceClient:
        """Create Config Service gRPC client based on already loaded properties."""
        config_service_loading_options = ConfigOptionsBuilder().common_options("paths", "auth_out", "tls_out").options

        for option_name in ["config_service_host", "config_service_grpc_port"]:
            config_service_loading_options[option_name] = CONFIGURATION_SERVICE_OPTIONS[option_name]

        # Temporary config => doesn't have to be reloadable - explicitly setting None value
        loader_config = Config(self.microservice_name, config_service_loading_options, properties_loader=None)
        loader_config.from_dict(properties)

        jwt_generator = InternalJWTGenerator.from_jwk(loader_config.jwk, loader_config.jwt_expiration)
        tls_config = ClientTLSConfig(TLSConfigType.gRPC, "config_service", loader_config)

        logger = create_config_logger(self.microservice_name, properties)
        metrics = MetricsDAO()
        grpc_client = GRPCClient(
            "config_service_client",
            logger,
            loader_config.config_service_host,
            loader_config.config_service_grpc_port,
            jwt_generator,
            tls_config,
            metrics,
        )

        return ConfigServiceClient(self.replica_id, grpc_client, logger)

    @classmethod
    def load_properties_from_file(cls, path):
        """Load a dictionary with configuration options from file like application.properties."""
        try:
            with open(path, "rt") as config_file:
                return cls.parse_file_properties(config_file)
        except OSError as exception:
            raise ConfigurationError(f"Loading configuration from file {path} failed") from exception

    @classmethod
    def parse_file_properties(cls, lines):
        """Parse a dictionary with configuration options from content of file like application.properties."""
        properties = {}

        whole_property = ""
        multiline_property_lines_count = 0

        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue

            # '\' at the end of the line means multiline property
            if line.endswith("\\"):
                whole_property += line.rstrip("\\")
                multiline_property_lines_count += 1
                continue

            # '#' in the beginning of the line means comment (but not in the multiline property)
            if line.startswith("#") and not whole_property:
                continue

            whole_property += line
            key_value = whole_property.split("=", 1)
            if len(key_value) != 2:
                property_line = line_num - multiline_property_lines_count
                raise ConfigurationError(f"Cannot parse property key and value for property on line {property_line}")

            key = normalize_property_key(key_value[0])
            value = key_value[1].strip().strip('"')
            properties[key] = value

            whole_property = ""
            multiline_property_lines_count = 0

        return properties


class ConfigChangeStatus(enum.Enum):
    """Status of processing of configuration changes."""

    APPLIED = "APPLIED"  # All changes were applied
    CANNOT_APPLY = "CANNOT_APPLY"  # Cannot apply the changed property without restarting a microservice
    NOTHING_TO_APPLY = "NOTHING_TO_APPLY"  # There were no changes that are applicable to the current microservice


class Config:
    """Namespace for configuration options of all microservices."""

    def __init__(self, microservice_name, config_options, properties_loader=None):
        self.microservice_name = microservice_name
        self.config_options = config_options  # Configuration options which should be parsed
        self.properties_loader = properties_loader

        self.resolved_options = {}  # Configuration options with resolved values
        self.changed_option_names = set()  # Names of the configuration options that were changed during last reload
        self.applied_option_names = set()  # Names of the configuration options that were applied after last reload

    def __repr__(self):
        return f"{self.resolved_options!r}"

    def __eq__(self, other):
        if not isinstance(other, Config):
            return False

        return self.resolved_options == other.resolved_options

    @classmethod
    def from_all_sources(cls, microservice_name, config_options):
        """Load and extract the configuration options from all supported sources."""
        properties_loader = PropertiesLoader(microservice_name)
        flat_dictionary = properties_loader.load_all_sources()

        config = cls(microservice_name, config_options, properties_loader)
        config.from_dict(flat_dictionary)

        return config

    def from_dict(self, flat_dictionary, check_refreshable=False):
        """Extract the configuration options from already loaded dictionary."""
        SENTINEL = object()
        resolved_options = {}
        changed_option_names = set()
        not_refreshable_changed_option_names = set()
        dictionary = properties_to_nested_dict(flat_dictionary)
        microservice_property_name = self.microservice_name.replace("_", "-")

        for option_name, option in self.config_options.items():
            property_key = option["key"]
            try:
                new_value = json_path(dictionary, f"microservice.{microservice_property_name}.{property_key}")
            except ConfigurationError:
                new_value = json_path(dictionary, property_key)

            new_value = deserialize_property_value(new_value, option["deserializer"], self.microservice_name)
            resolved_options[option_name] = new_value

            old_value = self.resolved_options[option_name] if self.resolved_options else SENTINEL

            if old_value != new_value:
                changed_option_names.add(option_name)

                if not option["refreshable"]:
                    not_refreshable_changed_option_names.add(option_name)

        if check_refreshable and not_refreshable_changed_option_names:
            raise ConfigurationError(
                f"Following options are not refreshable without microservice restart: {not_refreshable_changed_option_names}"  # noqa: E501
            )

        self.resolved_options = resolved_options
        self.changed_option_names = changed_option_names
        self.applied_option_names = set()

        for config_option, new_value in resolved_options.items():
            setattr(self, config_option, new_value)

        self.decrypt_values()

    def decrypt_values(self):
        """Decrypt encrypted values based on loaded configuration."""
        keystores = {}

        for name, value in self.resolved_options.items():
            if not isinstance(value, str) or not value.startswith(ENCRYPTION_PREFIX):
                continue

            algorithm, key_alias, context, encrypted_value = parse_encrypted_property_info(value)

            if context not in keystores:
                keystore_config_prefix = context.lower()
                keystore_type = getattr(self, f"{keystore_config_prefix}_keystore_type")
                keystore_path = getattr(self, f"{keystore_config_prefix}_keystore")
                keystore_password = getattr(self, f"{keystore_config_prefix}_keystore_password")

                keystore_data = load_keystore_data(keystore_type, keystore_path)
                keystores[context] = create_symmetric_keystore(keystore_type, keystore_data, keystore_password)

            keystore = keystores[context]
            secret_key = keystore.secret_key(key_alias, secret_key_password=None)

            decrypted_value = decrypt_value(algorithm, secret_key, encrypted_value)

            setattr(self, name, decrypted_value)

    def reload(self, correlation_id: CorrelationId) -> bool:
        """Reload properties and update internal state."""
        # config_service_refresh_interval is affected by microservice's period
        # ConfigServiceClient is created before Config - interval cannot be injected in constructor
        new_properties = self.properties_loader.reload_config_service_properties(
            self.config_service_refresh_interval, correlation_id
        )
        if not new_properties:
            return False

        self.from_dict(new_properties, check_refreshable=True)

        return True

    def reload_processed(self, correlation_id: CorrelationId) -> None:
        """Notify Config Service that reload of configuration was processed with the resulted status."""
        if not self.changed_option_names:
            status = ConfigChangeStatus.NOTHING_TO_APPLY
        else:
            not_applied_option_names = set(self.changed_option_names).difference(self.applied_option_names)
            status = ConfigChangeStatus.CANNOT_APPLY if not_applied_option_names else ConfigChangeStatus.APPLIED

        self.properties_loader.reload_processed(status, correlation_id)

    def update_if_changed(self, option_name, update_function) -> bool:
        """Call update function if the property for corresponding option was changed."""
        if option_name not in self.changed_option_names:
            return False

        new_value = getattr(self, option_name)
        update_function(new_value)

        self.applied_option_names.add(option_name)

        return True


class ConfigOptionsBuilder:
    """Builds dictionary containing configuration options used to configure AI Core from any configuration source."""

    OTHER_SECTION = {"name": "Other", "order": 10000}

    def __init__(self):
        self.options = {}
        self.section = self.OTHER_SECTION

    def common_options(self, *args):
        """Add common options to existing options in this builder."""
        for option_name in args:
            for common_options_dict in COMMON_OPTIONS_MAPPING[option_name]:
                self.options.update(common_options_dict)

        return self

    def option(
        self,
        name,
        key,
        deserializer,
        description,
        default_value=None,
        refreshable=False,
        section=None,
        document_only=False,
    ):
        """Add new configuration option to existing options in this builder."""
        self.options[name] = {
            "key": key,
            "deserializer": deserializer,
            "description": description,
            "default_value": default_value,
            "refreshable": refreshable,
            "section": section or self.section,
            "document_only": document_only,  # Does not require default_value or value in etc/application.properties
        }

        return self

    def create_options(self, options_function):
        """Add new configuration options to existing options in this builder via supplied function."""
        options_function(self)
        return self

    def start_section(self, name: str, order: int):
        """Start new section for options used in application.properties.

        Note: The lower the order number is, the sooner the section will appear in the generated document.
        """
        self.section = {"name": name, "order": order}

        return self

    def end_section(self):
        """End section."""
        self.section = self.OTHER_SECTION

        return self


def parse_data_size(value: str) -> int:
    """Parse data size into bytes."""
    units = {"B": 0, "KB": 1, "MB": 2, "GB": 3, "TB": 4}

    match = re.match("([0-9]+) ?([a-zA-Z]{0,2})?$", value)
    if not match:
        raise ConfigurationError(f"Cannot parse data size {value!r}")

    parsed_value = int(match[1])

    parsed_unit = match[2]
    parsed_unit = parsed_unit.upper() or "KB"
    exponent = units[parsed_unit]

    return parsed_value * 1024 ** exponent


def server_options(
    config_options_builder: ConfigOptionsBuilder,
    microservice_name: str,
    module_name: str = None,
    grpc_host: str = "0.0.0.0",
    grpc_port: int = None,
    http_host: str = "0.0.0.0",
    http_port: int = None,
):
    """Generate options for setting up gRPC/HTTP server in microservice."""
    option_name = microservice_name.lower().replace(" ", "_")

    if module_name:
        module_name = module_name.lower().replace(" ", "_")
        property_name = f"{module_name}.{option_name}"
    else:
        property_name = option_name

    property_name = property_name.replace("_", "-")

    if grpc_port:
        config_options_builder.option(
            f"{option_name}_server_grpc_host",
            f"ataccama.one.aicore.{property_name}.grpc.server.listen-address",
            str,
            f"The network address to which the {microservice_name} gRPC server should bind.",
            default_value=grpc_host,
        )
        config_options_builder.option(
            f"{option_name}_server_grpc_port",
            f"ataccama.one.aicore.{property_name}.grpc.server.port",
            int,
            f"The port where the gRPC interface of the {microservice_name} microservice is running.",
            default_value=grpc_port,
        )
        config_options_builder.option(
            "server_grpc_max_message_size",
            "ataccama.server.grpc.properties.max-message-size",
            parse_data_size,
            "The maximum size of gRPC message. KB are used if no unit is specified.",
            default_value="1GB",
        )

    if http_port:
        config_options_builder.option(
            f"{option_name}_server_http_host",
            f"ataccama.one.aicore.{property_name}.http.server.listen-address",
            str,
            f"The network address to which the {microservice_name} HTTP server should bind.",
            default_value=http_host,
        )
        config_options_builder.option(
            f"{option_name}_server_http_port",
            f"ataccama.one.aicore.{property_name}.http.server.port",
            int,
            f"The HTTP port where the {microservice_name} microservice is running.",
            default_value=http_port,
        )


def connection_options(
    config_options_builder: ConfigOptionsBuilder,
    server_name: str,
    host: str = "localhost",
    grpc_port: int = None,
    http_port: int = None,
):
    """Generate options for setting up gRPC/HTTP connection to specified server."""
    option_name = server_name.lower().replace(" microservice", "").replace(" ", "_")
    property_name = option_name.replace("_", "-")

    config_options_builder.option(
        f"{option_name}_host",
        f"ataccama.client.connection.{property_name}.host",
        str,
        f"The IP address or the URL of the server where the {server_name} is running.",
        default_value=host,
    )

    if grpc_port:
        config_options_builder.option(
            f"{option_name}_grpc_port",
            f"ataccama.client.connection.{property_name}.grpc.port",
            int,
            f"The gRPC port of the server where the {server_name} is running.",
            default_value=grpc_port,
        )
        config_options_builder.option(
            "client_grpc_max_message_size",
            "ataccama.client.grpc.properties.max-message-size",
            parse_data_size,
            "The maximum size of gRPC message. KB are used if no unit is specified.",
            default_value="1GB",
        )

    if http_port:
        config_options_builder.option(
            f"{option_name}_http_port",
            f"ataccama.client.connection.{property_name}.http.port",
            int,
            f"The HTTP port of the server where the {server_name} is running.",
            default_value=http_port,
        )


PATHS_OPTIONS = (
    ConfigOptionsBuilder()
    .start_section("Configuration", 10)
    .option(
        "root_path",
        "ataccama.path.root",
        str,
        """The location of the root folder of the AI Core application. Some configuration paths are defined relatively
        to this path. The default value of this property can be overwritten only through environment variables,
        otherwise the change is ignored.""",
        default_value=".",
        document_only=True,  # This property can be configured only in ENV
    )
    .option(
        "lib_path",
        "ataccama.path.lib",
        str,
        """The location of the `lib` folder of the AI Core application. The default `application.properties` path is
        relative to this path. The default value of this property can be overwritten only through environment variables,
        otherwise the change is ignored.""",
        default_value="${ataccama.path.root}/lib",
        document_only=True,  # This property can be configured only in ENV
    )
    .option(
        "etc_path",
        "ataccama.path.etc",
        str,
        """The location of the etc folder of the AI Core application. The `etc/application.properties` path is relative
        to this path. The default value of this property can be overwritten only through environment variables and
        the default `application.properties` file. Otherwise, the change is ignored, which can lead to unexpected
        behavior.""",
        default_value="${ataccama.path.root}/etc",
    )
    .option(
        "log_path",
        "ataccama.path.log",
        str,
        "The location of the `log` folder of the AI Core application.",
        default_value="${ataccama.path.root}/log",
    )
    .option(
        "doc_path",
        "ataccama.path.doc",
        str,
        "The location of the `doc` folder of the AI Core application.",
        default_value="${ataccama.path.root}/doc",
    )
    .option(
        "tmp_path",
        "ataccama.path.tmp",
        str,
        "The location of the `tmp` folder of the AI Core application.",
        default_value="${ataccama.path.root}/temp",
    )
    .option(
        "migrations_path",
        "ataccama.path.migrations",
        str,
        "The location of the `migrations` folder of the AI Core application.",
        default_value="${ataccama.path.lib}/migrations",
    )
    .option(
        "artifact_version_txt_location",
        "ataccama.one.aicore.artifact-version-txt.location",
        str,
        "The location of the `artifact-version.txt` containing resolved version of AI Core application.",
        default_value="${ataccama.path.doc}/artifact-version.txt",
    )
    .option(
        "default_properties_location",
        "ataccama.one.aicore.config.location",
        str,
        """The location of the default `application.properties` file. The default value of this property can be
        overwritten only through environment variables, otherwise the change is ignored.""",
        default_value="${ataccama.path.lib}/application.properties",
        document_only=True,  # This property can be configured only in ENV
    )
    .option(
        "etc_properties_location",
        "ataccama.one.aicore.config.etc-location",
        str,
        """The path to the `etc/application.properties` file.""",
        default_value="${ataccama.path.etc}/application.properties",
    )
    .option(
        "manage_py_location",
        "ataccama.one.aicore.manage-py.location",
        str,
        """The path to the `manage.py` file, which is used to start microservices/processes of AI Core.""",
        default_value="${ataccama.path.lib}/manage.py",
    )
    .options
)

CONFIGURATION_SERVICE_OPTIONS = (
    ConfigOptionsBuilder()
    .start_section("Configuration", 10)
    .create_options(lambda builder: connection_options(builder, "Config Service", host="null", grpc_port="null"))
    .option(
        "config_service_refresh_interval",
        "ataccama.config-service.refresh-interval",
        int,
        """Defines the minimum amount of time after which the microservices send a new request to retrieve properties
        from the Configuration Service. Expressed in seconds.""",
        default_value=30,
    )
    .option(
        "config_service_heartbeat_interval",
        "ataccama.config-service.heartbeat-interval",
        int,
        """Defines the minimum amount of time after which the microservices signal to the Configuration Service that
        they are alive. Expressed in seconds.""",
        default_value=30,
    )
    .options
)

CONFIGURATION_SERVICE_DOCUMENT_OPTIONS = (
    ConfigOptionsBuilder()
    .start_section("Configuration", 10)
    .option(
        "config_service_override_local",
        "ataccama.config-service.override-local",
        bool,
        """Defines whether the properties from the Configuration Service override the properties located in
        `etc/application.properties`. If set to `false`, priority is given to local properties. The property needs to be
        set in the Configuration Service, otherwise it is ignored.""",
        default_value=False,
        document_only=True,  # This property should be configured only in Configuration Service
    )
    .options
)

HEALTH_CONFIG_OPTIONS = (
    ConfigOptionsBuilder()
    .start_section("Health", 15)
    .option(
        "heartbeat_timeout",
        "ataccama.one.aicore.heartbeat_timeout",
        float,
        """The timeout period during which the microservice and its subcomponents need to report as running, otherwise
        the whole microservice becomes unhealthy and its status changes to DOWN. The microservice also proactively shuts
        itself down when it registers such a situation.""",
        default_value="120",
    )
    .end_section()
    .options
)

LOGGING_CONFIG_OPTIONS = (
    ConfigOptionsBuilder()
    .start_section("Logging", 20)
    .option(
        "log_level",
        "root.level",
        str,
        "The minimum severity level starting from which logged messages are sent to the sink.",
        default_value="INFO",
    )
    .option(
        "log_stdout_plaintext",
        "ataccama.logging.plain-text-console-appender",
        bool,
        "Enables plain text console appender. Only one console appender can be enabled at a time.",
    )
    .option(
        "log_stdout_json",
        "ataccama.logging.json-console-appender",
        bool,
        "Enables JSON console appender. Only one console appender can be enabled at a time.",
    )
    .option(
        "log_file_plaintext",
        "ataccama.logging.plain-text-file-appender",
        bool,
        "Enables plain text file appender. Only one file appender can be enabled at a time.",
    )
    .option(
        "log_file_json",
        "ataccama.logging.json-file-appender",
        bool,
        "Enables JSON file appender. Only one file appender can be enabled at a time.",
    )
    .option(
        "log_rotation",
        "ataccama.one.aicore.logging.rotation",
        str,
        "Indicates how often the current log file should be closed and a new one started.",
        default_value="4 days",
    )
    .option(
        "log_filename",
        "ataccama.one.aicore.logging.filename",
        str,
        "The name of the file used by the file appender.",
        default_value="${ataccama.path.log}/aicore_{self.name}.log",
    )
    .option(
        "log_compression",
        "ataccama.one.aicore.logging.compression",
        str,
        "A compression or archive format to which log files should be converted when they are closed.",
        default_value="zip",
    )
    .end_section()
    # Used only for logging the CS URL when starting microservice
    .option("config_service_host", **CONFIGURATION_SERVICE_OPTIONS["config_service_host"])
    .option("config_service_grpc_port", **CONFIGURATION_SERVICE_OPTIONS["config_service_grpc_port"])
    .options
)


TLS_OUT_CONFIG_OPTIONS = (
    ConfigOptionsBuilder()
    .start_section("TLS - out", 81)
    .option(
        "client_tls_enabled",
        "ataccama.client.tls.enabled",
        bool,
        "Defines whether the gRPC and HTTP clients should use TLS when communicating with the servers.",
        default_value=False,  # False by default in java, too
    )
    .option(
        "client_tls_trust_all",
        "ataccama.client.tls.trust-all",
        bool,
        """Defines whether the gRPC and HTTP clients should verify the certificate of the server with which they
        communicate.""",
        default_value=False,
    )
    .option(
        "client_tls_truststore",
        "ataccama.client.tls.trust-store",
        str,
        """Points to the truststore with all the trusted certification authorities (CAs) used in gRPC and HTTP TLS
        communication. Used only when `tls.trust-all` is disabled.
        For example, `file:${ataccama.path.etc}/trust-store.pkcs12`.""",
        default_value="null",
    )
    .option(
        "client_tls_truststore_type",
        "ataccama.client.tls.trust-store-type",
        str,
        "The type of the truststore. Possible types are `PKCS12` and `JCEKS`.",
        default_value="null",
    )
    .option(
        "client_tls_truststore_password",
        "ataccama.client.tls.trust-store-password",
        str,
        "The password for the truststore. Used if the truststore is encrypted.",
        default_value="null",
    )
    .option(
        "client_tls_mtls",
        "ataccama.client.tls.mtls",
        bool,
        "Defines whether the gRPC and HTTP clients should use mTLS when communicating with the servers.",
        default_value=False,
    )
    .option(
        "client_tls_keystore",
        "ataccama.client.tls.key-store",
        str,
        """Points to the keystore containing private and public key certificates that are used by the gRPC and HTTP clients.
        For example, `file:${ataccama.path.etc}/key-store.pkcs12`.""",
        default_value="null",
    )
    .option(
        "client_tls_keystore_type",
        "ataccama.client.tls.key-store-type",
        str,
        "The type of the keystore. Possible types are `PKCS12`, `JKS`, and `JCEKS`.",
        default_value="null",
    )
    .option(
        "client_tls_keystore_password",
        "ataccama.client.tls.key-store-password",
        str,
        "The password for the keystore. Used if the keystore is encrypted.",
        default_value="null",
    )
    .option(
        "client_tls_private_key_alias",
        "ataccama.client.tls.key-alias",
        str,
        """The private key name specified in the provided keystore that is used for TLS.
        Does not work with `PKCS12` format. To avoid unexpected behavior, use `PKCS12` with only one private key.""",
        default_value="null",
    )
    .option(
        "client_tls_private_key_password",
        "ataccama.client.tls.key-password",
        str,
        """The password for the private key of the gRPC and HTTP clients. Used if the private key is encrypted.
        Does not work with `PKCS12` format. To avoid unexpected behavior, use `PKCS12` only with
        a non-encrypted private key.""",
        default_value="null",
    )
    .options
)


TLS_IN_CONFIG_OPTIONS = (
    ConfigOptionsBuilder()
    .start_section("TLS - in", 91)
    .option(
        "server_tls_enabled",
        "ataccama.server.tls.enabled",
        bool,
        "Defines whether the gRPC and HTTP servers should use TLS authentication.",
        default_value=False,  # False by default in java, too
    )
    .option(
        "server_tls_keystore",
        "ataccama.server.tls.key-store",
        str,
        """Points to the keystore containing private and public key certificates that are used by the gRPC and HTTP servers.
        For example, `file:${ataccama.path.etc}/key-store.pkcs12`.""",
        default_value="null",
    )
    .option(
        "server_tls_keystore_type",
        "ataccama.server.tls.key-store-type",
        str,
        "The type of the keystore. Possible types are `PKCS12`, `JKS`, and `JCEKS`.",
        default_value="null",
    )
    .option(
        "server_tls_keystore_password",
        "ataccama.server.tls.key-store-password",
        str,
        "The password for the keystore. Used if the keystore is encrypted.",
        default_value="null",
    )
    .option(
        "server_tls_private_key_alias",
        "ataccama.server.tls.key-alias",
        str,
        """The private key name specified in the provided keystore that is used for TLS.
        Does not work with `PKCS12` format. To avoid unexpected behavior, use `PKCS12` with only one private key.""",
        default_value="null",
    )
    .option(
        "server_tls_private_key_password",
        "ataccama.server.tls.key-password",
        str,
        """The password for the private key of the gRPC and HTTP servers. Used if the private key is encrypted."
        Does not work with `PKCS12` format. To avoid unexpected behavior, use `PKCS12` only with
        a non-encrypted private key.""",
        default_value="null",
    )
    .option(
        "server_tls_mtls",
        "ataccama.server.tls.mtls",
        lambda string: ServerTLSConfig.MTLSTypes[string],
        f"""Defines whether the gRPC and HTTP servers require clients to be authenticated.
        Possible values are `{ServerTLSConfig.MTLSTypes.NONE.name}`, `{ServerTLSConfig.MTLSTypes.OPTIONAL.name}`, `{ServerTLSConfig.MTLSTypes.REQUIRED.name}`.
        Can be set to `{ServerTLSConfig.MTLSTypes.REQUIRED.name}` only if `ataccama.server.tls.trust-cert-collection` is specified as well.""",  # noqa: E501
        default_value=ServerTLSConfig.MTLSTypes.OPTIONAL.name,
    )
    .option(
        "server_tls_truststore",
        "ataccama.server.tls.trust-store",
        str,
        """Points to the truststore with all the trusted certification authorities (CAs) used in the gRPC and HTTP
        TLS communication. For example, `file:${ataccama.path.etc}/trust-store.pkcs12`.""",
        default_value="null",
    )
    .option(
        "server_tls_truststore_type",
        "ataccama.server.tls.trust-store-type",
        str,
        "The type of the truststore. Possible types are `PKCS12` and `JCEKS`.",
        default_value="null",
    )
    .option(
        "server_tls_truststore_password",
        "ataccama.server.tls.trust-store-password",
        str,
        "The password for the truststore. Used if the truststore is encrypted.",
        default_value="null",
    )
    .option(
        "server_tls_allow_generate",
        "ataccama.server.tls.allow-generate",
        bool,
        """Defines whether the gRPC and HTTP servers should generate their self-signed certificate.
        The private key is saved to a location specified by `ataccama.server.tls.private-key`
        and the certificate to a location specified by `ataccama.server.tls.cert-chain`.""",
        default_value=False,
    )
    .option(
        "server_tls_generated_private_key",
        "ataccama.server.tls.private-key",
        str,
        """The path to the generated private key of the gRPC and HTTP servers.
        For example, `file:${ataccama.path.etc}/server.key`.""",
        default_value="null",
    )
    .option(
        "server_tls_generated_certificate_chain",
        "ataccama.server.tls.cert-chain",
        str,
        """The path to the generated certificate of the gRPC and HTTP servers.
        For example, `file:${ataccama.path.etc}/server.crt`.""",
        default_value="null",
    )
    .options
)


def specific_tls_config(options_prefix: str, global_config_options, tls_properties, microservice_name):
    """Create Config for TLS for specific server/client type - gRPC/HTTP."""
    tls_options = {}

    for option_name, option in global_config_options.items():
        tls_option_key = option["key"].replace(options_prefix, "")

        try:
            json_path(tls_properties, tls_option_key)
        except ConfigurationError:
            continue

        # Create server option only if the corresponding property was specified for given server type
        tls_option = {**option, "key": tls_option_key}
        tls_options[option_name] = tls_option

    # New TLS Config is created when reloading whole Config
    #   => TLS Config doesn't have to be reloadable - explicitly setting None value
    tls_config = Config(microservice_name, tls_options, properties_loader=None)
    tls_config.from_dict(tls_properties)

    return tls_config


def specific_tls_config_options(entity_type: str, config_type: TLSConfigType, global_config_options):
    """Create TLS connection config options for gRPC/HTTP server/client."""
    section = more_itertools.first(global_config_options.values())["section"]
    options_prefix = f"ataccama.{entity_type}.tls."

    return (
        ConfigOptionsBuilder()
        .start_section(section["name"], section["order"])
        .option(
            f"{entity_type}_{config_type.value}_tls",
            f"ataccama.{entity_type}.{config_type.value}.tls",
            lambda tls_properties, microservice_name: specific_tls_config(
                options_prefix, global_config_options, tls_properties, microservice_name
            ),
            f"""All {entity_type} TLS options can be specified directly for {config_type.name} {entity_type}. To set any TLS option for a {config_type.name} {entity_type},
            configure the same set of properties as for the global {entity_type} TLS configuration (properties with the `ataccama.{entity_type}.tls` prefix),
            but use the prefix `ataccama.{entity_type}.{config_type.value}.tls` instead.
            If an option is not specified for the {config_type.name} {entity_type}, global {entity_type} TLS options are applied.""",  # noqa: E501
            default_value="null",
        )
        .options
    )


def client_connection_tls_configs(connections_properties, microservice_name):
    """Create Config for TLS connection properties."""
    options_prefix = "ataccama.client.tls."
    global_config_options = TLS_OUT_CONFIG_OPTIONS

    connections_tls_configs = {}

    for connection_name, connection_properties in connections_properties.items():
        connection_tls_configs = connections_tls_configs[connection_name] = {}

        # ataccama.client.connection.<connection_name>.tls
        # ataccama.client.connection.<connection_name>.grpc.tls
        # ataccama.client.connection.<connection_name>.http.tls
        for tls_prefix, connection_tls_config_field in {
            "tls": "tls",
            "grpc.tls": "grpc_tls",
            "http.tls": "http_tls",
        }.items():
            try:
                connection_tls_properties = json_path(connection_properties, tls_prefix)
            except ConfigurationError:
                # Connection properties don't have to be specified at all
                connection_tls_config = Config(microservice_name, {})
            else:
                connection_tls_config = specific_tls_config(
                    options_prefix, global_config_options, connection_tls_properties, microservice_name
                )

            connection_tls_configs[connection_tls_config_field] = connection_tls_config

    return connections_tls_configs


TLS_OUT_GRPC_CONFIG_OPTIONS = specific_tls_config_options("client", TLSConfigType.gRPC, TLS_OUT_CONFIG_OPTIONS)
TLS_OUT_HTTP_CONFIG_OPTIONS = specific_tls_config_options("client", TLSConfigType.HTTP, TLS_OUT_CONFIG_OPTIONS)

TLS_OUT_CONNECTIONS_CONFIG_OPTIONS = (
    ConfigOptionsBuilder()
    .start_section("TLS - out", 81)
    .option(
        "client_connections",
        "ataccama.client.connection",
        lambda connections, microservice_name: client_connection_tls_configs(connections, microservice_name),
        """All client TLS options can be specified per connection. To set any TLS option for a specific client connection,
        configure the same set of properties as for the global client TLS configuration (properties with the `ataccama.client.tls` prefix).
        Depending on your setup, use one of the following prefixes:
        `ataccama.client.connection.<connection_name>.tls` for specifying TLS for connections using any communication protocol (gRPC and HTTP),
        `ataccama.client.connection.<connection_name>.grpc.tls` for specifying TLS for connections using the gRPC communication protocol,
        `ataccama.client.connection.<connection_name>.http.tls` for specifying TLS for connections using the HTTP communication protocol.
        If an option is not specified for the given client connection, global client TLS options are applied.""",  # noqa: E501
        default_value="null",
    )
    .options
)

TLS_IN_GRPC_CONFIG_OPTIONS = specific_tls_config_options("server", TLSConfigType.gRPC, TLS_IN_CONFIG_OPTIONS)
TLS_IN_HTTP_CONFIG_OPTIONS = specific_tls_config_options("server", TLSConfigType.HTTP, TLS_IN_CONFIG_OPTIONS)


SECURITY_HEADERS_OPTIONS = (
    ConfigOptionsBuilder()
    .start_section("Security headers", 92)
    .option(
        "headers_hsts",
        "ataccama.one.security.header.Strict-Transport-Security",
        str,
        """The value of the HTTP Strict-Transport-Security (HSTS) response header. Used only when HTTPS is enabled.
        Informs browsers that the resource should only be accessed using the HTTPS protocol.""",
        # Value recommended by OWASP (Open Web Application Security Project)
        default_value="max-age=31536000; includeSubDomains; preload",
    )
    .options
)

AUTH_OUT_CONFIG_OPTIONS = (
    ConfigOptionsBuilder()
    .start_section("Authentication - out", 80)
    .option(
        "jwk",
        "ataccama.authentication.internal.jwt.generator.key",
        str,
        "The private key of the AI Core module used to generate tokens for internal JWT authentication.",
    )
    .option(
        "jwt_expiration",
        "ataccama.authentication.internal.jwt.generator.token-expiration",
        int,
        """Defines the amount of time after which the token generated by the internal JWT generator expires.
        Expressed in seconds.""",
        default_value=900,
    )
    .end_section()
    .options
)


def platform_deployments(deployments):
    """Collect all necessary deployment options with jwt keys from all deployments."""
    parsed_deployments = {}

    for deployment_name, deployment in deployments.items():
        parsed_jwt_keys = {}
        deployment_jwt_keys = json_path(deployment, "security.jwt-keys")

        for key_name, key in deployment_jwt_keys.items():
            try:
                is_revoked = json_path(key, "is-revoked")
            except ConfigurationError:
                is_revoked = False

            parsed_jwt_keys[key_name] = {
                **key,
                "is_revoked": deserialize_property_value(is_revoked, bool, microservice_name=None),
            }

        try:
            roles = json_path(deployment, "security.roles")
        except ConfigurationError:
            roles = []

        parsed_deployments[deployment_name] = {
            "module": deployment.get("module"),
            "uri": deployment.get("uri"),
            "roles": deserialize_property_value(roles, list, microservice_name=None),
            "jwt_keys": parsed_jwt_keys,
        }

    return parsed_deployments


def http_acl_endpoints(endpoints):
    """Parse ACL endpoints properties."""
    parsed_endpoints = {}

    for pattern_name, pattern_value in endpoints.items():
        endpoint_filter = json_path(pattern_value, "endpoint-filter")
        allowed_roles = json_path(pattern_value, "allowed-roles")

        parsed_endpoints[pattern_name] = {
            "endpoint_paths": deserialize_property_value(endpoint_filter, list, microservice_name=None),
            "allowed_roles": deserialize_property_value(allowed_roles, list, microservice_name=None),
        }

    return parsed_endpoints


def db_connection_string(connection_info) -> str:
    """Parse Db connection string."""
    dialect = json_path(connection_info, "dialect")
    if dialect not in SUPPORTED_DIALECTS:
        raise ConfigurationError(
            f"Dialect '{dialect}' is not supported. Supported dialects are: {', '.join(SUPPORTED_DIALECTS)}"
        )

    host = json_path(connection_info, "host")
    username = json_path(connection_info, "username")
    password = json_path(connection_info, "password")

    return f"{dialect}://{username}:{password}@{host}"


AUTH_IN_CONFIG_OPTIONS = (
    ConfigOptionsBuilder()
    .start_section("Authentication - in", 90)
    .option(
        "platform_deployments",
        "ataccama.one.platform.deployments",
        platform_deployments,
        """Deployment settings (with public JWT keys) for other modules communicating with AI Core.
        Required fields for deployment are: `module`, `uri`, `roles`. These fields are used for creation of
        service identity during authentication.
        Required fields for JWT key are: `fingerprint`, `content`. Optional `is-revoked` is used for revoking
        the corresponding JWT key (e.g. via Config Service) if the key was compromised.
        Example settings for MMM:
        `ataccama.one.platform.deployments.mmm-be.module=<value>`,
        `ataccama.one.platform.deployments.mmm-be.uri=<value>`,
        `ataccama.one.platform.deployments.mmm-be.security.roles=<value>`,
        `ataccama.one.platform.deployments.mmm-be.security.jwt-keys.mmm-key.fingerprint=<value>`,
        `ataccama.one.platform.deployments.mmm-be.security.jwt-keys.mmm-key.content=<value>`,
        `ataccama.one.platform.deployments.mmm-be.security.jwt-keys.mmm-key.is-revoked=false`.""",
        default_value="null",
        refreshable=True,
    )
    .option(
        "keycloak_server_url",
        "ataccama.authentication.keycloak.server-url",
        str,
        "The URL of the server where Keycloak is running.",
    )
    .option(
        "keycloak_realm",
        "ataccama.authentication.keycloak.realm",
        str,
        "The name of the Keycloak realm. Used when requesting an access token during authorization.",
    )
    .option(
        "keycloak_token_client_id",
        "ataccama.authentication.keycloak.token.client-id",
        str,
        "The client token identifier of the AI Core module. Used when requesting an access token during authorization.",
    )
    .option(
        "keycloak_token_secret",
        "ataccama.authentication.keycloak.token.secret",
        str,
        "The secret key of the AI Core client. Used when requesting an access token during authorization.",
    )
    .option(
        "keycloak_token_issuer",
        "ataccama.authentication.keycloak.token.issuer",
        str,
        """The issuer of the Keycloak token. Used to validate the access (bearer) token obtained from Keycloak.
        If the value is `null`, the issuer is not verified.""",
        default_value=""
        "${ataccama.authentication.keycloak.server-url}/realms/${ataccama.authentication.keycloak.realm}",
    )
    .option(
        "keycloak_token_audience",
        "ataccama.authentication.keycloak.token.audience",
        str,
        """The expected recipients of the Keycloak token. Used to validate the access (bearer) token obtained from
        Keycloak. If the value is `null`, the audience is not verified.""",
        default_value="null",
    )
    .option(
        "keycloak_token_expected_algorithm",
        "ataccama.authentication.keycloak.token.expected-algorithm",
        str,
        "The expected algorithm that was used to sign the access (bearer) token obtained from Keycloak.",
        default_value="RS256",
    )
    .option(
        "keycloak_token_key_cache_ttl",
        "ataccama.authentication.keycloak.token.key-cache-ttl",
        int,
        """Defines how long the public certificates from Keycloak are cached on the AI Core side.
        If this time is exceeded, new certificates are fetched from Keycloak before the AI Core makes an attempt to authenticate.
        If this time is not exceeded, but the public certificate for the key parsed from the authentication attempt was not found in the cache,
        new certificates are fetched from Keycloak and authentication is attempted again.
        Expressed in seconds.""",  # noqa: E501
        default_value=300,
    )
    .option(
        "keycloak_token_key_cache_min_time_between_requests",
        "ataccama.authentication.keycloak.token.key-cache-min-time-between-request",
        int,
        """Defines the minimum amount of time between two consecutive requests for Keycloak certificates during which
        Keycloak is not asked for new certificates. This acts as a prevention against DDoS attacks with an unknown key.
        Expressed in seconds.""",
        default_value=5,
    )
    .option(
        "http_auth_basic",
        "ataccama.authentication.http.basic.enable",
        bool,
        """Enables basic authentication on the HTTP server. If enabled, Keycloak becomes a mandatory dependency
        - it needs to be running before the AI Core starts.""",
        default_value=True,
    )
    .option(
        "http_auth_basic_filter",
        "ataccama.authentication.http.basic.endpoint-filter",
        str,
        """Ant-style patterns that filter which HTTP endpoints have basic authentication enabled.
        Individual patterns are separated by `;`.""",
        default_value="/**",
    )
    .option(
        "http_auth_bearer",
        "ataccama.authentication.http.bearer.enable",
        bool,
        """Enables bearer authentication on the HTTP server. If enabled, Keycloak becomes a mandatory dependency
        - it needs to be running before the AI Core starts.""",
        default_value=True,
    )
    .option(
        "http_auth_bearer_filter",
        "ataccama.authentication.http.bearer.endpoint-filter",
        str,
        """Ant-style patterns that filter which HTTP endpoints have bearer authentication enabled.
        Individual patterns are separated by `;`.""",
        default_value="/**",
    )
    .option(
        "http_auth_internal_jwt",
        "ataccama.authentication.http.internal.jwt.enable",
        bool,
        "Enables internal JWT token authentication on the HTTP server.",
        default_value=True,
    )
    .option(
        "http_auth_internal_jwt_filter",
        "ataccama.authentication.http.internal.jwt.endpoint-filter",
        str,
        """Ant-style patterns that filter which HTTP endpoints have internal JWT authentication enabled.
        Individual patterns are separated by `;`.""",
        default_value="/**",
    )
    .option(
        "grpc_auth_basic",
        "ataccama.authentication.grpc.basic.enable",
        bool,
        """Enables basic authentication on the gRPC server. If enabled, Keycloak becomes a mandatory dependency
        - it needs to be running before the AI Core starts.""",
        default_value=True,
    )
    .option(
        "grpc_auth_bearer",
        "ataccama.authentication.grpc.bearer.enable",
        bool,
        """Enables bearer authentication on the gRPC server. If enabled, Keycloak becomes a mandatory dependency
        - it needs to be running before the AI Core starts.""",
        default_value=True,
    )
    .option(
        "grpc_auth_internal_jwt",
        "ataccama.authentication.grpc.internal.jwt.enable",
        bool,
        "Enables internal JWT token authentication on the gRPC server.",
        default_value=True,
    )
    .option(
        "http_acl_endpoints",
        "ataccama.authentication.http.acl.endpoints",
        http_acl_endpoints,
        f"""Used for securing HTTP endpoints based on user/module roles. The role comparison is case-insensitive.
        Example for allowing only `ADMIN` roles to access prometheus endpoint:
        `ataccama.authentication.http.acl.endpoints.prometheus-endpoint.endpoint-filter=["{Actuator.METRICS_PATH}"]`,
        `ataccama.authentication.http.acl.endpoints.prometheus-endpoint.allowed-roles=["ADMIN"].""",
        default_value="null",
    )
    .option(
        "http_acl_default_allow",
        "ataccama.authentication.http.acl.default-allow",
        bool,
        """If set to `false`, nobody is allowed to access any HTTP endpoint. To explicitly allow access to some endpoint,
        access based on allowed roles can be configured via `ataccama.authentication.http.acl.endpoints`.""",
        default_value=True,
    )
    .option(
        "impersonation_role",
        "ataccama.authentication.internal.jwt.impersonation-role",
        str,
        "Role used for validating that service that sends request to AI Core can impersonate a user.",
        default_value="IMPERSONATION",
    )
    .option(
        "public_endpoint_restriction_filter",
        "ataccama.authentication.http.public-endpoint-restriction-filter",
        str,
        """Ant-style patterns that filter which public HTTP endpoints should be protected. These endpoint become
        no longer public and authentication is required. Individual patterns are separated by `;`.""",
        default_value="null",
    )
    .end_section()
    .options
)

RETRYING_CONFIG_OPTIONS = (
    ConfigOptionsBuilder()
    .start_section("Retrying", 30)
    .option(
        "retrying_wait_type",
        "ataccama.one.aicore.retrying.wait.type",
        str,
        """Controls retrying of gRPC and graphQL communication attempts. The property determines which approach is used
        when waiting. For more information about how waiting periods between unsuccessful attempts are managed, see the
        [Tenacity API Reference](https://tenacity.readthedocs.io/en/latest/api.html), Wait Functions section.""",
        default_value="wait_exponential",
    )
    .option(
        "retrying_wait_kwargs",
        "ataccama.one.aicore.retrying.wait.kwargs",
        dict,
        """Controls retrying of gRPC and graphQL communication attempts. The property is used to calculate the duration of
        waiting periods between retries. For more information about how waiting periods between unsuccessful attempts
        are managed, see the [Tenacity API Reference](https://tenacity.readthedocs.io/en/latest/api.html),
        Wait Functions section.""",
        default_value='{"multiplier": 0.16, "exp_base": 2}',
    )
    .option(
        "retrying_stop_type",
        "ataccama.one.aicore.retrying.stop.type",
        str,
        """Controls retrying of gRPC and graphQL communication attempts. The property determines which approach is used to
        stop retrying. For more information, see the
        [Tenacity API Reference](https://tenacity.readthedocs.io/en/latest/api.html), Stop Functions section.""",
        default_value="stop_after_attempt",
    )
    .option(
        "retrying_stop_kwargs",
        "ataccama.one.aicore.retrying.stop.kwargs",
        dict,
        """Controls retrying of gRPC and graphQL communication attempts. The property determines when retrying stops.
        By default, retrying stops after 6 attempts in total, out of which 5 are retries.""",
        default_value='{"max_attempt_number": 6}',
    )
    .end_section()
    .options
)

READINESS_WAIT_CONFIG_OPTIONS = (
    ConfigOptionsBuilder()
    .start_section("Wait for readiness on start", 40)
    .option(
        "onstart_retrying_wait_type",
        "ataccama.one.aicore.onstart.retrying.wait.type",
        str,
        """Defines the behavior of the microservice while it waits on a dependency before starting. Currently, the
        microservice either waits to receive information about the health of the dependency or the database readiness
        (typically, this means waiting for the database to start and for MMM to create the tables needed). The property
        defines how waiting periods are managed between unsuccessful attempts to verify the readiness of the dependency.
        For a list of other available wait types, see the
        [Tenacity API Reference](https://tenacity.readthedocs.io/en/latest/api.html), Wait Functions section.""",
        default_value="wait_fixed",
    )
    .option(
        "onstart_retrying_wait_kwargs",
        "ataccama.one.aicore.onstart.retrying.wait.kwargs",
        dict,
        """Defines the behavior of the microservice while it waits on a dependency before starting. Keyword arguments
        (kwargs) are the arguments used to construct an instance of the specified wait type. In this case, the keyword
        argument sets the duration of waiting intervals.""",
        default_value='{"wait": 2.5}',
    )
    .option(
        "onstart_health_response_timeout",
        "ataccama.one.aicore.onstart.health.response-timeout",
        float,
        """Sets for how many seconds the microservice waits after requesting health information about its dependencies,
        for example, when the Recommender waits for the Neighbors or the Autocomplete waits for MMM.
        For more information, see the
        [Requests Developer Interface Documentation](https://requests.readthedocs.io/en/master/api/),
        section about the `timeout` parameter.""",
        default_value=5,
    )
    .end_section()
    .options
)

DB_CONFIG_OPTIONS = (
    ConfigOptionsBuilder()
    .start_section("DB", 50)
    .option(
        "connection_string",
        "ataccama.one.aicore.database.connection",
        db_connection_string,
        f"""Used to define the AI Core database connection configuration.
        Supported dialects: {', '.join(SUPPORTED_DIALECTS)}.
        Additional properties include the following:
        `ataccama.one.aicore.database.connection.dialect=postgres`
        `ataccama.one.aicore.database.connection.host=localhost:5432/ai`
        `ataccama.one.aicore.database.connection.username=one`
        `ataccama.one.aicore.database.connection.password=one`""",
        default_value="null",
    )
    .option(
        "db_poll_period",
        "ataccama.one.aicore.database.poll-period",
        int,
        """Defines how often the database is polled for changes. Used by the Term Suggestions microservice. Expressed in
        seconds.""",
        default_value=1,
    )
    .option(
        "engine_kwargs",
        "ataccama.one.aicore.database.engine-kwargs",
        dict,
        """Sets the SQLAlchemy engine options, such as the maximum length of identifiers used in the database. For more
        information, see the [Engine Configuration](https://docs.sqlalchemy.org/en/13/core/engines.html), section Engine
        Creation API, Parameters.""",
        default_value='{"max_identifier_length": 128}',
    )
    .end_section()
    .options
)

MMM_CONFIG_OPTIONS = (
    ConfigOptionsBuilder()
    .start_section("MMM", 70)
    .create_options(lambda builder: connection_options(builder, server_name="MMM", grpc_port=8521, http_port=8021))
    .end_section()
    .start_section("GraphQL", 60)
    .option(
        "connect_timeout",
        "ataccama.one.aicore.http.connect-timeout",
        int,
        """Defines after which amount of time the HTTP call is ended if the socket does not receive any bytes.
        Expressed in seconds.""",
        default_value="5",
    )
    .end_section()
    .options
)


PARALLELISM_CONFIG_OPTIONS = (
    ConfigOptionsBuilder()
    .start_section("Parallelism", 80)
    .option(
        "jobs",
        "ataccama.one.aicore.parallelism.jobs",
        int,
        """The number of parallel threads or processes spawned by high-level machine learning algorithms with explicit
        job management. If the value is set to `0`, all CPU cores run without hyper-threads.
        If the value is not set (`null`), the library default settings are applied.
        Use this option together with `ataccama.one.aicore.parallelism.omp`.
        For more information, see the AI Core Sizing Guidelines.""",
        default_value="1",
    )
    .option(
        "omp",
        "ataccama.one.aicore.parallelism.omp",
        int,
        """The number of parallel threads spawned by low-level calculations that are used by high-level machine learning algorithms.
        If the value is set to `0`, all CPU cores run without hyper-threads.
        If the value is not set (`null`), the library default settings are applied.
        The property relies on the static OpenBLAS API and OpenMP API, which have a lower overhead than the dynamic API
        used by the property `ataccama.one.aicore.parallelism.threads`.
        When this property is set, the OpenBLAS library gives it lower priority compared to `ataccama.one.aicore.parallelism.blas`.
        Several low-level libraries other than OpenBLAS and LAPACK, as well as libraries that use OpenMP, respect this
        option as well. Use this option together with `ataccama.one.aicore.parallelism.jobs`.
        For more information, see the AI Core Sizing Guidelines.""",  # noqa: E501
        default_value="1",
    )
    .option(
        "threads",
        "ataccama.one.aicore.parallelism.threads",
        int,
        """An alternative way of setting the number of parallel threads spawned by low-level calculations that are
        used by machine learning algorithms.
        If the value is set to `0`, all CPU cores run without hyper-threads.
        If the value is not set (`null`), the dynamic API is not used. Relies on the dynamic OpenBLAS API, which has
        a higher overhead than the static API used by `ataccama.one.aicore.parallelism.omp`.
        When this property is set, OpenBLAS gives it higher priority compared to
        `ataccama.one.aicore.parallelism.omp` and `ataccama.one.aicore.parallelism.blas`.
        The dynamic API is intended only for exceptional cases and should not be used otherwise.""",  # noqa: E501
        default_value="null",
    )
    .option(
        "blas",
        "ataccama.one.aicore.parallelism.blas",
        int,
        """An alternative way of overriding the number of parallel threads spawned by low-level calculations that are
        used by machine learning algorithms.
        If the value is set to `0`, all CPU cores run without hyper-threads.
        If the value is not set (`null`), other properties are not overridden.
        Relies on the static OpenBLAS API and might be ignored depending on the compilation options for the OpenBLAS library.
        When this property is set, OpenBLAS gives it higher priority compared to `ataccama.one.aicore.parallelism.omp`.
        This is intended only for exceptional cases and should not be used otherwise.""",  # noqa: E501
        default_value="null",
    )
    .end_section()
    .options
)


def encryption_options(context):
    """Create encryption config options for given context."""
    return (
        ConfigOptionsBuilder()
        .start_section("Encryption", 90)
        .option(
            f"{context}_keystore",
            f"{context}.encryption.key-store",
            str,
            """Points to the keystore containing private and public key certificates that are used by the gRPC and HTTP clients.
            For example, `file:${ataccama.path.etc}/key-store.pkcs12`.""",
            default_value="null",
        )
        .option(
            f"{context}_keystore_type",
            f"{context}.encryption.key-store-type",
            str,
            "The type of the keystore. Possible types are `PKCS12`, `JKS`, and `JCEKS`.",
            default_value="null",
        )
        .option(
            f"{context}_keystore_password",
            f"{context}.encryption.key-store-password",
            str,
            "The password for the keystore. Used if the keystore is encrypted.",
            default_value="null",
        )
        .options
    )


ENCRYPTION_OPTIONS = {}

for context in SUPPORTED_CONTEXTS.values():
    ENCRYPTION_OPTIONS.update(encryption_options(context))


COMMON_OPTIONS_MAPPING = {
    "paths": [PATHS_OPTIONS],
    "cs": [CONFIGURATION_SERVICE_OPTIONS],
    "health": [HEALTH_CONFIG_OPTIONS],
    "logging": [LOGGING_CONFIG_OPTIONS],
    "auth_in": [AUTH_IN_CONFIG_OPTIONS],
    "auth_out": [AUTH_OUT_CONFIG_OPTIONS],
    "tls_out": [
        TLS_OUT_CONFIG_OPTIONS,
        TLS_OUT_GRPC_CONFIG_OPTIONS,
        TLS_OUT_HTTP_CONFIG_OPTIONS,
        TLS_OUT_CONNECTIONS_CONFIG_OPTIONS,
    ],
    "tls_in": [TLS_IN_CONFIG_OPTIONS, TLS_IN_GRPC_CONFIG_OPTIONS, TLS_IN_HTTP_CONFIG_OPTIONS, SECURITY_HEADERS_OPTIONS],
    "retrying": [RETRYING_CONFIG_OPTIONS],
    "readiness_wait": [READINESS_WAIT_CONFIG_OPTIONS],
    "db": [DB_CONFIG_OPTIONS],
    "mmm": [MMM_CONFIG_OPTIONS],
    "parallelism": [PARALLELISM_CONFIG_OPTIONS],
    "encryption": [ENCRYPTION_OPTIONS],
    "auth": [],
    "microservice_commons": [],
}  # Manually add new sections to each microservice (including Supervisor) which needs it

for options_group in ["auth_in", "auth_out", "tls_in", "tls_out"]:
    COMMON_OPTIONS_MAPPING["auth"].extend(COMMON_OPTIONS_MAPPING[options_group])

for options_group in [
    "paths",
    "cs",
    "health",
    "logging",
    "auth",
    "retrying",
    "readiness_wait",
    "parallelism",
    "encryption",
]:
    COMMON_OPTIONS_MAPPING["microservice_commons"].extend(COMMON_OPTIONS_MAPPING[options_group])
