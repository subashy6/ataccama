"""Resources (objects with managed life-cycle), their runtime state and health."""

from __future__ import annotations

import contextlib
import enum
import threading
import time

from typing import TYPE_CHECKING

import tenacity

from aicore.common.constants import RESPONSIVENESS_PERIOD
from aicore.common.exceptions import AICoreException
from aicore.common.registry import LogId
from aicore.common.retry import stop_if
from aicore.common.utils import set_event_after


if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from typing import Any, Optional, TypeVar

    from aicore.common.logging import LoggedAction, Logger

    TResource = TypeVar("TResource", bound="Resource")


class RuntimeState(enum.Enum):
    """State of a resource."""

    NOT_READY = enum.auto()
    RUNNING = enum.auto()
    SHUTTING_DOWN = enum.auto()
    STOPPED = enum.auto()

    def __repr__(self):
        return self.name


class ResourceLifeCycleError(AICoreException):
    """General resource life-cycle management error."""

    def __init__(self, *resource_names: str):
        super().__init__(*resource_names)

    @property
    def resource_names(self) -> tuple[str, ...]:
        """Return names of the resources whose whose life-cycle management failed."""
        return self.args


class ResourceVerificationError(ResourceLifeCycleError):
    """Resources failed to verify a predicate."""


class ResourceStartError(ResourceLifeCycleError):
    """Resources failed to start."""


class ResourceShutdownError(ResourceLifeCycleError):
    """Resources failed to shutdown."""


class Health:
    """Thread-safe state of resource's health (liveness, readiness and last error).

    The state can advance only in one direction: STARTING –> RUNNING –> SHUTTING_DOWN –> STOPPED.
    """

    LIVENESS_NEVER_UPDATED: int = -1

    def __init__(self, tracks_liveness: bool = True, on_state_change: Callable[[], None] = lambda: None):
        self._state = RuntimeState.NOT_READY
        self._details = ""
        self._error = False
        self.last_alive = self.LIVENESS_NEVER_UPDATED
        self.tracks_liveness = tracks_liveness
        self.on_state_change = on_state_change  # Hook for custom callback

    def __repr__(self):
        representation = self._state.name

        if self._error:
            representation = f"{representation} (ERROR)"

        if self._details:
            representation = f"{representation} - {self._details}"

        return representation

    @property
    def state(self) -> RuntimeState:
        """Get current runtime state of the resource."""
        return self._state

    @property
    def details(self) -> str:
        """Get current health details of the resource."""
        return self._details

    @property
    def error(self) -> bool:
        """Get an indication whether an error occurred for the resource."""
        return self._error

    @error.setter
    def error(self, error: bool):
        """Set an indication whether an error occurred for the resource."""
        if self._error != error:
            self._error = error
            self.on_state_change()

    def is_healthy(self, timeout: float, now: Optional[float] = None) -> bool:
        """Return true if the resource is RUNNING and it has reported that it's alive recently enough."""
        if now is None:
            now = int(time.time())

        return self._state == RuntimeState.RUNNING and (not self.tracks_liveness or now - self.last_alive <= timeout)

    def alive(self, now: Optional[int] = None) -> None:
        """Indicate that the resource is alive, i.e. update its last alive timestamp."""
        if now is None:
            now = int(time.time())

        if self._state in {RuntimeState.NOT_READY, RuntimeState.RUNNING, RuntimeState.SHUTTING_DOWN}:
            self.last_alive = now

    def not_ready(self, details: str = "", error: bool = False) -> None:
        """Indicate that the resource is not ready."""
        if self._state == RuntimeState.NOT_READY:
            self._change_state(RuntimeState.NOT_READY, details, error)

    def running(self, details: str = "", error: bool = False) -> None:
        """Indicate that the resource is running."""
        if self._state == RuntimeState.NOT_READY:
            self.alive()
            self._change_state(RuntimeState.RUNNING, details, error)

    def shutting_down(self, details: str = "", error: bool = False) -> None:
        """Indicate that the resource is shutting down."""
        if self._state in {RuntimeState.NOT_READY, RuntimeState.RUNNING}:
            self._change_state(RuntimeState.SHUTTING_DOWN, details, error)

    def stopped(self, details: str = "", error: bool = False) -> None:
        """Indicate that tha resource is stopped."""
        if self._state != RuntimeState.STOPPED:
            self._change_state(RuntimeState.STOPPED, details, error)

    def _change_state(self, state: RuntimeState, details: str, error: bool):
        """Change internal state if the state differs from previous one."""
        if self._state == state and self._details == details and self._error == error:
            return

        self._state = state
        self._details = details
        self._error = error
        self.on_state_change()


