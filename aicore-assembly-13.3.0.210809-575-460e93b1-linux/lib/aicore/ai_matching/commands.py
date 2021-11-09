"""De-/serialization and server-side handling of gRPC commands for AI Matching."""
from __future__ import annotations

import abc

from typing import TYPE_CHECKING

import aicore.ai_matching.proto.ai_matching_pb2 as matching_proto

from aicore.ai_matching.constants import SubPhase
from aicore.ai_matching.enums import (
    AiMatchingError,
    ComputationState,
    InvalidPhaseError,
    MatchingDecision,
    MatchingId,
    MatchingPhase,
    MdcColumnType,
    NoMoreTrainingPairsError,
    NotEnoughLabeledPairsError,
    Proposal,
    ProposalType,
    RestartType,
    Status,
    UnknownMatchingError,
    UnknownPairError,
)
from aicore.ai_matching.registry import AIMatchingMetric, LogId
from aicore.ai_matching.rules_extraction import RulesWithCoverage
from aicore.ai_matching.serialization import (
    blocking_rule_to_proto,
    deserialize,
    proposal_to_proto,
    rule_to_proto,
    status_to_proto,
)
from aicore.ai_matching.utils.logging import log_progress
from aicore.ai_matching.utils.time_bounds import measure_time_bounds
from aicore.common.command import Command, CommandError


if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from typing import Optional

    from aicore.ai_matching.microservices import MatchingManagerService
    from aicore.ai_matching.types import BlockingRule, MdcColumn, RecordData, RecordIdsPair, TrainingPair
    from aicore.common.auth import Identity
    from aicore.common.types import CorrelationId

# Translation of internal AI Matching errors into CommandError reason codes
AI_ERROR_TO_COMMAND_ERROR_REASON: dict[type[AiMatchingError], str] = {
    InvalidPhaseError: "invalid_phase",
    UnknownMatchingError: "unknown_matching_id",
    NoMoreTrainingPairsError: "no_more_training_pairs",
    UnknownPairError: "unknown_pair",
    NotEnoughLabeledPairsError: "not_enough_labeled_pairs",
}


def all_except(*phases: MatchingPhase, **_kwargs) -> tuple[MatchingPhase, ...]:
    """Return all phases except those listed as arguments of the function."""
    allowed: set[MatchingPhase] = set(MatchingPhase) - set(phases)
    return tuple(allowed)


class AIMatchingCommandBase(Command, abc.ABC):
    """A base class for commands connected to a particular matching id which adds handling of AI Matching errors."""

    allowed_in_phases: tuple[
        MatchingPhase, ...
    ] = ()  # Phases of matching in which this command is allowed to be called
    __slots__ = ("matching_id", "error")

    def __init__(self, matching_id: MatchingId):
        self.matching_id = matching_id  # Matching id this command is connected to
        self.error: Optional[AiMatchingError] = None  # The error which was raised during the command processing

    def process(
        self,
        microservice: MatchingManagerService,
        correlation_id: CorrelationId,
        identity: Optional[Identity] = None,
    ) -> None:
        """Process the command and handle all AI Matching related errors which occur during the processing."""
        phase = microservice.get_phase_of_matching(self.matching_id)
        try:
            if not microservice.started:
                resources = {resource.name: str(resource.health) for resource in microservice.all_resources}
                raise InvalidPhaseError(
                    self.matching_id,
                    f"Microservice has not yet fully started and thus cannot accept commands - "
                    f"resources: {resources}",
                    resources=resources,
                )

            if phase not in self.allowed_in_phases:
                if phase == MatchingPhase.NOT_CREATED:
                    raise UnknownMatchingError(self.matching_id)
                else:
                    raise InvalidPhaseError(
                        self.matching_id,
                        f"Command {type(self).__name__} cannot be performed in "
                        f"phase {phase} (allowed only in phases: {self.allowed_in_phases})",
                        command=self,
                        phase=phase,
                        allowed_phases=self.allowed_in_phases,
                    )
            self._process(microservice, correlation_id, identity)

        except AiMatchingError as error:
            self.error = error
            reason_code = AI_ERROR_TO_COMMAND_ERROR_REASON.get(type(error), "unspecified_ai_matching_problem")
            raise CommandError(reason_code, error.message, **error.kwargs) from error

    @abc.abstractmethod
    def _process(self, microservice: MatchingManagerService, correlation_id: CorrelationId, identity: Identity) -> None:
        """Perform the actual processing of the command, AIMatchingErrors raised will be handled and logged."""


class CommandWithStatusBase(AIMatchingCommandBase, abc.ABC):
    """Command which returns a status."""

    __slots__ = (
        "matching_id",
        "error",
        "status",
    )

    def __init__(self, matching_id: MatchingId):
        super().__init__(matching_id)
        self.status: Optional[Status] = None  # Status of the particular AI Matching containing a potential error type

    def process(
        self,
        microservice: MatchingManagerService,
        correlation_id: CorrelationId,
        identity: Optional[Identity] = None,
    ) -> None:
        """Process the command (handling the errors) and then include the error into the status."""
        super().process(microservice, correlation_id, identity)

        try:
            manager = microservice.get_matching_manager(self.matching_id)
            self.status = manager.generate_status_message()
        except UnknownMatchingError:
            self.status = Status.not_created_status(self.matching_id)


