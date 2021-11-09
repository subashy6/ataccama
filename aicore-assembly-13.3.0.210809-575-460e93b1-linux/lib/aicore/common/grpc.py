"""Generic gRPC server and client wrappers using JSON messages."""

from __future__ import annotations

import atexit
import concurrent.futures
import inspect
import json
import time
import traceback

from typing import TYPE_CHECKING

import grpc
import grpc._server
import tenacity

from aicore.common.auth import AuthenticationError, create_internal_jwt_header, get_authorization_header
from aicore.common.command import CommandError
from aicore.common.constants import CORRELATION_ID_HEADER, ENCODING, RESPONSIVENESS_PERIOD
from aicore.common.exceptions import AICoreException
from aicore.common.logging import WARNING_COLOR
from aicore.common.registry import GRPCClientMetric, GRPCServerMetric, LogId
from aicore.common.resource import BackgroundThread, Resource, RuntimeState
from aicore.common.retry import never_retrying
from aicore.common.tls import CertificatesLoader, ServerTLSConfig


if TYPE_CHECKING:
    from typing import Any, Optional, Union

    from aicore.common.auth import Identity
    from aicore.common.command import Command
    from aicore.common.resource import Health
    from aicore.common.types import CorrelationId

    # we'd like Union[Message, Iterator[Message]] for both, however mypy complains (Liskov's principle violation)
    Request = Any
    Response = Any

    Metadata = tuple[tuple[str, str], ...]
    MultiCallable = Union[
        grpc.UnaryUnaryMultiCallable,
        grpc.UnaryStreamMultiCallable,
        grpc.StreamUnaryMultiCallable,
        grpc.StreamStreamMultiCallable,
    ]


# See also https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md
# and https://tools.ietf.org/html/rfc7540#section-8.1.2
# and https://github.com/grpc/grpc/tree/master/examples/python


def abort(state, call, code, original_details: bytes):
    """Add a traceback to exceptions which cause gRPC server to abort."""
    details = f"{original_details.decode(ENCODING)}\n{traceback.format_exc()}".encode(ENCODING)
    _original_abort(state, call, code, details)


_original_abort = grpc._server._abort
grpc._server._abort = abort


def create_grpc_metadata(correlation_id: CorrelationId) -> Metadata:
    """Create invocation/response metadata, containing single metadatum – the correlation id."""
    return ((CORRELATION_ID_HEADER, correlation_id),)


def get_correlation_id(metadata: Metadata) -> CorrelationId:
    """Get correlation id from metadata, return empty string if it's not present."""
    for header, value in metadata:
        if header == CORRELATION_ID_HEADER:
            return value
    return ""


def max_message_size_options(max_message_size: int) -> list:
    """Create gRPC options for specifying max message size."""
    if not max_message_size:
        return []

    return [
        ("grpc.max_message_length", max_message_size),
        ("grpc.max_send_message_length", max_message_size),
        ("grpc.max_receive_message_length", max_message_size),
    ]


class GRPCClientError(AICoreException):
    """Wrapper for gRPC client-related errors."""


