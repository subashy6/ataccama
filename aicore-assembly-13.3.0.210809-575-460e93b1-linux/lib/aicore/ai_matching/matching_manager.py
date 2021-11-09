"""Management and control of individual matching services."""
from __future__ import annotations

import contextlib

from typing import TYPE_CHECKING

import dedupe._typing as dedupe_types

from aicore.ai_matching.constants import MIN_LABELED_PAIRS, MINIMAL_MODEL_QUALITY, SubPhase
from aicore.ai_matching.enums import (
    ComputationState,
    ErrorMessage,
    MatchingDecision,
    MatchingPhase,
    NotEnoughLabeledPairsError,
    Proposal,
    RestartType,
    Status,
    UnknownPairError,
)
from aicore.ai_matching.matching_steps import (
    BlockingStep,
    ClusteringStep,
    ExtractingRulesStep,
    FetchingStep,
    GeneratingProposalsStep,
    InitializationStep,
    ScoringStep,
)
from aicore.ai_matching.registry import AIMatchingMetric, LogId
from aicore.ai_matching.storage import SingleStorage
from aicore.ai_matching.utils.logging import log_info
from aicore.ai_matching.utils.time_bounds import measure_time_bounds
from aicore.common.grpc import GRPCClient
from aicore.common.logging import Logger
from aicore.common.metrics import MetricsDAO
from aicore.common.utils import random_correlation_id


if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Optional

    from aicore.ai_matching.matching_steps import StepBase
    from aicore.ai_matching.types import RecordIdsPair, TrainingPair
    from aicore.common.auth import Identity
    from aicore.common.config import Config
    from aicore.common.types import CorrelationId


# Steps used for computation in each phase
PHASE_TRANSITIONS: dict[MatchingPhase, type[StepBase]] = {
    # MatchingPhase.NOT_CREATED -> INITIALIZING_MATCHING by InitMatching(FromFile)Command
    # Initialization stage
    MatchingPhase.INITIALIZING_MATCHING: InitializationStep,
    # MatchingPhase.TRAINING_MODEL -> FETCHING_RECORDS by EvaluateRecordsMatchingCommand or ExtractRulesCommand
    # Evaluation stage
    MatchingPhase.FETCHING_RECORDS: FetchingStep,
    MatchingPhase.BLOCKING_RECORDS: BlockingStep,
    MatchingPhase.SCORING_PAIRS: ScoringStep,
    MatchingPhase.CLUSTERING_RECORDS: ClusteringStep,
    # Records matching evaluation
    MatchingPhase.GENERATING_PROPOSALS: GeneratingProposalsStep,
    # Rules extraction
    MatchingPhase.EXTRACTING_RULES: ExtractingRulesStep,
    # Other
    # MatchingPhase.READY -> GENERATING_PROPOSALS by EvaluateRecordsMatchingCommand
    # MatchingPhase.READY -> EXTRACTING_RULES by ExtractRulesCommand
    # MatchingPhase.ERROR -> INITIALIZING_MATCHING by RestartMatchingCommand
}