class InitMatchingCommand(CommandWithStatusBase):
    """Initialize AI Matching for particular entity and layer."""

    service = "ataccama.aicore.ai_matching.AiMatching"
    method = "InitMatching"
    request_class = matching_proto.InitMatchingRequest
    response_class = matching_proto.InitMatchingResponse
    allowed_in_phases = (MatchingPhase.NOT_CREATED,)
    __slots__ = ("matching_id", "error", "status", "columns", "matching_id_column", "record_id_column")

    def __init__(
        self,
        matching_id: MatchingId,
        columns: list[MdcColumn],
        matching_id_column: MdcColumn,
        record_id_column: MdcColumn,
    ):
        super().__init__(matching_id)
        self.columns = columns
        self.matching_id_column = matching_id_column
        self.record_id_column = record_id_column

    def __repr__(self):
        return (
            f"InitMatchingCommand({self.matching_id}: {self.columns} / {self.matching_id_column} "
            f"/ {self.record_id_column}) -> {self.status}"
        )

    @classmethod
    def deserialize_from_client(cls, request: matching_proto.InitMatchingRequest) -> InitMatchingCommand:
        """Create the command from given protobuf message."""
        columns = [(MdcColumnType(column.type), column.name) for column in request.columns]

        return cls(
            matching_id=MatchingId(request.matching_id.entity_name, request.matching_id.layer_name),
            columns=columns,
            matching_id_column=(MdcColumnType.ID_LONG_TYPE, request.matching_id_column.name),
            record_id_column=(MdcColumnType.ID_LONG_TYPE, request.record_id_column.name),
        )

    def _process(
        self,
        microservice: MatchingManagerService,
        correlation_id: CorrelationId,
        identity: Optional[Identity] = None,
    ) -> None:
        """Set command's state based on results provided by given microservice."""
        microservice.create_new_matching(self.matching_id, correlation_id, identity)

        matching_manager = microservice.get_matching_manager(self.matching_id)
        with matching_manager.start_initialization_from_storage(correlation_id, identity) as storage:
            storage.used_columns = self.columns
            storage.matching_id_column = self.matching_id_column
            storage.record_id_column = self.record_id_column

    def serialize_for_client(self) -> matching_proto.InitMatchingResponse:
        """Create a gRPC response based on the command's results."""
        return self.response_class(status=status_to_proto(self.status))


class InitMatchingFromFileCommand(CommandWithStatusBase):
    """Initialize AI Matching for particular entity and layer."""

    service = "ataccama.aicore.ai_matching.AiMatching"
    method = "InitMatchingFromFile"
    request_class = matching_proto.InitMatchingFromFileRequest
    response_class = matching_proto.InitMatchingFromFileResponse
    allowed_in_phases = (MatchingPhase.NOT_CREATED,)
    __slots__ = (
        "matching_id",
        "error",
        "status",
        "columns",
        "matching_id_column",
        "record_id_column",
        "file_path",
        "dialect",
    )

    def __init__(
        self,
        matching_id: MatchingId,
        columns: list[MdcColumn],
        matching_id_column: MdcColumn,
        record_id_column: MdcColumn,
        file_path: str,
        dialect: str = "csv_semicolon_separated",
    ):
        super().__init__(matching_id)
        self.columns = columns
        self.matching_id_column = matching_id_column
        self.record_id_column = record_id_column
        self.file_path = file_path
        self.dialect = dialect

    def __repr__(self):
        return (
            f"InitMatchingFromFileCommand({self.matching_id}: {self.columns} / {self.matching_id_column} "
            f"/ {self.record_id_column} / {self.file_path} / {self.dialect}) -> {self.status}"
        )

    @classmethod
    def deserialize_from_client(
        cls, request: matching_proto.InitMatchingFromFileRequest
    ) -> InitMatchingFromFileCommand:
        """Create the command from given protobuf message."""
        columns = [(MdcColumnType(column.type), column.name) for column in request.columns]

        return cls(
            matching_id=MatchingId(request.matching_id.entity_name, request.matching_id.layer_name),
            columns=columns,
            matching_id_column=(MdcColumnType.ID_LONG_TYPE, request.matching_id_column.name),
            record_id_column=(MdcColumnType.ID_LONG_TYPE, request.record_id_column.name),
            file_path=request.file_path,
            dialect=request.dialect,
        )

    def _process(
        self,
        microservice: MatchingManagerService,
        correlation_id: CorrelationId,
        identity: Optional[Identity] = None,
    ) -> None:
        """Set command's state based on results provided by given microservice."""
        microservice.create_new_matching(self.matching_id, correlation_id, identity)

        matching_manager = microservice.get_matching_manager(self.matching_id)
        with matching_manager.start_initialization_from_storage(correlation_id, identity) as storage:
            storage.used_columns = self.columns
            storage.matching_id_column = self.matching_id_column
            storage.record_id_column = self.record_id_column
            storage.data_file_path = self.file_path
            storage.dialect = self.dialect

    def serialize_for_client(self) -> matching_proto.InitMatchingFromFileResponse:
        """Create a gRPC response based on the command's results."""
        return self.response_class(status=status_to_proto(self.status))


