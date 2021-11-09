"""Bare metal microservices supervisor.

Observations:
  a) Ctrl+C in terminal/console (Linux/Windows) sends the SIGINT/CTRL_C_EVENT to the whole process group.

Windows specific observations:
  b) CTRL_C_EVENT seems not to be possible to send to a single process within a process group, it's always sent
     to the whole group (including the process which send the signal).
  c) CTRL_C_EVENT works only under certain conditions and generally seems fragile.
     See: https://docs.microsoft.com/en-us/windows/console/generateconsolectrlevent
     and Remarks section in: https://docs.microsoft.com/en-us/windows/console/setconsolectrlhandler
  d) Signals don't interrupt blocking functions by default => Thread.join() or Event.wait() prevent the signal
     from being handled. See: https://mail.python.org/pipermail/python-dev/2017-August/148800.html
  e) Once the main thread exits, it can't handle signals anymore (probably due to d)).
  f) SIGTERM isn't useful on Windows, it's available just because it's one of the six signals required by standard C.
     See: https://bugs.python.org/issue26350#msg260201
"""

from __future__ import annotations

import enum
import functools
import json
import signal
import subprocess
import sys
import time

from typing import TYPE_CHECKING

import requests

from aicore.common.config import ClientTLSConfig, ConfigOptionsBuilder, server_options
from aicore.common.constants import CORRELATION_ID_HEADER, RESPONSIVENESS_PERIOD
from aicore.common.http import HTTPClient, create_url
from aicore.common.microservice import Microservice
from aicore.common.registry import LogId
from aicore.common.resource import BackgroundThread, Health, RuntimeState
from aicore.common.tls import TLSConfigType
from aicore.common.utils import datetime_now, random_correlation_id
from aicore.registry import MICROSERVICE_NAMES, collect_health_check_config_options


if TYPE_CHECKING:
    import datetime

    from collections.abc import Callable
    from typing import Any, Optional, Union

    from aicore.common.logging import Logger
    from aicore.common.types import CorrelationId


# Updated to be compatible with new Spring Boot's Actuator (separated liveness and readiness)
# Whole Supervisor will be removed soon, no need to polish the implementation


def readiness_actuator_client(target: str, config) -> HTTPClient:
    """Return readiness actuator client for the target (e.g. 'mmm' or 'neighbors') based on the config."""
    host = getattr(config, f"{target}_host")
    port = getattr(config, f"{target}_http_port")
    tls_config = ClientTLSConfig(TLSConfigType.HTTP, target, config)

    url = create_url(host, port, "actuator/health/readiness", tls_config.enabled)

    return HTTPClient(url, tls_config)


class ActuatorStatus(str, enum.Enum):
    """State of a resource in Spring Actuator "status" format."""

    # Spring Actuator status "UNKNOWN" is not used
    UP = "UP"  # Liveness: OK, readiness: OK
    DOWN = "DOWN"  # Liveness: FAIL, readiness: N/A
    OUT_OF_SERVICE = "OUT_OF_SERVICE"  # Liveness: OK, readiness: FAIL

    @classmethod
    def from_health(cls, health: Health, timeout: float, now: Optional[float] = None):
        """Create actuator status reflecting given health, heartbeat timeout and now timestamp."""
        if health.is_healthy(timeout, now):
            return ActuatorStatus.UP
        elif health.state == RuntimeState.RUNNING:  # Not healthy but running
            return ActuatorStatus.DOWN
        else:
            return ActuatorStatus.OUT_OF_SERVICE


class ReadinessActuatorResponse:
    """Wrapper for a response from a readiness actuator endpoint."""

    def __init__(
        self,
        result_of_get: Union[requests.Response, Exception],
        timestamp: datetime.datetime,
        correlation_id: CorrelationId,
    ):
        received_successfully = isinstance(result_of_get, requests.Response)
        self.raw: Optional[requests.Response] = result_of_get if received_successfully else None
        self.error: Optional[Exception] = result_of_get if not received_successfully else None

        self.details: dict[str, Any] = {}
        self.timestamp = timestamp
        self.correlation_id = correlation_id

        if received_successfully:
            try:
                self.details = json.loads(self.raw.text)
            except json.JSONDecodeError as decode_error:
                self.error = decode_error

    @classmethod
    def from_client(
        cls,
        http_client: HTTPClient,
        timeout: float,
        correlation_id: CorrelationId,
        now: Optional[datetime.datetime] = None,
    ) -> ReadinessActuatorResponse:
        """Perform GET on the url and wrap the result into the readiness actuator response wrapper."""
        result: Union[requests.Response, Exception]

        try:
            result = http_client.get(headers={CORRELATION_ID_HEADER: correlation_id}, timeout=timeout)
        except (requests.ConnectionError, requests.HTTPError, requests.Timeout) as error:
            result = error
        return cls(result, now or datetime_now(), correlation_id)

    @property
    def is_valid(self):
        """Return true if the response was received and the payload was valid JSON."""
        return self.error is None

    @property
    def received_successfully(self):
        """Return true if the GET request completed."""
        return isinstance(self.raw, requests.Response)

    @property
    def reported_alive(self):
        """Return true if a response was received from the actuator endpoint."""
        return self.received_successfully

    @property
    def reported_ready(self):
        """Return true if the actuator endpoint indicated readiness via the 'status' property."""
        # See https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#container-probes
        return self.received_successfully and 200 <= self.raw.status_code < 400

    def liveness_or_readiness_differ(self, other: ReadinessActuatorResponse) -> bool:
        """Return true if the two responses differ in liveness or readiness or both."""
        return other.reported_alive != self.reported_alive or other.reported_ready != self.reported_ready