class Resource:
    """Anything with managed life-cycle."""

    def __init__(self, name: str, logger: Logger, tracks_liveness: bool = True):
        self.name = name
        self.logger = logger

        self.health = Health(tracks_liveness, on_state_change=self.on_state_change)

    def __repr__(self):
        return f"Resource {self.name!r}"

    def start(self) -> None:
        """Initiate start of the resource, don't block."""
        self.health.running()  # To be implemented by child classes

    def shutdown(self) -> None:
        """Initiate shutdown of the resource, don't block."""
        self.health.stopped()  # To be implemented by child classes

    def on_state_change(self) -> None:
        """Log state change of the resource."""
        message, additional_kwargs = self.prepare_state_change_log_record()
        if not message:
            return  # Don't log anything on empty message

        kwargs = {"self": self, "health": self.health, **additional_kwargs}
        # Add "depth=2" option, otherwise identical to Logger.info
        # This contextualizes the logrecord to the line of code where state change was triggered (2 levels up in stack).
        self.logger.logger.opt(capture=True, depth=2).bind(_record_type="message").info(message, **kwargs)

    def prepare_state_change_log_record(self) -> tuple[str, dict[str, Any]]:
        """Return log message and kwargs appropriate for the new state the resource is in."""
        return "{self!r} is {health!r}", {"event_id": LogId.resource_state_change}

    @contextlib.contextmanager
    def running(self: TResource, timeout: Optional[float]) -> Iterator[TResource]:
        """Context manager for a running resource, raise if the resource fails to become running or stopped in time."""
        manager = Resources()
        manager.add(self)

        with self.logger.action(LogId.resource_start) as action:
            action.start("Starting {self!r}", self=self)
            start_timed_out = set_event_after(timeout)

            try:
                manager.start(action, start_timed_out)
            except Exception as error:
                action.exception("{self!r} failed to start in time", self=self, error=error)
                raise

            action.finish("{self!r} successfully started", self=self)

        try:
            yield self
        finally:
            with self.logger.action(LogId.resource_shutdown) as action:
                action.start("Shutting down {self!r}", self=self)
                shutdown_timed_out = set_event_after(timeout)

                try:
                    manager.shutdown(action, shutdown_timed_out)
                except Exception as error:
                    action.exception("{self!r} failed to shutdown in time", self=self, error=error)
                    raise

                action.finish("{self!r} successfully stopped", self=self)


class Resources:
    """Manages resources of a microservice."""

    def __init__(self):
        self.resources: dict[str, Resource] = {}

    def __iter__(self) -> Iterator[Resource]:
        return iter(self.resources.values())

    def __add__(self, other) -> Resources:
        if not isinstance(other, Resources):
            raise TypeError

        resources = Resources()
        resources.resources = {**self.resources, **other.resources}

        return resources

    def __repr__(self):
        return repr({resource.name: resource.health for resource in self})

    def add(self, resource: Resource) -> None:
        """Add the resource, i.e. start managing it."""
        if resource.name in self.resources:
            raise ValueError(f"Resource {resource.name!r} already present")

        self.resources[resource.name] = resource

    def dead(self, timeout) -> dict[str, Health]:
        """Get resources which haven't recently reported that are still alive."""
        return {
            resource.name: resource.health
            for resource in self.resources.values()
            if not resource.health.is_healthy(timeout)
        }

    def start(self, action: LoggedAction, cancel_wait: threading.Event) -> None:
        """Start all managed resources, block until all are running."""
        for resource in self:
            try:
                resource.start()
            except Exception as error:
                resource.health.error = True
                raise ResourceStartError(resource.name) from error

        try:
            self.wait(action, cancel_wait, self._verify_running)
        except ResourceVerificationError as error:
            raise ResourceStartError(*error.resource_names) from None

    def shutdown(self, action: LoggedAction, cancel_wait: threading.Event) -> None:
        """Shutdown all managed resources, block until all are stopped."""
        for resource in self:
            try:
                resource.shutdown()
            except Exception as error:
                resource.health.error = True
                raise ResourceShutdownError(resource.name) from error

        try:
            self.wait(action, cancel_wait, predicate=lambda r: r.health.state == RuntimeState.STOPPED)
        except ResourceVerificationError as error:
            raise ResourceShutdownError(*error.resource_names) from None

    def wait(self, action: LoggedAction, cancel_wait: threading.Event, predicate: Callable[[Resource], bool]) -> None:
        """Block until all resources verify the predicate."""
        pending = {}

        while True:
            # str(health) to capture current snapshot of health, not a reference to the evolving health object
            new_pending = {resource: str(resource.health) for resource in self if not predicate(resource)}
            if not new_pending:
                return  # All resources verify the predicate

            if new_pending.keys() != pending.keys():  # Report change in pending resources
                action.info(
                    "*** Waiting for resources: {pending_resources} ***",
                    pending_resources={resource.name for resource in new_pending},
                    message_id=LogId.resources_wait,
                )

            pending = new_pending

            if cancel_wait.wait(RESPONSIVENESS_PERIOD):
                # Wait was cancelled and there are still some resources which didn't verify the predicate
                raise ResourceVerificationError(*pending.keys())

    @staticmethod
    def _verify_running(resource: Resource) -> bool:
        """Return True for a running resource, False for a not ready one; raise otherwise."""
        state = resource.health.state
        if state == RuntimeState.RUNNING:
            return True
        elif state == RuntimeState.NOT_READY:
            return False
        else:
            raise ResourceStartError(resource.name)  # Raise as it can't ever become a running resource