RESTART_TYPES_ALLOWED_IN: dict[RestartType, tuple[MatchingPhase, ...]] = {
    RestartType.RESET_TO_EVALUATION: all_except(
        MatchingPhase.NOT_CREATED, MatchingPhase.INITIALIZING_MATCHING, MatchingPhase.TRAINING_MODEL
    ),
    RestartType.RESET_TO_TRAINING: all_except(
        MatchingPhase.NOT_CREATED, MatchingPhase.INITIALIZING_MATCHING, MatchingPhase.TRAINING_MODEL
    ),
    RestartType.CLEAR_TRAINING_PAIRS: all_except(MatchingPhase.NOT_CREATED, MatchingPhase.INITIALIZING_MATCHING),
    RestartType.RESET_ALL: all_except(MatchingPhase.NOT_CREATED),
}


class RestartMatchingCommand(CommandWithStatusBase):
    """Restart the matching process (either just the initialization stage, or the whole process)."""

    service = "ataccama.aicore.ai_matching.AiMatching"
    method = "RestartMatching"
    request_class = matching_proto.RestartMatchingRequest
    response_class = matching_proto.RestartMatchingResponse
    # Allowed generally in all phases, depends on the type of restart
    allowed_in_phases = all_except(MatchingPhase.NOT_CREATED)
    __slots__ = ("matching_id", "error", "status", "restart_type")

    def __init__(self, matching_id: MatchingId, restart_type: RestartType):
        super().__init__(matching_id)
        self.restart_type = restart_type

    def __repr__(self):
        return f"RestartMatchingCommand({self.matching_id}, {self.restart_type}) -> {self.status}"

    @classmethod
    def deserialize_from_client(cls, request: matching_proto.RestartMatchingRequest) -> RestartMatchingCommand:
        """Create the command from given protobuf message."""
        return cls(
            matching_id=MatchingId(request.matching_id.entity_name, request.matching_id.layer_name),
            restart_type=RestartType(request.restart_type),
        )

    def _process(
        self,
        microservice: MatchingManagerService,
        correlation_id: CorrelationId,
        identity: Identity,
    ) -> None:
        """Set command's state based on results provided by given microservice."""
        old_matching_manager = microservice.get_matching_manager(self.matching_id)
        current_phase = old_matching_manager.storage.phase
        if current_phase not in RESTART_TYPES_ALLOWED_IN[self.restart_type]:
            raise InvalidPhaseError(
                self.matching_id,
                f"RestartMatching (with type {self.restart_type}) cannot be called in phase: {current_phase})",
                restart_type=self.restart_type,
                current_phase=current_phase,
            )

        if self.restart_type == RestartType.CLEAR_TRAINING_PAIRS:
            old_matching_manager.storage.clear_training()
            microservice.logger.info(
                "{matching_id}: Cleared all training data",
                message_id=LogId.cleared_training_data,
                matching_id=self.matching_id,
                correlation_id=correlation_id,
                identity=identity,
            )
            return

        if self.restart_type == RestartType.RESET_TO_EVALUATION:
            if old_matching_manager.storage.clustering_state == ComputationState.NOT_PLANNED:
                raise InvalidPhaseError(
                    self.matching_id,
                    f"RestartMatching (with type {self.restart_type}) cannot be called before "
                    f"at least one of: records matching or rules extraction was asked for.",
                    restart_type=self.restart_type,
                )

        microservice.create_new_matching(self.matching_id, correlation_id, identity, replace=True)
        new_matching_manager = microservice.get_matching_manager(self.matching_id)
        new_matching_manager.reinitialize_matching(
            self.restart_type, correlation_id, identity, old_matching_manager.storage
        )
        microservice.logger.info(
            "{matching_id}: Matching was restarted - {restart_type!s}",
            message_id=LogId.matching_restarted,
            matching_id=self.matching_id,
            restart_type=self.restart_type,
            correlation_id=correlation_id,
            identity=identity,
        )

    def serialize_for_client(self) -> matching_proto.RestartMatchingResponse:
        """Create a gRPC response based on the command's results."""
        return self.response_class(status=status_to_proto(self.status))


class GetTrainingPairCommand(AIMatchingCommandBase):
    """
    Obtain training pair for user evaluation.

    The same pair is obtained by subsequent calls of this command until the old one is resolved by calling
    UpdateTrainingPairCommand with the correct pair of IDs.
    """

    service = "ataccama.aicore.ai_matching.AiMatching"
    method = "GetTrainingPair"
    request_class = matching_proto.GetTrainingPairRequest
    response_class = matching_proto.GetTrainingPairResponse
    allowed_in_phases = (MatchingPhase.TRAINING_MODEL, MatchingPhase.READY)
    __slots__ = ("matching_id", "error", "training_pair")

    def __init__(self, matching_id: MatchingId):
        super().__init__(matching_id)
        self.training_pair: RecordIdsPair = (-1, -1)

    def __repr__(self):
        return f"GetTrainingPairCommand({self.matching_id}) -> {self.training_pair} / {self.error}"

    @classmethod
    def deserialize_from_client(cls, request: matching_proto.GetTrainingPairRequest) -> GetTrainingPairCommand:
        """Create the command from given protobuf message."""
        return cls(matching_id=MatchingId(request.matching_id.entity_name, request.matching_id.layer_name))

    def _process(
        self,
        microservice: MatchingManagerService,
        _correlation_id: CorrelationId,
        _identity: Identity,
    ) -> None:
        """Set command's state based on results provided by given microservice."""
        matching_manager = microservice.get_matching_manager(self.matching_id)
        matching_manager.storage.prepare_new_training_pair_if_resolved()

        training_pair = matching_manager.storage.prepared_training_pair
        if not training_pair:
            raise NoMoreTrainingPairsError(self.matching_id, "All prepared training candidates were labeled")

        self.training_pair = training_pair

    def serialize_for_client(self) -> matching_proto.GetTrainingPairResponse:
        """Create a gRPC response based on the command's results."""
        response = self.response_class()
        response.pair.id1, response.pair.id2 = self.training_pair
        return response