class GRPCClient(Resource):
    """gRPC client for commands."""

    def __init__(
        self,
        name,
        logger,
        host,
        port,
        jwt_generator,
        tls_config,
        metrics,
        retrying=never_retrying,
        max_message_size=None,
    ):
        super().__init__(name, logger, tracks_liveness=False)
        self.host = host
        self.port = port
        self.jwt_generator = jwt_generator
        self.tls_config = tls_config
        self.retrying = retrying.copy(
            retry=tenacity.retry_if_exception_type(grpc.RpcError), before_sleep=self._log_send_attempt, reraise=True
        )

        self.channel: Optional[grpc.Channel] = None
        self.max_message_size = max_message_size

        # A future which matures once the channel is ready to conduct RPCs. It's used to transit the client into
        # the RUNNING state (achieved by adding a "done callback" to the future).
        # It's created using https://grpc.github.io/grpc/python/grpc.html#grpc.channel_ready_future
        # which uses https://grpc.github.io/grpc/python/grpc.html#grpc.Channel.subscribe under the hood.
        # See also https://grpc.github.io/grpc/python/grpc.html#grpc.ChannelConnectivity
        # and https://grpc.github.io/grpc/python/grpc.html#grpc.Future.
        self.channel_ready_future: Optional[grpc.Future] = None

        self.metrics = metrics
        self.metrics.register(GRPCClientMetric)

    def __repr__(self):
        tls = " with TLS" if self.tls_config.enabled else ""

        return f"gRPC client {self.name!r} ({self.host}:{self.port}{tls})"

    def prepare_state_change_log_record(self) -> tuple[str, dict[str, Any]]:
        """Return log message and kwargs appropriate for the new state the grpc client is in."""
        return "{self!r} is {health!r}", {"event_id": LogId.grpc_client_state_change}

    def create_stub(self, command: Command) -> MultiCallable:
        """Create a stub for making a remote gRPC call."""
        stub_factory = getattr(self.channel, command.method_type)
        return stub_factory(
            command.method_id(),
            request_serializer=command.request_class.SerializeToString,
            response_deserializer=command.response_class.FromString,
        )  # Replaces the generated gRPC stub

    def send(
        self,
        command: Command,
        correlation_id: CorrelationId,
        identity: Optional[Identity] = None,
        log_rpc_error=False,
        **retry_kwargs,
    ) -> None:
        """Send the given command over gRPC (i.e. process it remotely) with retries.

        Beware:
        In case of response streaming rpc the method deserialize_from_server() might store in the command
        just a generator expression. Hence the fact that this method (send) did return doesn't actually mean that
        the remote call is finished. The generator stored inside the command will get iterated only after this method
        returned, and that's when unexpected and unhandled grpc related exceptions might get raised.
        If that happens, pay attention to the DETAILS attribute of that exception, stacktrace might be confusing.
        """
        retrying = self.retrying.copy(**retry_kwargs) if retry_kwargs else self.retrying

        def timed_remote_call(*args, **kwargs):
            with self.metrics.measure_time(GRPCClientMetric.query_seconds):
                return self.remote_call(*args, **kwargs)

        try:
            stub = self.create_stub(command)
            metadata = create_grpc_metadata(correlation_id)
            response_correlation_id = retrying(timed_remote_call, stub, command, metadata, identity)

            self.validate_correlation_id(correlation_id, response_correlation_id, command, identity)
        except grpc.RpcError as error:
            if log_rpc_error:
                self.logger.error(
                    "gRPC client failed with {error_code} while calling {method!r} of {service!r} service at {host}:{port}: {details}",  # noqa: E501
                    error_code=error.code(),  # See https://github.com/grpc/grpc/blob/master/doc/statuscodes.md
                    method=command.method,
                    service=command.service,
                    host=self.host,
                    port=self.port,
                    details=error.details(),
                    correlation_id=correlation_id,
                    identity=identity,
                    message_id=LogId.grpc_client_send_error,
                )

            raise GRPCClientError from error
        except Exception:
            self.logger.error(
                "gRPC client failed to process the command {command!r}",
                command=command,
                correlation_id=correlation_id,
                identity=identity,
                message_id=LogId.grpc_client_process_command_error,
            )
            raise

    def create_ssl_credentials(self):
        """Create credentials used for TLS secured channel."""
        certificates_loader = CertificatesLoader(self.tls_config)
        private_key = None
        certificate_chain = None
        options = ()

        trusted_certificates = certificates_loader.load_trusted_certificates()

        if self.tls_config.trust_all:
            # gRPC doesn't have option for not verifying certificate
            #   - fetch certificate and add it to trusted ones
            #   - override Common Name in gRPC -> java sets it as "cnName" for self-signed certificate
            common_name, server_certificate = certificates_loader.load_server_certificate(self.host, self.port)
            options = (("grpc.ssl_target_name_override", common_name),)

            if trusted_certificates:
                trusted_certificates = f"{trusted_certificates}{server_certificate}"
            else:
                trusted_certificates = server_certificate

        if self.tls_config.mtls:
            private_key, certificate_chain = certificates_loader.load_key_and_certificate()

        return (
            grpc.ssl_channel_credentials(
                root_certificates=trusted_certificates, private_key=private_key, certificate_chain=certificate_chain
            ),
            options,
        )

    def start(self) -> None:
        """Create a communication channel; client becomes RUNNING when the channel is ready."""
        options = max_message_size_options(self.max_message_size)

        if self.tls_config.enabled:
            credentials, ssl_options = self.create_ssl_credentials()
            options.extend(ssl_options)

            self.channel = grpc.secure_channel(f"{self.host}:{self.port}", credentials, options=options)
        else:
            self.channel = grpc.insecure_channel(f"{self.host}:{self.port}", options=options)

        # This future matures once the channel is ready to conduct RPCs; more comments in GRPCClient.__init__
        self.channel_ready_future = grpc.channel_ready_future(self.channel)
        self.channel_ready_future.add_done_callback(self._on_future_done)

    def shutdown(self) -> None:
        """Close the channel."""
        self.health.shutting_down()

        if self.channel:
            # both don't block
            self.channel_ready_future.cancel()  # No-op if matured, otherwise unsubscribe from channel's state updates
            self.channel.close()  # Immediately terminate all active RPCs with the channel

        self.health.stopped()

    def populate_authentication_metadata(self, metadata: Metadata, identity: Optional[Identity] = None) -> Metadata:
        """Populate metadata with generated JWT token."""
        jwt_token = self.jwt_generator.generate(identity)
        header = create_internal_jwt_header(jwt_token)
        return metadata + (header,)

    def validate_correlation_id(
        self,
        correlation_id: CorrelationId,
        response_correlation_id: CorrelationId,
        command: Command,
        identity: Optional[Identity],
    ) -> None:
        """Log a warning when the provided correlation ids don't match."""
        if not response_correlation_id:
            self.logger.warning(
                "gRPC client received response from {method!r} of {service!r} service without any correlation id",
                method=command.method,
                service=command.service,
                correlation_id=correlation_id,
                identity=identity,
                message_id=LogId.grpc_client_missing_correlation_id,
            )
        elif response_correlation_id != correlation_id:
            self.logger.warning(
                "gRPC client received response from {method!r} of {service!r} service with inconsistent correlation id {response_correlation_id!r}",  # noqa: E501
                method=command.method,
                service=command.service,
                response_correlation_id=response_correlation_id,
                correlation_id=correlation_id,
                identity=identity,
                message_id=LogId.grpc_client_inconsistent_correlation_id,
            )

    def remote_call(
        self, stub: MultiCallable, command: Command, metadata: Metadata, identity: Optional[Identity] = None
    ) -> CorrelationId:
        """Invoke a remote call using the stub with given command and metadata."""
        request = command.serialize_for_server()
        metadata = self.populate_authentication_metadata(metadata, identity)

        if hasattr(stub, "with_call"):
            # Only unary responses have with_call()
            response, grpc_call = stub.with_call(request, metadata=metadata)
        else:
            # Stream responses are both iterable and grpc.Call objects
            response = grpc_call = stub(request, metadata=metadata)

        command.deserialize_from_server(response)
        return get_correlation_id(grpc_call.initial_metadata())

    def _on_future_done(self, _future: grpc.Future):
        """Mark client as running when the channel is ready."""
        channel_is_ready = not self.channel_ready_future.cancelled()
        if channel_is_ready:
            self.health.running()

    def _log_send_attempt(self, retry_state: tenacity.RetryCallState):
        """Log failed attempt to send command."""
        # Same as Logger.warning + added depth to preserve code location in log
        log_callback = (
            self.logger.logger.opt(capture=True, depth=4).bind(_record_type="message", _color=WARNING_COLOR).warning
        )

        bound_arguments = inspect.signature(self.remote_call).bind(*retry_state.args, **retry_state.kwargs)
        command = bound_arguments.arguments["command"]
        correlation_id = get_correlation_id(bound_arguments.arguments["metadata"])
        identity = bound_arguments.arguments["identity"]

        error = retry_state.outcome.exception()
        log_callback(
            "gRPC client {name!r} raised {error_name!r} while sending {command!r} at {host}:{port}, next attempt in {sleep} s",  # noqa: E501
            name=self.name,
            error=error,
            error_name=type(error).__name__,
            command=command,
            host=self.host,
            port=self.port,
            attempt=retry_state.attempt_number,
            sleep=retry_state.next_action.sleep,
            correlation_id=correlation_id,
            identity=identity,
            message_id=LogId.grpc_client_send_error,
        )


