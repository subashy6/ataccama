"""Common commands shared by all AI Core modules."""

from __future__ import annotations

from typing import TYPE_CHECKING

import google.protobuf.empty_pb2
import google.protobuf.json_format

import aicore.common.proto.ClientService_pb2 as cs_client_proto
import aicore.common.proto.common_pb2 as common_proto
import aicore.common.proto.PropertyService_pb2 as cs_property_proto

from aicore.common.exceptions import AICoreException
from aicore.common.registry import LogId


if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from typing import ClassVar, Optional

    from google.protobuf.message import Message

    from aicore.common.auth import Identity
    from aicore.common.grpc import Request, Response
    from aicore.common.microservice import Microservice
    from aicore.common.types import CorrelationId


class CommandError(AICoreException):
    """A handled error raised during processing of a command (e.g. invalid arguments in current microservice state)."""

    def __init__(self, reason: str, message: str, **kwargs):
        self.reason = reason  # Agreed upon code for a subtype of the error
        self.message = message  # Description of the error in human readable format
        self.kwargs = kwargs  # Context in which the error occurred

    @property
    def context(self) -> dict[str, str]:
        """Return context of the error as a dictionary with string keys and values."""
        details = {"reason": self.reason, "message": self.message}
        details.update({key: str(value) for key, value in self.kwargs.items()})
        return details


class Command:
    """Implementation of a gRPC method (both client and server side with de/serialization)."""

    # Things to be aware of:
    #    - google.protobuf.Timestamp.ToDateTime() will return a naive datetime objects that needs to be manually
    #    transformed into a timezone-aware one -> naive_datetime.replace(tzinfo=datetime.timezone.utc)

    # To be overridden by child classes
    service: ClassVar[str]  # Name of gRPC service in format "ataccama.aicore.<module>.<service>"
    method: ClassVar[str]  # Name of gRPC method
    method_type: ClassVar[str] = "unary_unary"  # Type of gRPC call: "<request>_<response>" where <> is "unary"/"stream"
    request_class: ClassVar[type[Message]]  # protobuf message class for necessary data for command instantiation
    response_class: ClassVar[type[Message]]  # protobuf message class for command's results
    # Mark a command as an exception for not logging messages by setting this to `False`. Default value set to `True`.
    enable_logging: bool = True

    __slots__ = ()

    def __repr__(self):
        return f"{type(self).__name__}()"

    @classmethod
    def method_id(cls) -> str:
        """Return the full identifier of the gRPC method this command implements."""
        return f"/{cls.service}/{cls.method}"

    # gRPC client (re-implement if the client side of the rpc is handled in AI Core)

    def serialize_for_server(self) -> Request:
        """Create a gRPC request (protobuf message or iterator of them) based on the command's state."""
        return self.request_class()

    def deserialize_from_server(self, response: Response) -> None:
        """Set command's state based on the gRPC response (protobuf message or iterator of them)."""
        pass

    # gRPC server (re-implement if the server side of the rpc is handled in AI Core)

    @classmethod
    def deserialize_from_client(cls, request: Request) -> Command:
        """Create the command from given gRPC request (protobuf message or iterator of them)."""
        return cls()

    def process(self, microservice, correlation_id: CorrelationId, identity: Optional[Identity] = None) -> None:
        """Perform the command (in case it should provide some results, compute them and store them in the command)."""
        pass

    def serialize_for_client(self) -> Response:
        """Create a gRPC response (protobuf message or iterator of them) based on the command's results."""
        return self.response_class()


class ShutdownServiceCommand(Command):
    """Trigger graceful shutdown of the microservice."""

    service = "ataccama.aicore.common.CommonMessages"
    method = "ShutdownService"
    request_class = common_proto.ShutdownServiceRequest
    response_class = common_proto.ShutdownServiceResponse

    def process(
        self, microservice: Microservice, correlation_id: CorrelationId, identity: Optional[Identity] = None
    ) -> None:
        """Trigger graceful shutdown of the microservice."""
        microservice.logger.info(
            "*** Service {name!r} is shutting down as requested via gRPC ***",
            name=microservice.name,
            message_id=LogId.microservice_shutdown_requested_via_grpc,
            correlation_id=correlation_id,
            identity=identity,
        )
        microservice.shutdown()


class ConfigServiceHeartbeatCommand(Command):
    """Ping Config Service with heartbeat."""

    service = "com.ataccama.one.onecfg.server.grpc.ClientService"
    method = "heartbeat"
    request_class = cs_client_proto.HeartbeatRequest
    response_class = google.protobuf.empty_pb2.Empty
    __slots__ = "replica_identifier"

    def __init__(self, replica_identifier):
        self.replica_identifier = replica_identifier

    def serialize_for_server(self) -> cs_client_proto.HeartbeatRequest:
        """Create a gRPC request based on the command's state."""
        request = self.request_class()
        request.replicaIdentifier = self.replica_identifier

        return request