class Supervisor(Microservice):
    """Bare metal supervisor for microservices.

    Note: not to be run in a Docker container as a monolithical version of AI Core.
    """

    def __init__(self, config):
        super().__init__("supervisor", config)

        self.wsgi = self.wsgi_server()

        microservices: list[str] = self.config.supervisor_microservices
        captured_microservices: list[str] = self.config.supervisor_captured_microservices

        self.logger.info(
            "Microservices to control: {microservices}",
            microservices=microservices,
            message_id=LogId.supervisor_controlled_microservices,
        )
        if captured_microservices:
            self.logger.info(
                "Microservices to capture output of: {microservices}",
                microservices=captured_microservices,
                message_id=LogId.supervisor_captured_microservices,
            )

        for name in captured_microservices:
            if name not in microservices:
                self.logger.warning(
                    "Can't capture output of a not controlled microservice {microservice!r}",
                    microservice=name,
                    message_id=LogId.supervisor_unknown_captured_microservice,
                )

        for name in microservices:
            popen_args = [sys.executable, self.config.manage_py_location, "run", name, "native"]
            capture_output = name in captured_microservices
            process = ChildProcess(name, self.logger, popen_args, capture_output)

            respawner = ProcessRespawner(f"{name}_respawner", self.logger, self.config, process)
            self.operational_resources.add(respawner)

    @property
    def total_respawns(self) -> int:
        """Return the total number of microservice processes respawns."""
        return sum(
            resource.respawns for resource in self.operational_resources if isinstance(resource, ProcessRespawner)
        )