class GRPCServer(BackgroundThread):
    """gRPC server for commands.

    As one would expect, this uses grpc.server under the hood. Unfortunately, grpc._server._Server.start() spawns
    a polling thread with a hardcoded target (an infinite polling loop), from which we can't update health
    and respond to shutdown initiation. So:
    1) We don't use grpc._server._Server.start() and replace it instead:
    - GRPCServer already is a BackgroundThread => no need to create another thread (callback set in super().__init__)
    - the rest of the grpc._server._Server.start()'s code is pasted into GRPCServer.start()
    2) We use our own polling loop, which updates health and responds to shutdown initiation. For more details see
    the docstring of GRPCServer.serve_forever.
    """

    def __init__(
        self,
        name,
        host,
        port,
        commands,
        microservice,
        logger,
        authenticator,
        tls_config,
        metrics,
        max_message_size,
        poll_timeout=RESPONSIVENESS_PERIOD,
        shutdown_rpc_timeout=5,
    ):
        super().__init__(name, logger, callback=self.serve_forever)
        self.host = host
        self.port = port
        self.commands = {command_class.method_id(): command_class for command_class in commands}
        self.microservice = microservice
        self.authenticator = authenticator
        self.tls_config = tls_config
        self.poll_timeout = poll_timeout  # [s] The polling thread checks whether it should shutdown at least this often
        # [s] At shutdown wait this long for the active RPCs to finish before they get aborted
        self.shutdown_rpc_timeout = shutdown_rpc_timeout

        # most commands do CPU-bound ML computations => no use for thread-based parallelism (scale horizontally instead)
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=1, thread_name_prefix=self.name + "_worker_"
        )

        # Imagine the following situation:
        # Some Command's process() method got stuck doing its computation. This means the thread in ThreadPool
        # executing this computation can't be joined. We also initiate shutdown of the GRPCServer. The polling thread
        # is now waiting for the ThreadPool to shutdown (see GRPCServer.serve_forever) – which it can't, as its thread
        # is stuck => GRPCServer never reaches STOPPED state.
        #
        # Therefore, someone waiting for the GRPCServer to get to the STOPPED state times out waiting for it and
        # the whole process decides to exit – but it actually won't exit. Why? Because ThreadPool uses atexit.register
        # to register an atexit callback to join all threads ever created by any ThreadPool
        # (see concurrent.futures.thread._python_exit and the comment above it).
        #
        # Now, the GRPCServer gives a chance to the ThreadPool to gracefully shutdown it's threads (we call
        # thread_pool.shutdown() is serve_forever) AND we DON'T want to wait for the pool's threads to finish when
        # the whole process is exiting => we unregister this callback.
        atexit.unregister(concurrent.futures.thread._python_exit)  # does nothing when already unregistered

        options = max_message_size_options(max_message_size)
        self.server = grpc.server(self.thread_pool, handlers=(self,), options=options)

        self.metrics = metrics
        self.metrics.register(GRPCServerMetric)
        # Tracking the value manually would require further modifications of the library code => callback is easier
        self.metrics.set_callback(GRPCServerMetric.queue_size, lambda: self.server._state.active_rpc_count)

    def __repr__(self):
        tls = " with TLS" if self.tls_config.enabled else ""

        return f"gRPC server {self.name!r} ({self.host}:{self.port}{tls})"

    def prepare_state_change_log_record(self) -> tuple[str, dict[str, Any]]:
        """Return log message and kwargs appropriate for the new state the grpc server is in."""
        message = "{self!r} is {health!r}"
        kwargs = {"event_id": LogId.grpc_server_state_change}

        if self.health.state == RuntimeState.RUNNING:
            message += " and serving with methods {methods!r}"
            kwargs["methods"] = list(self.commands.keys())

        return message, kwargs

    def create_ssl_credentials(self):
        """Create credentials used for TLS secured channel."""
        certificates_loader = CertificatesLoader(self.tls_config)

        pem_keys = [certificates_loader.load_key_and_certificate()]
        trusted_certificates = certificates_loader.load_trusted_certificates()

        return grpc.ssl_server_credentials(
            pem_keys,
            root_certificates=trusted_certificates,
            require_client_auth=self.tls_config.mtls == ServerTLSConfig.MTLSTypes.REQUIRED,
        )

    def start(self) -> None:
        """Start the gRPC server and its background polling thread."""
        if self.tls_config.enabled:
            server_credentials = self.create_ssl_credentials()
            self.server.add_secure_port(f"{self.host}:{self.port}", server_credentials)
        else:
            self.server.add_insecure_port(f"{self.host}:{self.port}")

        # code snippet copied from grpc._server._start (without the thread setup+start – we do that differently)
        state = self.server._state
        with state.lock:
            if state.stage is not grpc._server._ServerStage.STOPPED:
                raise ValueError("Cannot start already-started server!")

            state.server.start()
            state.stage = grpc._server._ServerStage.STARTED
            grpc._server._request_call(state)
        # end

        super().start()

    def authenticate(self, context: grpc.ServicerContext) -> Identity:
        """Authenticate successfully or throw exception."""
        metadata = context.invocation_metadata()
        header = get_authorization_header(metadata)
        return self.authenticator.authenticate(header)

    def command_handler(
        self, command_class: type[Command], request: Request, context: grpc.ServicerContext
    ) -> Response:
        """Handle a gRPC call by delegating it to the given command.

        Beware:
        In case of response streaming rpc it might happen that any of the command.<method>() called here
        (especially Command.serialize_for_client()) don't actually do the work when called – they might just
        store or return a generator expression or an iterator. In that case the actual work is only done when
        the response is iterated over – when the individual protobuf messages are streamed back to the client.
        That happens only after this method returns – somewhere deep in the gRPC library.
        If any exception get raised there, it gets handled:
            - it's logged by the gRPC library logger
            - the rpc call is aborted
            => our GRPCServer has no idea any exception was raised.
        To see what actually happened, see DETAILS of the exception on the CLIENT side.
        """
        correlation_id = ""
        identity = None

        try:
            with self.metrics.measure_time(GRPCServerMetric.processing_seconds, stage="authentication"):
                identity = self.authenticate(context)

            correlation_id = get_correlation_id(context.invocation_metadata())
            self.validate_correlation_id(correlation_id, command_class, identity)
            metadata = create_grpc_metadata(correlation_id)
            context.send_initial_metadata(metadata)

            command = command_class.deserialize_from_client(request)
            # Remove once Microservice is sequential + beware of streaming (.process() might just create e.g. generator)
            with self.microservice.process_lock:
                with self.metrics.measure_time(GRPCServerMetric.processing_seconds, stage="processing"):
                    command.process(self.microservice, correlation_id, identity)  # Inversion of control
            response = command.serialize_for_client()

        except AuthenticationError as error:
            self.logger.warning(
                "gRPC server received command {command_class.__name__} with incorrect authentication: {error}",
                request=request,
                command_class=command_class,
                error=error,
                correlation_id=correlation_id,
                identity=identity,
                message_id=LogId.grpc_server_unauthenticated,
            )
            self.metrics.increment(GRPCServerMetric.auth_failures_total)
            context.abort(code=grpc.StatusCode.UNAUTHENTICATED, details=str(error))

        except CommandError as error:

            self.logger.warning(
                "gRPC worker failed to process the command {command!r} due to {reason} with message: {message}",
                command=command,
                reason=error.reason,
                message=error.message,
                context=error.kwargs,
                correlation_id=correlation_id,
                identity=identity,
                message_id=LogId.grpc_server_command_error,
            )
            context.abort(code=grpc.StatusCode.INTERNAL, details=json.dumps(error.context))

        except Exception as error:
            self.logger.exception(
                "gRPC worker thread raised an exception while processing command {command!r}",
                command=command,
                error=error,
                correlation_id=correlation_id,
                identity=identity,
                message_id=LogId.grpc_server_process_error,
            )
            self.health.shutting_down(error=True)
            message = f"gRPC worker thread raised an exception while processing request {request!r} with correlation_id {correlation_id!r}: {error!r}"  # noqa: E501
            context.abort(code=grpc.StatusCode.UNKNOWN, details=message)

        if command.enable_logging:
            self.logger.event(
                "gRPC worker thread successfully processed {command!r} from {peer!r}",
                command=command,
                peer=context.peer(),
                correlation_id=correlation_id,
                identity=identity,
                event_id=LogId.grpc_server_process,
            )

        return response

    def validate_correlation_id(
        self, correlation_id: CorrelationId, command_class: type[Command], identity: Identity
    ) -> None:
        """Log a warning when the correlation id is empty."""
        if not correlation_id:
            self.logger.warning(
                "gRPC server received request to perform {method!r} of {service!r} service without any correlation id",
                method=command_class.method,
                service=command_class.service,
                identity=identity,
                message_id=LogId.grpc_server_missing_correlation_id,
            )

    # Compatible signature with grpc.GenericRpcHandler
    def service(self, handler_call_details: grpc.HandlerCallDetails) -> Optional[grpc.RpcMethodHandler]:
        """Return a method handler suitable for handling a rpc call described by the call details."""
        command_class = self.commands.get(handler_call_details.method, None)

        if not command_class:
            correlation_id = get_correlation_id(handler_call_details.invocation_metadata)
            self.logger.error(
                "gRPC server does not support gRPC method {method!r}",
                method=handler_call_details.method,
                correlation_id=correlation_id,
                message_id=LogId.grpc_server_unsupported_method,
            )
            return None  # None is expected when this grpc.GenericRpcHandler can't provide handler for the rpc call

        def timed_command_handler(*args, **kwargs):
            with self.metrics.measure_time(GRPCServerMetric.processing_seconds, stage="total"):
                return self.command_handler(command_class, *args, **kwargs)

        self.metrics.increment(GRPCServerMetric.commands_total, type=command_class.method)
        rpc_method_handler_factory = getattr(grpc, f"{command_class.method_type}_rpc_method_handler")
        return rpc_method_handler_factory(
            behavior=timed_command_handler,  # Submitted to the thread pool
            request_deserializer=command_class.request_class.FromString,
            response_serializer=command_class.response_class.SerializeToString,
        )

    def serve_forever(self, health: Health):  # Replaces grpc._server._serve
        """Periodically poll for incoming gRPC calls, update health and end when requested.

        This is a slightly enriched code from the grpc._server._serve() function, which it replaces.

        Keep in mind that this is the callback of the BackgroundThread the GRPCServer inherits from. This means
        that this GRPCServer becomes RUNNING just before this callback is called and becomes STOPPED right after
        the callback returns.

        Differences from the library function:
        1) Custom poll timeout – uses self.poll_timeout instead of a hardcoded constant
            grpc._server._DEALLOCATED_SERVER_CHECK_PERIOD_S.
        2) Health update (alive)
        3) Shutdown check every event/poll_timeout (at the end of the while cycle).
        => self.server.stop() is called when shutdown is requested. This:
            - immediately makes the server stop accepting new connections,
            - cancels remaining active RPCs after self.shutdown_rpc_timeout seconds, and
            - puts an event into the state.completion_queue which causes the grpc._server._process_event_and_continue
            to return False and hence break the while loop.
        4) Waiting for ThreadPool's threads to finish. Once the self.server.stop() is called, the server won't accept
        any new RPCs => no more work being submitted to the ThreadPool. Hence it should be able to shutdown shortly
        even when waiting for its threads to finish.
        """
        state = self.server._state

        while True:
            timeout = time.time() + self.poll_timeout  # Custom poll timeout, 1)
            event = state.completion_queue.poll(timeout)

            if state.server_deallocated:
                grpc._server._begin_shutdown_once(state)

            if event.completion_type != grpc._cython.cygrpc.CompletionType.queue_timeout:
                if not grpc._server._process_event_and_continue(state, event):
                    break  # Break instead of return (for waiting for rpc/threads shutdown), 2)

            event = None

            health.alive()  # 2)
            if health.state != RuntimeState.RUNNING:  # 3)
                self.server.stop(grace=self.shutdown_rpc_timeout)  # Doesn't block, idempotent, 3)

        self.thread_pool.shutdown(wait=True)  # Block until all the remaining RPC handling callbacks get processed, 4)