class GetExistingTrainingPairsCommand(AIMatchingCommandBase):
    """Return information about already labeled training pairs of particular AI matching."""

    service = "ataccama.aicore.ai_matching.AiMatching"
    method = "GetExistingTrainingPairs"
    request_class = matching_proto.GetExistingTrainingPairsRequest
    response_class = matching_proto.GetExistingTrainingPairsResponse
    allowed_in_phases = all_except(MatchingPhase.NOT_CREATED, MatchingPhase.INITIALIZING_MATCHING)
    __slots__ = ("matching_id", "error", "training_pairs")

    def __init__(self, matching_id: MatchingId):
        super().__init__(matching_id)
        self.training_pairs: list[TrainingPair] = []

    def __repr__(self):
        return f"GetExistingTrainingPairsCommand({self.matching_id}) -> {self.training_pairs} / {self.error}"

    @classmethod
    def deserialize_from_client(
        cls, request: matching_proto.GetExistingTrainingPairsRequest
    ) -> GetExistingTrainingPairsCommand:
        """Create the command from given protobuf message."""
        return cls(matching_id=MatchingId(request.matching_id.entity_name, request.matching_id.layer_name))

    def _process(
        self,
        microservice: MatchingManagerService,
        _correlation_id: CorrelationId,
        _identity: Identity,
    ) -> None:
        """Set command's state based on results provided by given microservice."""
        matching_manager = microservice.get_matching_manager(self.matching_id)
        self.training_pairs = matching_manager.storage.fetch_all_training_pairs()

    def serialize_for_client(self) -> matching_proto.GetExistingTrainingPairsResponse:
        """Create a gRPC response based on the command's results."""
        response = self.response_class()

        for training_pair in self.training_pairs:
            proto_pair = response.pairs.add()
            id1, id2, decision_type = training_pair

            proto_pair.pair.id1, proto_pair.pair.id2, proto_pair.decision = (
                id1,
                id2,
                decision_type.value,  # type: ignore
            )

        return response


class UpdateTrainingPairCommand(CommandWithStatusBase):
    """Update AI matching model with evaluated training pair.

    Delete the currently prepared training pair if it is the one being updated.
    """

    service = "ataccama.aicore.ai_matching.AiMatching"
    method = "UpdateTrainingPair"
    request_class = matching_proto.UpdateTrainingPairRequest
    response_class = matching_proto.UpdateTrainingPairResponse
    allowed_in_phases = all_except(
        MatchingPhase.NOT_CREATED,
        MatchingPhase.INITIALIZING_MATCHING,
        MatchingPhase.ERROR,  # Restart first, then update pairs
        MatchingPhase.BLOCKING_RECORDS,  # The training pairs are used here, so cannot be modified
    )

    __slots__ = ("matching_id", "error", "status", "training_pair")

    def __init__(self, matching_id: MatchingId, training_pair: TrainingPair):
        super().__init__(matching_id)
        self.training_pair = training_pair

    def __repr__(self):
        return f"UpdateTrainingPairCommand({self.matching_id}: {self.training_pair}) -> {self.status}"

    @classmethod
    def deserialize_from_client(cls, request: matching_proto.UpdateTrainingPairRequest) -> UpdateTrainingPairCommand:
        """Create the command from given protobuf message."""
        id1 = request.training_pair.pair.id1
        id2 = request.training_pair.pair.id2
        id1, id2 = sorted([id1, id2])
        return cls(
            matching_id=MatchingId(request.matching_id.entity_name, request.matching_id.layer_name),
            training_pair=(
                id1,
                id2,
                MatchingDecision(request.training_pair.decision),
            ),
        )

    def _process(
        self,
        microservice: MatchingManagerService,
        _correlation_id: CorrelationId,
        _identity: Identity,
    ) -> None:
        """Set command's state based on results provided by given microservice."""
        matching_manager = microservice.get_matching_manager(self.matching_id)
        storage = matching_manager.storage
        storage.subphase = matching_manager.update_training_data.__name__
        with measure_time_bounds() as time_bounds:
            matching_manager.update_training_data(self.training_pair)  # Update stored pairs, update model and progress

        log_progress(
            matching_manager.logger,
            storage,
            logger_depth=2,
            elapsed_time=time_bounds.elapsed_time(),
        )

        prepared_pair = matching_manager.storage.prepared_training_pair
        if prepared_pair is not None:
            # Delete prepared training pair if it was the one updated
            training_pair_ids = self.training_pair[:2]  # First two elements are IDs, last is decision
            if prepared_pair == training_pair_ids:
                matching_manager.storage.prepared_training_pair = None

        storage.subphase = SubPhase.SUBPHASE_WAITING_FOR_USER.name

    def serialize_for_client(self) -> matching_proto.UpdateTrainingPairResponse:
        """Create a gRPC response based on the command's results."""
        return self.response_class(status=status_to_proto(self.status))