class ProcessRespawner(BackgroundThread):
    """Tries to keep a process with a readiness actuator endpoint alive.

    Note: becomes RUNNING only when the controlled process reports as alive and ready.
    """

    def __init__(self, name: str, logger: Logger, config, process: ChildProcess):
        super().__init__(
            name,
            logger,
            callback=self.control_forever,
            auto_running=False,  # We make respawner go into the running state only when the process reports as ready
        )
        self.config = config
        self.readiness_client = readiness_actuator_client(process.name, config)
        self.process = process
        self.respawns: int = 0
        self.process_health: Optional[ReadinessActuatorResponse] = None

    def control_forever(self, health: Health):
        """Keep trying to have an alive process until the respawner is asked to shut down."""
        try:
            manage = self._spawn_process
            while health.state in {RuntimeState.NOT_READY, RuntimeState.RUNNING}:
                manage, next_iteration_in = manage()
                health.alive()
                self.sleep_between_iterations(next_iteration_in)
        finally:  # Child process doesn't die when parent process dies => try/finally to ensure it gets shut down
            self._shutdown_process()

    def update_process_health(self, correlation_id: CorrelationId):
        """Update readiness actuator response from the controlled process."""
        self.process_health = ReadinessActuatorResponse.from_client(
            self.readiness_client, self.config.supervisor_liveness_connection_timeout, correlation_id
        )

        if not self.process_health.received_successfully:
            self.logger.warning(
                "Failed to get readiness of the process {name!r} from {url!r}: {error}",
                url=self.readiness_client.url,
                error=self.process_health.error,
                correlation_id=correlation_id,
                message_id=LogId.supervisor_get_process_health_error,
                **self.process.log_kwargs,
            )
        elif not self.process_health.is_valid:
            self.logger.error(
                "Invalid readiness response of the process {name!r} from {url!r}: {error}",
                url=self.readiness_client.url,
                error=self.process_health.error,
                correlation_id=correlation_id,
                message_id=LogId.supervisor_invalid_process_health_response,
                **self.process.log_kwargs,
            )

    def sleep_between_iterations(self, sleep: float):
        """Sleep between life-cycle management iterations, interrupt the sleeping if shutdown is requested."""
        sleep_end = time.monotonic() + sleep

        while True:
            remaining = sleep_end - time.monotonic()
            if remaining <= 0 or self.health.state not in {RuntimeState.NOT_READY, RuntimeState.RUNNING}:
                return

            time.sleep(min(RESPONSIVENESS_PERIOD, remaining))
            self.health.alive()

    def prepare_state_change_log_record(self) -> tuple[str, dict[str, Any]]:
        """Return log message and kwargs appropriate for the new state the process respawner is in."""
        return "", {}  # Don't log state changes of the respawner as they aren't interesting

    # The following private methods are to be called only from the control_forever() method

    def _spawn_process(self) -> tuple[Callable, float]:
        """Spawn the process."""
        is_respawn = self.process.pid != -1
        self.process_health = None
        self.process.spawn()
        if is_respawn:
            self.respawns += 1
            self.logger.warning(
                "Process {name!r} respawn count: {respawns}",
                name=self.process.name,
                respawns=self.respawns,
                message_id=LogId.process_respawn_count,
            )
        return self._liveness_check, self.config.supervisor_liveness_start_delay

    def _liveness_check(self, attempt: int = 1) -> tuple[Callable, float]:
        """Verify liveness and readiness of the process."""
        if not self.process.is_running():
            self.logger.error(
                "Process {name!r} pid: {pid} isn't running",
                message_id=LogId.process_not_running,
                **self.process.log_kwargs,
            )
            return self._spawn_process, 0

        correlation_id = random_correlation_id()
        prev_process_health = self.process_health
        self.update_process_health(correlation_id)

        log_kwargs = {
            "alive": self.process_health.reported_alive,
            "ready": self.process_health.reported_ready,
            "correlation_id": correlation_id,
        }
        log_kwargs.update(self.process.log_kwargs)

        # Log current liveness and readiness state (if it changed or if the process isn't alive)
        if self.process_health.reported_alive:
            if not prev_process_health or self.process_health.liveness_or_readiness_differ(prev_process_health):
                if self.process_health.reported_ready:  # Process alive and ready
                    self.logger.info(
                        "Process {name!r} alive and ready",
                        message_id=LogId.process_alive_and_ready,
                        _color="<green>",
                        **log_kwargs,
                    )
                elif prev_process_health and prev_process_health.reported_ready:  # Process only alive but was ready
                    self.logger.warning(
                        "Process {name!r} alive, stopped being ready",
                        message_id=LogId.process_stopped_being_ready,
                        **log_kwargs,
                    )
                else:  # Process only alive
                    self.logger.info("Process {name!r} alive", message_id=LogId.process_alive, **log_kwargs)
        else:  # Process not alive
            self.logger.warning(
                "Process {name!r} not alive, attempt {attempt}/{max_attempts}",
                attempt=attempt,
                max_attempts=self.config.supervisor_liveness_retries,
                message_id=LogId.process_not_alive,
                **log_kwargs,
            )

        if self.process_health.reported_alive:  # Process alive => continue checking liveness
            if self.process_health.reported_ready:
                self.health.running()  # Respawner becomes RUNNING on the first successful readiness check
            return self._liveness_check, self.config.supervisor_liveness_interval
        elif attempt < self.config.supervisor_liveness_retries:
            return functools.partial(self._liveness_check, attempt + 1), self.config.supervisor_liveness_interval
        else:  # Too many attempts with process not alive result => shutdown (and later respawn) it
            return self._shutdown_process, 0

    def _shutdown_process(self) -> tuple[Callable, float]:
        """Shutdown the process."""
        self.process.shutdown(self.config.supervisor_shutdown_timeout)
        return self._spawn_process, 0