class BackgroundThread(Resource):
    """Spawns a task in a background thread."""

    def __init__(
        self,
        name: str,
        logger: Logger,
        callback: Callable[[Health], None],  # Accepts health to be able to indicate liveness and check for shutdown
        auto_running: bool = True,
        tracks_liveness: bool = True,
    ):
        super().__init__(name, logger, tracks_liveness)
        self.callback = callback  # Use functools.partial to inject dependencies into the callback
        self.auto_running = auto_running  # Whether this resource becomes RUNNING right before the callback is called

        # Daemon threads do not receive signals and are killed when their parent exits
        self.thread = threading.Thread(name=self.name, target=self.run, daemon=True)

    def start(self) -> None:
        """Start the background thread."""
        self.thread.start()

    def shutdown(self) -> None:
        """Signal to the background thread that it should shutdown."""
        if self.thread.is_alive():
            self.health.shutting_down()
        else:
            self.health.stopped()  # Never started thread can be directly declared as stopped

    def run(self):
        """Method representing the thread's activity, provides exception handling around the callback."""  # noqa: D401
        if self.auto_running:
            self.health.running()
        try:
            self.callback(self.health)
        except Exception as error:
            self.logger.exception(
                "BackgroundThread {name!r} raised an unhandled exception",
                name=self.name,
                error=error,
                event_id=LogId.resource_unhandled_exception,
            )
            self.health.stopped(error=True)
        else:
            self.health.stopped()


class ReadinessDependency(Resource):
    """Resource that becomes running once the readiness predicate is verified.

    The predicate is repeatedly evaluated until it either returns True (and the resource thus becomes running)
    or shutdown is triggered.
    """

    def __init__(
        self,
        name: str,
        logger: Logger,
        onstart_retrying: tenacity.Retrying,
        readiness_predicate: Callable[[], bool],
        tracks_liveness: bool,
    ):
        super().__init__(name, logger, tracks_liveness)

        self.readiness_checker = threading.Thread(
            target=self.wait_for_resource_readiness, name=f"{name}_readiness_checker", daemon=True
        )
        self.readiness_predicate = readiness_predicate  # Once evaluates to True, the resource becomes running

        asked_to_shutdown = stop_if(lambda _: self.health.state != RuntimeState.NOT_READY)
        self.onstart_retrying = onstart_retrying.copy(
            retry=tenacity.retry_if_result(lambda is_ready: not is_ready),  # Retry if the predicate returns False
            stop=asked_to_shutdown,  # Stop when shutdown was triggered (overrides the fact that we might like to retry)
        )

    def start(self) -> None:
        """Start readiness checking of the resource."""
        self.readiness_checker.start()

    def shutdown(self) -> None:
        """Stop the resource."""
        self.health.stopped()  # Also makes the retrying controller stop retrying (if it's still ongoing) => thread ends

    def wait_for_resource_readiness(self):
        """Repeatedly try verifying readiness of the resource until success or shutdown is triggered."""
        try:
            self.onstart_retrying(self.readiness_predicate)
        except tenacity.RetryError:
            # The retrying controller was told to stop retrying (e.g. via controller's event)
            self.health.shutting_down()
        except Exception as error:
            self.logger.exception(
                "Readiness wait on dependency {self!r} raised an unhandled exception",
                self=self,
                error=error,
                event_id=LogId.readiness_wait_error,
            )
            self.health.shutting_down(error=True)
        else:
            self.health.running()