class EvaluateRecordsMatchingCommand(CommandWithStatusBase):
    """Evaluate current model and prepare proposals for split and merge."""

    service = "ataccama.aicore.ai_matching.AiMatching"
    method = "EvaluateRecordsMatching"
    request_class = matching_proto.EvaluateRecordsMatchingRequest
    response_class = matching_proto.EvaluateRecordsMatchingResponse
    allowed_in_phases = all_except(
        MatchingPhase.NOT_CREATED,
        MatchingPhase.INITIALIZING_MATCHING,
        MatchingPhase.GENERATING_PROPOSALS,
        MatchingPhase.ERROR,
    )

    __slots__ = ("matching_id", "error", "status", "cached_proposals_count", "confidence_threshold")

    def __init__(self, matching_id: MatchingId, cached_proposals_count: int, confidence_threshold: float):
        super().__init__(matching_id)
        # Number of proposals with precomputed score and explainability info to cache
        self.cached_proposals_count = cached_proposals_count
        self.confidence_threshold = confidence_threshold  # Limit for proposal confidence for caching

    def __repr__(self):
        return (
            f"EvaluateCommand({self.matching_id}: {self.cached_proposals_count} / {self.confidence_threshold})"
            f" -> {self.status}"
        )

    @classmethod
    def deserialize_from_client(
        cls, request: matching_proto.EvaluateRecordsMatchingRequest
    ) -> EvaluateRecordsMatchingCommand:
        """Create the command from given protobuf message."""
        return cls(
            matching_id=MatchingId(request.matching_id.entity_name, request.matching_id.layer_name),
            cached_proposals_count=request.cached_proposals_count,
            confidence_threshold=request.confidence_threshold,
        )

    def _process(self, microservice: MatchingManagerService, correlation_id: CorrelationId, identity: Identity) -> None:
        """Set command's state based on results provided by given microservice."""
        matching_manager = microservice.get_matching_manager(self.matching_id)

        storage = matching_manager.storage
        state = storage.records_matching_state.name
        if storage.records_matching_state != ComputationState.NOT_PLANNED:
            raise InvalidPhaseError(
                self.matching_id, message=f"Trying to plan records matching, but it is already: {state}", state=state
            )

        storage.cached_proposals_count = self.cached_proposals_count
        storage.confidence_threshold = self.confidence_threshold

        if storage.phase == MatchingPhase.TRAINING_MODEL:
            matching_manager.start_common_computation(correlation_id, identity)
        elif storage.phase == MatchingPhase.READY:
            matching_manager.change_phase(MatchingPhase.GENERATING_PROPOSALS)
        # In other phases do nothing except planning of the records matching computation
        storage.records_matching_state = ComputationState.PLANNED

        microservice.metrics.increment(
            AIMatchingMetric.n_evaluate_records_matching_command_calls, 1, matching_id=str(storage.matching_id)
        )

    def serialize_for_client(self) -> matching_proto.EvaluateRecordsMatchingResponse:
        """Create a gRPC response based on the command's results."""
        return self.response_class(status=status_to_proto(self.status))


class ExtractRulesCommand(CommandWithStatusBase):
    """Extract decision rules after scoring blocked pairs."""

    service = "ataccama.aicore.ai_matching.AiMatching"
    method = "ExtractRules"
    request_class = matching_proto.ExtractRulesRequest
    response_class = matching_proto.ExtractRulesResponse
    allowed_in_phases = all_except(
        MatchingPhase.NOT_CREATED,
        MatchingPhase.INITIALIZING_MATCHING,
        MatchingPhase.EXTRACTING_RULES,
        MatchingPhase.ERROR,
    )

    __slots__ = (
        "matching_id",
        "error",
        "status",
        "min_match_confidence",
        "min_distinct_confidence",
    )

    def __init__(self, matching_id: MatchingId, min_match_confidence: float, min_distinct_confidence: float):
        super().__init__(matching_id)

        self.min_match_confidence = min_match_confidence  # Min. confidence to use a positive pair in rules extraction
        self.min_distinct_confidence = min_distinct_confidence  # Min. conf. to use a negative pair in rules extraction

    def __repr__(self):
        return (
            f"ExtractRulesCommand({self.matching_id}: {self.min_match_confidence} / {self.min_distinct_confidence}) "
            f"-> {self.status}"
        )

    @classmethod
    def deserialize_from_client(cls, request: matching_proto.ExtractRulesRequest) -> ExtractRulesCommand:
        """Create the command from given protobuf message."""
        return cls(
            matching_id=MatchingId(request.matching_id.entity_name, request.matching_id.layer_name),
            min_match_confidence=request.min_match_confidence,
            min_distinct_confidence=request.min_distinct_confidence,
        )

    def _process(self, microservice: MatchingManagerService, correlation_id: CorrelationId, identity: Identity) -> None:
        """Set command's state based on results provided by given microservice."""
        matching_manager = microservice.get_matching_manager(self.matching_id)

        storage = matching_manager.storage
        if storage.rules_extraction_state != ComputationState.NOT_PLANNED:
            state = storage.rules_extraction_state.name
            raise InvalidPhaseError(
                self.matching_id, message=f"Trying to plan rules extraction, but it is already: {state}", state=state
            )

        storage.min_match_confidence = self.min_match_confidence
        storage.min_distinct_confidence = self.min_distinct_confidence

        if storage.phase == MatchingPhase.TRAINING_MODEL:
            matching_manager.start_common_computation(correlation_id, identity)
        elif storage.phase == MatchingPhase.READY:
            matching_manager.change_phase(MatchingPhase.EXTRACTING_RULES)
        # In other phases do nothing except planning of the rules extraction computation
        storage.rules_extraction_state = ComputationState.PLANNED

        microservice.metrics.increment(
            AIMatchingMetric.n_extract_rules_command_calls, 1, matching_id=str(storage.matching_id)
        )

    def serialize_for_client(self) -> matching_proto.ExtractRulesResponse:
        """Create a gRPC response based on the command's results."""
        return self.response_class(status=status_to_proto(self.status))