class ChildProcess:
    """Process wrapper which supports respawns (repeated shutdown(), spawn())."""

    def __init__(self, name: str, logger: Logger, popen_args, capture_output: bool):
        self.name = name
        self.logger = logger
        self.popen_args = popen_args
        self.capture_output = capture_output  # Forward stdout/stderr outputs of the child process to the main process
        self._process: Optional[subprocess.Popen] = None

    @property
    def pid(self) -> int:
        """Return PID of the last spawned process; return -1 if none was spawned yet."""
        return self._process.pid if self._process else -1

    def spawn(self) -> None:
        """Spawn a new process (no-op if already running)."""
        if self.is_running():
            return

        kwargs = self.capture_output_kwargs.copy()
        # Spawning subprocess in its own process group is a workaround for a)
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True

        self._process = subprocess.Popen(self.popen_args, **kwargs)
        self.logger.info("Process {name!r} pid: {pid} spawned", message_id=LogId.process_spawned, **self.log_kwargs)

    def is_running(self) -> bool:
        """Return True if the process is running (i.e. it was spawned and it hasn't exited yet)."""
        return self._process is not None and self._process.poll() is None

    def shutdown(self, timeout: float) -> None:
        """Signal to the process to shut down, kill it after timeout (no-op if not running)."""
        if not self.is_running():
            self.logger.warning(
                "Process {name!r} pid: {pid} is already dead, skipping shutdown",
                message_id=LogId.process_already_dead,
                **self.log_kwargs,
            )
            return

        if sys.platform == "win32":
            shutdown_signal = signal.CTRL_BREAK_EVENT  # CTRL_BREAK_EVENT instead of CTRL_C_EVENT due to b) and c)
        else:
            shutdown_signal = signal.SIGTERM

        self._process.send_signal(shutdown_signal)
        self.logger.info(
            "Sent shutdown signal to process {name!r} pid: {pid}",
            message_id=LogId.supervisor_shutdown_signal_sent,
            **self.log_kwargs,
        )

        try:
            self._process.wait(timeout)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self.logger.warning(
                "Process {name!r} pid: {pid} killed after {timeout} s grace period",
                timeout=timeout,
                message_id=LogId.process_killed,
                **self.log_kwargs,
            )
        else:
            self.logger.info(
                "Process {name!r} pid: {pid} gracefully shut down",
                message_id=LogId.process_shutdown,
                **self.log_kwargs,
            )

    @property
    def log_kwargs(self) -> dict[str, Any]:
        """Create common kwargs for log records related to this process."""
        return {"name": self.name, "pid": self.pid}

    @property
    def capture_output_kwargs(self) -> dict[str, Any]:
        """Create kwargs managing capturing of input/output/error streams of the process."""
        return {
            "stdin": subprocess.DEVNULL,
            "stdout": sys.stdout if self.capture_output else subprocess.DEVNULL,
            "stderr": sys.stderr if self.capture_output else subprocess.DEVNULL,
        }


CONFIG_OPTIONS = (
    ConfigOptionsBuilder()
    .common_options("microservice_commons")
    .start_section("Supervisor", 100)
    .option(
        "supervisor_microservices",
        "ataccama.one.aicore.supervisor.microservices",
        list,
        "Defines which microservices are started when the Supervisor is run.",
        default_value=json.dumps(MICROSERVICE_NAMES),
    )
    .option(
        "supervisor_shutdown_timeout",
        "ataccama.one.aicore.supervisor.shutdown-timeout",
        float,
        """When the Supervisor is asked to shut down (for example, by pressing `Ctrl+C`), the service asks the
        microservices to shut down as well. This property defines how much time the microservices have to gracefully
        shut down before they are stopped.""",
        default_value=5,
    )
    .option(
        "supervisor_captured_microservices",
        "ataccama.one.aicore.supervisor.captured-microservices",
        list,
        """A list of microservices whose stdout and stderr streams are forwarded to the respective stdout and stderr
        streams of the Supervisor process for debugging purposes.""",
        default_value="[]",
    )
    .option(
        "supervisor_liveness_start_delay",
        "ataccama.one.aicore.supervisor.liveness.start-delay",
        float,
        """Defines for how long the Supervisor waits after starting a microservice before it starts checking its health
        (a temporary workaround). Expressed in seconds.""",
        default_value=10,
    )
    .option(
        "supervisor_liveness_interval",
        "ataccama.one.aicore.supervisor.liveness.interval",
        float,
        """Determines how often a health check is performed. By default, this is done once every minute. Expressed in
        seconds.""",
        default_value=60,
    )
    .option(
        "supervisor_liveness_retries",
        "ataccama.one.aicore.supervisor.liveness.retries",
        int,
        """Determines how many consecutive health checks need to fail, indicating that the microservice is no longer
        running, before the microservice is restarted.""",
        default_value=3,
    )
    .option(
        "supervisor_liveness_connection_timeout",
        "ataccama.one.aicore.supervisor.liveness.connection-timeout",
        float,
        """When the Supervisor runs a health check, this property controls for how long the Supervisor waits to receive
        data before cancelling the request. If the connection times out, the microservice is considered as no longer
        running. For more information, see the
        [Requests Developer Interface Documentation](https://requests.readthedocs.io/en/master/api/), section about the
        `timeout` parameter.""",
        default_value=5,
    )
    .create_options(lambda builder: server_options(builder, microservice_name="Supervisor", http_port=8040))
    .end_section()
    .options
)
CONFIG_OPTIONS.update(collect_health_check_config_options())

MICROSERVICES = {"supervisor": Supervisor}