class MatchingManager:
    """Manager for training and control of single AI matching."""

    def __init__(
        self,
        mdc_grpc_client: GRPCClient,
        storage: SingleStorage,
        metrics: MetricsDAO,
        logger: Logger,
        correlation_id: Optional[CorrelationId] = None,
    ):
        self.mdc_grpc_client = mdc_grpc_client
        self.storage = storage
        self.metrics = metrics
        self.logger = logger

        self.storage.last_command_correlation_id = correlation_id or random_correlation_id()

    def log(self, message: str, message_id: LogId, **kwargs):
        """Log info message related to a particular matching id."""
        storage = self.storage
        log_info(
            self.logger,
            message,
            message_id,
            storage.matching_id,
            storage.last_command_correlation_id,
            storage.identity,
            **kwargs,
        )

    @contextlib.contextmanager
    def start_initialization_from_storage(
        self,
        correlation_id: CorrelationId,
        identity: Optional[Identity],
    ) -> Iterator[SingleStorage]:
        """Set up the matching (via storage) and then start the (re)initialization step based on the storage content."""
        # Only correlation id changes every time the matching is (re)initialized
        self.storage.last_command_correlation_id = correlation_id
        self.storage.last_command_identity = identity

        yield self.storage  # The storage can be further modified here before the InitializationStep is actually started

        self.storage.update_model_quality()
        self.change_phase(MatchingPhase.INITIALIZING_MATCHING)
        self.metrics.observe(
            AIMatchingMetric.n_columns,
            len(self.storage.used_columns),
            matching_id=str(self.storage.matching_id),
        )

    @staticmethod
    def computation_state_after_restart(previous_state: ComputationState) -> ComputationState:
        """Plan state if it was planned or finished, keep it not planned otherwise."""
        if previous_state == ComputationState.NOT_PLANNED:
            return ComputationState.NOT_PLANNED
        return ComputationState.PLANNED

    def reinitialize_matching(
        self,
        restart_type: RestartType,
        correlation_id: CorrelationId,
        identity: Identity,
        old_storage: SingleStorage,
    ):
        """Restart the matching process (either just the initialization stage, or the whole process)."""
        storage: SingleStorage
        with self.start_initialization_from_storage(correlation_id, identity) as storage:
            # What settings to transfer from the old storage to the current one (typically freshly created)
            storage.last_command_correlation_id = correlation_id
            storage.used_columns = old_storage.used_columns
            storage.record_id_column = old_storage.record_id_column
            storage.matching_id_column = old_storage.matching_id_column
            storage.data_file_path = old_storage.data_file_path

            if restart_type in [RestartType.RESET_TO_TRAINING, RestartType.RESET_TO_EVALUATION]:
                storage.deduper = old_storage.deduper  # To pass the training pairs, deduper will be replaced

            if restart_type == RestartType.RESET_TO_EVALUATION:
                storage.skip_training_phase = True
                storage.clustering_state = ComputationState.PLANNED
                storage.records_matching_state = self.computation_state_after_restart(
                    old_storage.records_matching_state
                )
                storage.rules_extraction_state = self.computation_state_after_restart(
                    old_storage.rules_extraction_state
                )
                storage.cached_proposals_count = old_storage.cached_proposals_count
                storage.confidence_threshold = old_storage.confidence_threshold
                storage.min_match_confidence = old_storage.min_match_confidence
                storage.min_distinct_confidence = old_storage.min_distinct_confidence
            elif restart_type == RestartType.RESET_ALL:
                pass  # Do not keep anything

        old_storage.active = False  # Mark the old storage as inactive and ready to be deleted

    def start_common_computation(self, correlation_id: CorrelationId, identity: Optional[Identity]):
        """Start computations of the main AI Matching algorithm, leading to clustering of pairs."""
        self.storage.last_command_correlation_id = correlation_id
        self.storage.last_command_identity = identity

        self.check_enough_labeled_pairs()

        self.log(
            "Starting AI Matching computation with status: {status_message}",
            LogId.evaluation_start,
            status_message=self.generate_status_message(),
        )

        self.storage.clustering_state = ComputationState.PLANNED
        # Set training progress to 100% even if model quality is low
        self.storage.set_phase_progress(1.0)
        self.change_phase(MatchingPhase.FETCHING_RECORDS)

    def check_enough_labeled_pairs(self):
        """Check whether there is enough labeled pairs to start the computation, raise an exception if not."""
        n_match = self.storage.get_training_counts(MatchingDecision.MATCH)
        n_distinct = self.storage.get_training_counts(MatchingDecision.DISTINCT)
        required = MIN_LABELED_PAIRS
        if n_match < required or n_distinct < required:
            raise NotEnoughLabeledPairsError(
                self.storage.matching_id,
                f"{required} labeled pairs of each type is required to start the computation, but only "
                f"{n_match} MATCH and {n_distinct} DISTINCT were labeled so far",
                required=required,
                n_match=n_match,
                n_distinct=n_distinct,
            )

    def get_proposal_info(self, pair: RecordIdsPair) -> Proposal:
        """Return info about particular proposal."""
        proposal = self.storage.fetch_proposal_info(pair)

        if not proposal:
            raise UnknownPairError(
                self.storage.matching_id, pair, f"Requested training pair {pair} is unknown / not present"
            )

        return proposal

    def discard_proposal(self, record_pair: RecordIdsPair) -> None:
        """Reject proposal and do not use it for further training. Do nothing if the proposal is not present."""
        discarded_proposal = self.storage.discard_proposal(record_pair)
        if not discarded_proposal:
            raise UnknownPairError(
                self.storage.matching_id,
                record_pair,
                f"Requested pair {record_pair} is unknown / not present and thus cannot be discarded",
            )

    def update_training_data(self, training_pair: TrainingPair) -> None:
        """Update training pairs and the model."""
        _, record_id_column_name = self.storage.record_id_column  # type: ignore
        id1, id2, decision = training_pair
        pair = (id1, id2)

        # Remove the pair with the old decision
        stored_training_pair = self.storage.fetch_training_pair(pair)
        if stored_training_pair:
            _, _, old_decision = stored_training_pair
            self.storage.remove_training_pair(pair, old_decision)

        if decision == MatchingDecision.UNKNOWN:
            return  # The pair with old decision was removed, new is not added

        # Add the pair to the training data, but now with new decision
        try:
            pair_data = self.storage.fetch_training_pair_data(pair)
        except KeyError:
            raise UnknownPairError(
                self.storage.matching_id, pair, f"Pair {pair} is unknown / not present and thus cannot be updated"
            )

        # Retrain the model with new data
        examples = dedupe_types.TrainingData(distinct=[], match=[])
        examples[decision.to_dedupe()].append(pair_data)
        self.storage.deduper.mark_pairs(examples)

        self.storage.update_model_quality()

        if self.storage.phase == MatchingPhase.TRAINING_MODEL:
            self.set_training_progress()

    def set_training_progress(self):
        """Set training progress based on the current model quality."""
        progress = min(self.storage.model_quality / MINIMAL_MODEL_QUALITY, 1.0)
        self.storage.set_phase_progress(progress)

    def generate_status_message(self) -> Status:
        """Generate a status message containing information about the matching."""
        return self.storage.generate_status_message()

    def process(self, config: Config) -> bool:
        """Call methods according to actual phase."""
        if self.want_to_work():
            current_phase = self.storage.phase
            step_class = PHASE_TRANSITIONS[current_phase]
            # Create and evaluate the step for this phase
            try:
                with measure_time_bounds() as time_bounds:
                    # TODO: Step should not know about grpc, metrics or logger  # noqa T101 ONE-21104
                    current_matching_step = step_class(
                        self.storage, self.mdc_grpc_client, self.metrics, self.logger, config
                    )
                    new_phase = current_matching_step()

                self.metrics.set_value(
                    AIMatchingMetric.step_processing_seconds,
                    time_bounds.elapsed_time().seconds,
                    matching_step=str(current_matching_step),
                    matching_id=str(self.storage.matching_id),
                )

                with measure_time_bounds() as time_bounds_metrics:
                    current_matching_step.collect_metrics()

                self.log(
                    "Metrics collection took: {time_spent} time",
                    LogId.metrics_collection,
                    time_spent=time_bounds_metrics.elapsed_time(),
                )

            except Exception as error:
                new_phase = MatchingPhase.ERROR
                message = repr(error)
                self.storage.error_message = ErrorMessage(message, current_phase)
                self.logger.exception(
                    "{matching_id!r}: Error while computing {phase!s} phase: {message}",
                    message_id=LogId.error_in_step,
                    matching_id=self.storage.matching_id,
                    phase=current_phase,
                    message=message,
                    error=error,
                    correlation_id=self.storage.last_command_correlation_id,
                    identity=self.storage.last_command_identity,
                )

            self.change_phase(new_phase)
            return self.want_to_work()

        return False

    def want_to_work(self):
        """Check whether there is work to do."""
        if not self.storage.active:
            return False
        return self.storage.phase in PHASE_TRANSITIONS

    def change_phase(self, new_phase: MatchingPhase):
        """Change the matching phase and restart the phase progress counter."""
        if not self.storage.active:
            self.log(
                "Due to previous restart, old computation related to {matching_id} finished in phase {phase}",
                LogId.old_process_finished,
                phase=self.storage.phase.name,
            )
            return

        self.log(
            "Progressed: {previous_phase} --> {current_phase} (progress: {progress:0.2f}%)",
            LogId.matching_phase_changed,
            previous_phase=self.storage.phase.name,
            current_phase=new_phase.name,
            progress=self.storage.progress * 100,
        )

        self.storage.phase = new_phase
        self.storage.subphase = SubPhase.SUBPHASE_NOT_STARTED.name
        self.storage.phase_progress = 0