class GetRuleSuggestionsCommand(AIMatchingCommandBase):
    """Get all decision rules that were extracted by the model."""

    service = "ataccama.aicore.ai_matching.AiMatching"
    method = "GetRuleSuggestions"
    request_class = matching_proto.GetRuleSuggestionsRequest
    response_class = matching_proto.GetRuleSuggestionsResponse
    # There are no suggestions in other phases
    allowed_in_phases = (MatchingPhase.READY, MatchingPhase.GENERATING_PROPOSALS, MatchingPhase.ERROR)

    __slots__ = ("matching_id", "error", "rules", "columns")

    def __init__(self, matching_id: MatchingId):
        super().__init__(matching_id)

        self.rules: Optional[RulesWithCoverage] = None  # Extracted rules and their statistics
        self.columns: Optional[list[MdcColumn]] = None  # Columns used for matching

    def __repr__(self):
        return f"GetRuleSuggestionsCommand({self.matching_id}) -> {self.rules}"

    @classmethod
    def deserialize_from_client(cls, request: matching_proto.GetRuleSuggestionsRequest) -> GetRuleSuggestionsCommand:
        """Create the command from given protobuf message."""
        return cls(
            matching_id=MatchingId(request.matching_id.entity_name, request.matching_id.layer_name),
        )

    def _process(
        self, microservice: MatchingManagerService, _correlation_id: CorrelationId, _identity: Identity
    ) -> None:
        """Set command's state based on results provided by given microservice."""
        matching_manager = microservice.get_matching_manager(self.matching_id)
        state = matching_manager.storage.rules_extraction_state
        if state != ComputationState.FINISHED:
            raise InvalidPhaseError(
                self.matching_id,
                f"Rule suggestions are not yet computed (extract rules is in state: {state})",
                state=state,
            )
        self.rules = matching_manager.storage.extracted_rules
        self.columns = matching_manager.storage.used_columns

    def serialize_for_client(self) -> matching_proto.GetRuleSuggestionsResponse:
        """Create a gRPC response based on the command's results."""
        rules_proto = []
        for rule_with_statistics in self.rules.rules:
            rule_proto = rule_to_proto(rule_with_statistics.rule, self.columns)
            rule_suggestion = matching_proto.RuleSuggestion(rule=rule_proto)
            rule_suggestion.statistics.covered_positive_cases = rule_with_statistics.covered_positive_cases
            rules_proto.append(rule_suggestion)

        return self.response_class(rule_suggestions=rules_proto)


class GetBlockingRulesCommand(AIMatchingCommandBase):
    """Get learnt Blocking Rules that were used to group records that were fed to an instance of AI matching."""

    service = "ataccama.aicore.ai_matching.AiMatching"
    method = "GetBlockingRules"
    request_class = matching_proto.GetBlockingRulesRequest
    response_class = matching_proto.GetBlockingRulesResponse
    allowed_in_phases = (
        MatchingPhase.SCORING_PAIRS,
        MatchingPhase.CLUSTERING_RECORDS,
        MatchingPhase.GENERATING_PROPOSALS,
        MatchingPhase.EXTRACTING_RULES,
        MatchingPhase.READY,
        MatchingPhase.ERROR,
    )

    __slots__ = ("matching_id", "error", "blocking_rules")

    def __init__(self, matching_id: MatchingId):
        super().__init__(matching_id)

        self.blocking_rules: Optional[list[BlockingRule]] = None  # Learnt Predicates from dedupe

    def __repr__(self):
        return f"GetBlockingRulesCommand({self.matching_id}) -> {self.blocking_rules}"

    @classmethod
    def deserialize_from_client(cls, request: matching_proto.GetBlockingRulesRequest) -> GetBlockingRulesCommand:
        """Create the command from given protobuf message."""
        return cls(matching_id=MatchingId(request.matching_id.entity_name, request.matching_id.layer_name))

    def _process(
        self,
        microservice: MatchingManagerService,
        _correlation_id: CorrelationId,
        _identity: Identity,
    ) -> None:
        """Set command's state based on results provided by given microservice."""
        matching_manager = microservice.get_matching_manager(self.matching_id)
        self.blocking_rules = list(matching_manager.storage.get_blocking_rules())

    def serialize_for_client(self) -> matching_proto.GetBlockingRulesResponse:
        """Create a gRPC response based on the command's results."""
        blocking_rules_proto = [blocking_rule_to_proto(rule) for rule in self.blocking_rules]
        return self.response_class(blocking_rules=blocking_rules_proto)


