"""Microservices (processes or Docker containers) provided by AI matching."""

from __future__ import annotations

import random
import time

from typing import TYPE_CHECKING

import more_itertools
import numpy

from aicore.ai_matching import MATCHING_MANAGER
from aicore.ai_matching.commands import (
    DiscardProposalCommand,
    EvaluateRecordsMatchingCommand,
    ExtractRulesCommand,
    GetBlockingRulesCommand,
    GetExistingTrainingPairsCommand,
    GetProposalCommand,
    GetProposalsCommand,
    GetRuleSuggestionsCommand,
    GetStatusCommand,
    GetStatusesCommand,
    GetTrainingPairCommand,
    InitMatchingCommand,
    InitMatchingFromFileCommand,
    RestartMatchingCommand,
    UpdateTrainingPairCommand,
)
from aicore.ai_matching.enums import InvalidPhaseError, MatchingId, MatchingPhase, UnknownMatchingError
from aicore.ai_matching.matching_manager import MatchingManager
from aicore.ai_matching.registry import AIMatchingMetric, LogId
from aicore.ai_matching.storage import SingleStorage
from aicore.common.constants import RESPONSIVENESS_PERIOD
from aicore.common.microservice import Microservice
from aicore.common.resource import RuntimeState
from aicore.common.utils import datetime_now


if TYPE_CHECKING:
    from typing import Optional

    from aicore.ai_matching.enums import Status
    from aicore.common.auth import Identity
    from aicore.common.resource import Health
    from aicore.common.types import CorrelationId

RANDOM_SEED = 1  # Random seed for the service. However, it will still not be deterministic because of hashing in
# sets / dicts is nondeterministic for security reasons
# use os.environ["PYTHONHASHSEED"] = "1" in case the determinism is desirable for debugging


class MatchingManagerService(Microservice):
    """Manages multiple matching processes through all stages (from initialization and training to final evaluation)."""

    def __init__(self, config):
        super().__init__("matching_manager", config)

        random.seed(RANDOM_SEED)
        numpy.random.seed(RANDOM_SEED)

        # If unsafe, individual managers should not be access directly as this does not raise UnknownMatchingError
        self._matching_managers: dict[MatchingId, MatchingManager] = {}

        self.server = self.grpc_server(
            commands=[
                InitMatchingCommand,
                InitMatchingFromFileCommand,
                RestartMatchingCommand,
                GetTrainingPairCommand,
                GetExistingTrainingPairsCommand,
                UpdateTrainingPairCommand,
                EvaluateRecordsMatchingCommand,
                GetStatusCommand,
                GetStatusesCommand,
                GetProposalCommand,
                GetProposalsCommand,
                DiscardProposalCommand,
                ExtractRulesCommand,
                GetRuleSuggestionsCommand,
                GetBlockingRulesCommand,
            ],
        )

        self.mdc_grpc_client = self.grpc_client("mdc")

        self.wsgi = self.wsgi_server()

        self.current_matching_manager: Optional[MatchingManager] = None  # Currently working matching manager

        self.started = False  # True if the microservice actually stated - used for the background thread below to wait
        # for other resources to be ready (resource waiting for other resource is not supported yet)
        # Thread to run all the work while staying responsive to Commands - waits for self.started to start processing
        self.worker = self.background_thread("matching_worker_thread", self.run_matching_forever, tracks_liveness=False)
        self.metrics.register(AIMatchingMetric)

    def run_matching_forever(self, health: Health):
        """Repeatedly process one phase of a matching manager which wants to work."""
        with self.logger.action(LogId.matching_worker_thread_startup) as action:
            action.start("Matching thread is starting")
            if not self.started:
                resources = {resource.name: str(resource.health) for resource in self.all_resources}
                action.info(
                    "Matching thread is waiting for microservice to start its resources: {resources}",
                    resources=resources,
                )
            while not self.started:  # Wait for the service to start (then the dependencies like MDC DB are ready)
                if health.state != RuntimeState.RUNNING:
                    action.error("Matching thread was stopped before it could start")
                    return  # Thread is shutting down
                time.sleep(RESPONSIVENESS_PERIOD)

            health.alive()
            action.finish("Matching thread is running")

        while health.state == RuntimeState.RUNNING:
            self.progress_one_step()

            health.alive()

    def progress_one_step(self):
        """Perform one step of the currently selected matching manager, select a new one if none was selected."""
        # We prefer the same matching manager to work continuously over multiple steps until is does not want to work
        # anymore to decrease the amount of intermediate results we need to store.
        # Also, we prefer the matching manager which was created earlier to run before a later one to reduce the amount
        # of unfinished matchings running in parallel.
        if self.current_matching_manager is None:
            with self.process_lock:  # Prevent changing matching managers via gRPC command during the selection
                self.current_matching_manager = more_itertools.first_true(
                    self._matching_managers.values(), pred=lambda manager: manager.want_to_work()
                )

        if self.current_matching_manager is None:  # No manager wants to work, sleep for a while
            time.sleep(RESPONSIVENESS_PERIOD)
            return

        # While manager has work to do, allow it to work continuously to limit the amount of unfinished ones
        wants_to_run_again = self.current_matching_manager.process(self.config)
        if not wants_to_run_again:
            self.current_matching_manager = None

    def create_new_matching(
        self,
        matching_id: MatchingId,
        correlation_id: CorrelationId,
        identity: Optional[Identity],
        replace: bool = False,
    ):
        """Create a new matching with its manager and storage. Replacing an old one if `replace` is True."""
        if matching_id in self._matching_managers and not replace:
            raise InvalidPhaseError(
                matching_id,
                "Matching with this ID already exists, thus cannot be initialized "
                "again (use `RestartMatching` if you want to reinitialize it)",
            )

        if not identity or not identity.user_identity_dict:
            self.logger.warning(
                "No user identity was specified for the AI Matching {matching_id!r}",
                message_id=LogId.no_user_identity,
                matching_id=matching_id,
                correlation_id=correlation_id,
            )

        storage = SingleStorage(matching_id, identity)
        storage.model_update_time = datetime_now()
        matching_manager = MatchingManager(self.mdc_grpc_client, storage, self.metrics, self.logger, correlation_id)
        self._matching_managers[matching_id] = matching_manager

        self.metrics.increment(AIMatchingMetric.n_manager_instances)

    def on_start(self):
        """Establish connection to DB."""
        self.started = True

    def get_matching_manager(self, matching_id: MatchingId) -> MatchingManager:
        """Return the matching manager assigned to the particular matching id or raise an error if none exists."""
        manager = self._matching_managers.get(matching_id)
        if manager is None:
            raise UnknownMatchingError(matching_id)
        return manager

    def get_matchings_states(self) -> list[Status]:
        """Return states of all active AI matchings."""
        return [manager.generate_status_message() for manager in self._matching_managers.values()]

    def get_phase_of_matching(self, matching_id: MatchingId) -> MatchingPhase:
        """Return phase of a particular AI matching (NOT_CREATED if the matching does not exist)."""
        manager = self._matching_managers.get(matching_id)
        if manager is None:
            return MatchingPhase.NOT_CREATED

        return manager.storage.phase


MICROSERVICES = {
    MATCHING_MANAGER: MatchingManagerService,
}