class GetLatestPropertiesCommand(Command):
    """Ask Config Service for properties."""

    service = "com.ataccama.one.onecfg.server.grpc.PropertyService"
    method = "getProperties"
    request_class = google.protobuf.empty_pb2.Empty
    response_class = cs_property_proto.GetPropertiesResponse
    __slots__ = ("properties", "version")

    def __init__(self):
        self.properties = {}
        self.version = None

    def deserialize_from_server(self, response: cs_property_proto.GetPropertiesResponse) -> None:
        """Create dict of properties."""
        self.properties = {single_property.name: single_property.value for single_property in response.properties}
        self.version = response.version


class GetLatestPropertiesVersionCommand(Command):
    """Get latest version of Config Service properties."""

    service = "com.ataccama.one.onecfg.server.grpc.PropertyService"
    method = "getLatestVersion"
    request_class = google.protobuf.empty_pb2.Empty
    response_class = cs_property_proto.GetLatestVersionResponse
    __slots__ = "version"

    def __init__(self):
        self.version = None

    def deserialize_from_server(self, response: cs_property_proto.GetLatestVersionResponse) -> None:
        """Get latest version of Config Service properties."""
        self.version = response.version


class PropertiesAppliedCommand(Command):
    """Let Config Service know that properties were applied."""

    service = "com.ataccama.one.onecfg.server.grpc.PropertyService"
    method = "applied"
    request_class = cs_property_proto.PropertiesAppliedRequest
    response_class = google.protobuf.empty_pb2.Empty
    __slots__ = ("replica_identifier", "version")

    def __init__(self, replica_identifier, version):
        self.replica_identifier = replica_identifier
        self.version = version

    def serialize_for_server(self) -> cs_property_proto.PropertiesAppliedRequest:
        """Create a gRPC request based on the command's state."""
        request = self.request_class()
        request.replicaIdentifier = self.replica_identifier
        request.version = self.version

        return request


class PropertiesNothingToApplyCommand(Command):
    """Let Config Service know that there was nothing to apply."""

    service = "com.ataccama.one.onecfg.server.grpc.PropertyService"
    method = "nothingToApply"
    request_class = cs_property_proto.NothingToApplyRequest
    response_class = google.protobuf.empty_pb2.Empty
    __slots__ = "replica_identifier"

    def __init__(self, replica_identifier):
        self.replica_identifier = replica_identifier

    def serialize_for_server(self) -> cs_property_proto.NothingToApplyRequest:
        """Create a gRPC request based on the command's state."""
        request = self.request_class()
        request.replicaIdentifier = self.replica_identifier

        return request


class TestCommand(Command):
    """Bidirectional streaming echo test of the gRPC communication.

    Each input string from the inputs is "echoed" back with "echo: " prefix in the outputs.
    Generators are used so that the whole [client => server => client] chain processes the messages one by one.
    """

    service = "ataccama.aicore.common.TestMessages"
    method = "Test"
    method_type = "stream_stream"
    request_class = common_proto.TestRequest
    response_class = common_proto.TestResponse
    __slots__ = ("inputs", "echos")

    def __init__(self, inputs: Iterable[str]):
        # both can be read only once (since they are Iterables)
        self.inputs = inputs
        self.echos: Iterable[str] = ()

    def __repr__(self):
        return f"TestCommand({self.inputs})"

    # client

    def serialize_for_server(self) -> Iterator[common_proto.TestRequest]:
        """Create a gRPC request (iterator of protobuf messages - one for each string in the inputs)."""
        for data in self.inputs:
            yield self.request_class(data=data)

    def deserialize_from_server(self, response: Iterator[common_proto.TestResponse]) -> None:
        """Get the echoed strings back from the gRPC response (iterator of protobuf messages)."""
        self.echos = (msg.echoed_data for msg in response)

    # server

    @classmethod
    def deserialize_from_client(cls, request: Iterator[common_proto.TestRequest]) -> TestCommand:
        """Create the command from given gRPC request (iterator of protobuf messages)."""
        return cls(inputs=(request.data for request in request))

    def process(
        self, _microservice: Microservice, _correlation_id: CorrelationId, _identity: Optional[Identity] = None
    ) -> None:
        """Compute command's echos - prepend each input with 'echo: '."""
        self.echos = (f"echo: {data}" for data in self.inputs)

    def serialize_for_client(self) -> Iterator[common_proto.TestResponse]:
        """Create a gRPC response (iterator fo protobuf messages - one for each echoed string)."""
        for echo in self.echos:
            yield self.response_class(echoed_data=echo)