class GetStatusCommand(CommandWithStatusBase):
    """Get status information about particular AI matching."""

    service = "ataccama.aicore.ai_matching.AiMatching"
    method = "GetStatus"
    request_class = matching_proto.GetStatusRequest
    response_class = matching_proto.GetStatusResponse
    allowed_in_phases = all_except(MatchingPhase.NOT_CREATED)
    enable_logging = False  # Disable logging for GetStatus like commands so as to not spam the logs.

    __slots__ = ("matching_id", "error", "status")

    def __repr__(self):
        return f"GetStatusCommand({self.matching_id}) -> {self.status}"

    @classmethod
    def deserialize_from_client(cls, request: matching_proto.GetStatusRequest) -> GetStatusCommand:
        """Create the command from given protobuf message."""
        return cls(matching_id=MatchingId(request.matching_id.entity_name, request.matching_id.layer_name))

    def _process(
        self,
        microservice: MatchingManagerService,
        _correlation_id: CorrelationId,
        _identity: Identity,
    ) -> None:
        """Set command's state based on results provided by given microservice."""
        pass  # Status is automatically extracted by the CommandWithStatusBase base class process()

    def serialize_for_client(self) -> matching_proto.GetStatusResponse:
        """Create a gRPC response based on the command's results."""
        return self.response_class(status=status_to_proto(self.status))


class GetStatusesCommand(Command):
    """Get status information about all active AI matchings."""

    service = "ataccama.aicore.ai_matching.AiMatching"
    method = "GetStatuses"
    request_class = matching_proto.GetStatusesRequest
    response_class = matching_proto.GetStatusesResponse
    enable_logging = False  # Disable logging for GetStatus like commands so as to not spam the logs.

    __slots__ = ("states",)

    def __init__(self):
        self.states: list[Status] = []

    def __repr__(self):
        return f"GetStatusesCommand() -> {self.states}"

    @classmethod
    def deserialize_from_client(cls, request: matching_proto.GetStatusesRequest) -> GetStatusesCommand:
        """Create the command from given protobuf message."""
        return cls()

    def process(
        self,
        microservice: MatchingManagerService,
        _correlation_id: CorrelationId,
        _identity: Optional[Identity] = None,
    ) -> None:
        """Set command's state based on results provided by given microservice."""
        self.states = microservice.get_matchings_states()

    def serialize_for_client(self) -> matching_proto.GetStatusesResponse:
        """Create a gRPC response based on the command's results."""
        response = self.response_class()

        for state in self.states:
            response.matching_states.append(status_to_proto(state))

        return response


class GetProposalCommand(AIMatchingCommandBase):
    """Return information about particular proposal."""

    service = "ataccama.aicore.ai_matching.AiMatching"
    method = "GetProposal"
    request_class = matching_proto.GetProposalRequest
    response_class = matching_proto.GetProposalResponse
    # There are no proposals in other phases
    allowed_in_phases = (MatchingPhase.READY, MatchingPhase.EXTRACTING_RULES, MatchingPhase.ERROR)
    __slots__ = ("matching_id", "error", "pair", "proposal")

    def __init__(self, matching_id: MatchingId, pair: RecordIdsPair):
        super().__init__(matching_id)
        self.pair = pair

        self.proposal: Optional[Proposal] = Proposal(-1, -1, 0, ProposalType.ALL)

    def __repr__(self):
        return f"GetProposalCommand({self.matching_id}: {self.pair}) -> {self.proposal} / {self.error}"

    @classmethod
    def deserialize_from_client(cls, request: matching_proto.GetProposalRequest) -> GetProposalCommand:
        """Create the command from given protobuf message."""
        id1, id2 = sorted([request.pair.id1, request.pair.id2])
        return cls(
            matching_id=MatchingId(request.matching_id.entity_name, request.matching_id.layer_name),
            pair=(id1, id2),
        )

    def _process(
        self,
        microservice: MatchingManagerService,
        _correlation_id: CorrelationId,
        _identity: Identity,
    ) -> None:
        """Set command's state based on results provided by given microservice."""
        matching_manager = microservice.get_matching_manager(self.matching_id)
        state = matching_manager.storage.records_matching_state
        if state != ComputationState.FINISHED:
            raise InvalidPhaseError(
                self.matching_id,
                f"Records matching proposals are not yet computed " f"(evaluate records matching is in state: {state})",
                state=state,
            )
        self.proposal = matching_manager.get_proposal_info(self.pair)

    def serialize_for_client(self) -> matching_proto.GetProposalResponse:
        """Create a gRPC response based on the command's results."""
        response = self.response_class(proposal=proposal_to_proto(self.proposal))
        return response


class GetProposalsCommand(AIMatchingCommandBase):
    """Return prepared AI matching proposals."""

    service = "ataccama.aicore.ai_matching.AiMatching"
    method = "GetProposals"
    request_class = matching_proto.GetProposalsRequest
    response_class = matching_proto.GetProposalsResponse
    # There are no proposals in other phases
    allowed_in_phases = (MatchingPhase.READY, MatchingPhase.EXTRACTING_RULES, MatchingPhase.ERROR)

    __slots__ = ("matching_id", "error", "proposals_count", "confidence_threshold", "decision", "proposals")

    def __init__(
        self, matching_id: MatchingId, proposals_count: int, confidence_threshold: float, decision: ProposalType
    ):
        super().__init__(matching_id)
        self.proposals_count = proposals_count  # maximal number of proposals of each type to return
        self.confidence_threshold = confidence_threshold  # minimal confidence level for returned proposals
        self.decision = decision  # type of proposals to return

        self.proposals: list[Proposal] = []

    def __repr__(self):
        return (
            f"GetProposalsCommand({self.matching_id}: {self.proposals_count} / {self.confidence_threshold} "
            f"/ {self.decision}) -> {self.proposals} / {self.error}"
        )

    @classmethod
    def deserialize_from_client(cls, request: matching_proto.GetProposalsRequest) -> GetProposalsCommand:
        """Create the command from given protobuf message."""
        return cls(
            matching_id=MatchingId(request.matching_id.entity_name, request.matching_id.layer_name),
            proposals_count=request.proposals_count,
            confidence_threshold=request.confidence_threshold,
            decision=ProposalType(request.decision),
        )

    def _process(
        self,
        microservice: MatchingManagerService,
        _correlation_id: CorrelationId,
        _identity: Identity,
    ) -> None:
        """Set command's state based on results provided by given microservice."""
        matching_manager = microservice.get_matching_manager(self.matching_id)
        state = matching_manager.storage.records_matching_state
        if state != ComputationState.FINISHED:
            raise InvalidPhaseError(
                self.matching_id,
                f"Records matching proposals are not yet computed " f"(evaluate records matching is in state: {state})",
                state=state,
            )
        self.proposals = matching_manager.storage.get_proposals(
            self.confidence_threshold, self.decision, self.proposals_count
        )

    def serialize_for_client(self) -> matching_proto.GetProposalsResponse:
        """Create a gRPC response based on the command's results."""
        response = self.response_class()

        for proposal in self.proposals:
            response.proposals.append(proposal_to_proto(proposal))

        return response


class DiscardProposalCommand(CommandWithStatusBase):
    """Reject a proposal and do not use it for training."""

    service = "ataccama.aicore.ai_matching.AiMatching"
    method = "DiscardProposal"
    request_class = matching_proto.DiscardProposalRequest
    response_class = matching_proto.DiscardProposalResponse
    # There are no proposals in other phases
    allowed_in_phases = (MatchingPhase.READY, MatchingPhase.EXTRACTING_RULES, MatchingPhase.ERROR)

    __slots__ = ("matching_id", "error", "status", "pair")

    def __init__(self, matching_id: MatchingId, pair: RecordIdsPair):
        super().__init__(matching_id)
        self.pair = pair

    def __repr__(self):
        return f"DiscardProposalCommand({self.matching_id}: {self.pair}) -> {self.status}"

    @classmethod
    def deserialize_from_client(cls, request: matching_proto.DiscardProposalRequest) -> DiscardProposalCommand:
        """Create the command from given protobuf message."""
        id1, id2 = sorted([request.pair.id1, request.pair.id2])
        return cls(
            matching_id=MatchingId(request.matching_id.entity_name, request.matching_id.layer_name),
            pair=(id1, id2),
        )

    def _process(
        self,
        microservice: MatchingManagerService,
        _correlation_id: CorrelationId,
        _identity: Identity,
    ) -> None:
        """Set command's state based on results provided by given microservice."""
        matching_manager = microservice.get_matching_manager(self.matching_id)
        state = matching_manager.storage.records_matching_state
        if state != ComputationState.FINISHED:
            raise InvalidPhaseError(
                self.matching_id,
                f"Records matching proposals are not yet computed " f"(evaluate records matching is in state: {state})",
                state=state,
            )
        matching_manager.discard_proposal(self.pair)

    def serialize_for_client(self) -> matching_proto.DiscardProposalResponse:
        """Create a gRPC response based on the command's results."""
        return self.response_class(status=status_to_proto(self.status))


# --------------------------------------------------------------------------------------------
# -------  Requests from AI Matching to MDC
# --------------------------------------------------------------------------------------------

NOT_SORTED = ""  # Empty sort column name means that we do not require the records from MDM to be sorted


class AiMatchingDataCommand(Command):
    """Fetch stream of records from MDC optionally sorted by a specific column."""

    service = "ataccama.aicore.ai_matching.AiMatchingDataConnectService"
    method = "AiMatchingData"
    method_type = "unary_stream"  # Response is a stream of encoded record rows
    request_class = matching_proto.AiMatchingDataRequest
    response_class = matching_proto.ProvideDataResponse
    __slots__ = ("master_layer", "name", "columns", "sort_column", "data_records")

    def __init__(self, master_layer: str, name: str, columns: list[MdcColumn], sort_column: str = NOT_SORTED):
        self.master_layer = master_layer
        self.name = name
        self.columns = columns
        self.sort_column = sort_column

        self.data_records: Optional[Iterator[RecordData]] = None

    def __repr__(self):
        return f"AiMatchingDataCommand - {self.master_layer} / {self.name} / {self.sort_column}"

    def serialize_for_server(self) -> matching_proto.AiMatchingDataRequest:
        """Create a gRPC request based on the command's state."""
        request = self.request_class()
        request.master_layer = self.master_layer
        request.name = self.name
        request.sort_column = self.sort_column

        for column in self.columns:
            proto_column = request.columns.add()
            column_type, name = column
            if column_type == MdcColumnType.ID_LONG_TYPE:
                column_type = MdcColumnType.LONG  # MDC requires LONG as type of ID columns

            proto_column.type, proto_column.name = column_type.value, name  # type: ignore

        return request

    def deserialize_from_server(self, response: Iterable[matching_proto.ProvideDataResponse]):
        """Set command's state based on protobuf response message."""
        # Convert internal id types to correct MDC types we expect to receive
        columns_corrected_types = []
        for column in self.columns:
            internal_type, name = column
            mdc_type = MdcColumnType.LONG if internal_type == MdcColumnType.ID_LONG_TYPE else internal_type
            columns_corrected_types.append((mdc_type, name))
        self.data_records = deserialize(columns_corrected_types, response)
