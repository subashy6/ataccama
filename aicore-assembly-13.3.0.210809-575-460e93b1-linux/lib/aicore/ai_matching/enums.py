"""Definitions of the basic objects and enums used within the AIMatching module."""
from __future__ import annotations

import abc
import dataclasses
import enum

from typing import TYPE_CHECKING

from aicore.common.exceptions import AICoreException
from aicore.common.utils import datetime_now


if TYPE_CHECKING:
    import datetime

    from collections.abc import Sequence
    from typing import Optional

    from aicore.ai_matching.types import ColumnName, ColumnScores, DedupeDecision, RecordId, RecordIdsPair


class MatchingPhase(enum.Enum):
    """Phases in which an AI matching can be found - needs to be kept in sync with gRPC enum MatchingPhase."""

    # Initialization
    NOT_CREATED = 0  # The matching is non-existing, was never created
    INITIALIZING_MATCHING = 1  # In the process of initialization
    TRAINING_MODEL = 2  # Initialized, waiting for users to provide training pairs

    # Common computation
    FETCHING_RECORDS = 3  # All records data are being fetched from MDM or from a file
    BLOCKING_RECORDS = 4  # Records are being blocked by blocking rules
    SCORING_PAIRS = 5  # Similarity of candidate pairs prefiltered by blocking rules is being computed
    CLUSTERING_RECORDS = 6  # Records are being clustered into groups (matched) based on the similarity

    # Records matching
    GENERATING_PROPOSALS = 7  # Matching produced by the previous phase is compared to a ground truth from MDM

    # Extracting rules
    EXTRACTING_RULES = 8  # Rules are extracted based on the results from CLUSTERING_RECORDS

    # Waiting for the user to fetch results or plan other computation
    READY = 9  # Matching proposals generating and/or rules extraction finished and the results can be asked for

    ERROR = 10  # A critical error occurred which prevents the matching to continue, it will need to be restarted. The
    # related error message is contained in the Status about the matching.


class ComputationState(enum.Enum):
    """
    Computation Plan state - needs to be kept in sync with gRPC enum `ComputationState`.

    Included as part of the status message that can be asked for anytime
    """

    NOT_PLANNED = 0  # Computation of the specific result has not yet been planned
    PLANNED = 1  # Computation of the specific result was planned and might already started, but has not finished
    FINISHED = 2  # Computation of the specific result finished and the results can be asked for


class ProposalType(enum.Enum):
    """Type of a proposal - needs to be kept in sync with gRPC enum."""

    ALL = 0  # Any type
    MERGE = 1  # Proposal for merging two records
    SPLIT = 2  # Proposal for splitting two records in one master group


class MatchingDecisionConversionError(AICoreException):
    """There is no equivalent for this matching decision in dedupe."""


class MatchingDecision(enum.Enum):
    """Type of training pair - needs to be kept in sync with gRPC enum."""

    UNKNOWN = 0
    MATCH = 1
    DISTINCT = 2

    def to_dedupe(self) -> DedupeDecision:
        """Return a dedupe key for the decision."""
        if self == MatchingDecision.MATCH:
            return "match"
        elif self == MatchingDecision.DISTINCT:
            return "distinct"
        raise MatchingDecisionConversionError(f"There is no dedupe equivalent of {self} in dedupe")


class RestartType(enum.Enum):
    """Type of the restart command - needs to be kept in sync with gRPC enum RestartType."""

    # Keep training pairs, reinitialize the matching and then immediately continue to the FETCHING_RECORDS phase
    # as if  EvaluateRecordsMatching() or ExtractRules() was called. I.e., skip the MODEL_TRAINING phase
    RESET_TO_EVALUATION = 0
    RESET_TO_TRAINING = 1  # Reinitialize the matching process, keep training pairs
    CLEAR_TRAINING_PAIRS = 2  # Delete all training pairs, do not reinitialize matching process
    RESET_ALL = 3  # Reinitialize matching and delete all training pairs (= CLEAR_TRAINING_PAIRS + RESET_TO_TRAINING)


class MdcColumnType(enum.Enum):
    """Definition of a type of MDC columns - needs to be kept in sync with gRPC enum."""

    ID_LONG_TYPE = -1  # Internal type for ID columns, is send and received as LONG when communicating with MDC
    STRING = 0
    INTEGER = 1
    DAY = 2
    BOOLEAN = 3
    LONG = 4
    DATETIME = 5
    FLOAT = 6


@dataclasses.dataclass(frozen=True)
class MatchingId:
    """Matching identifier."""

    entity_name: str  # name of the entity (e.g. 'person' or 'organisation')
    layer_name: str  # name of the matching layer (e.g. 'norm')

    def __repr__(self):
        return f"Matching[{self.entity_name}+{self.layer_name}]"


@dataclasses.dataclass
class ErrorMessage:
    """Contains information about a critical error which occurred during the background computation."""

    message: str  # The raised exception converted to a human readable string
    phase: MatchingPhase  # Phase in which the computation failed


class Proposal:
    """AI matching proposal."""

    def __init__(
        self,
        id1: RecordId,
        id2: RecordId,
        confidence: float,
        decision: ProposalType,
        key_columns: Sequence[ColumnName] = (),
        column_scores: Optional[ColumnScores] = None,
    ):
        self.id1 = id1
        self.id2 = id2
        self.confidence = confidence  # matching confidence, value in [0, 1]
        self.decision = decision  # use only MERGE/SPLIT enum values
        self.key_columns = key_columns  # column names used for blocking (key rules) in MERGE proposals
        self.column_scores = column_scores  # map of column names and their value addition to the classification

    def add_explanation(self, key_columns: list[ColumnName], column_scores: ColumnScores):
        """Add explanation to the proposal."""
        self.key_columns = key_columns
        self.column_scores = column_scores

    def __eq__(self, other):
        """Check if two proposals are equal."""
        if not isinstance(other, Proposal):
            return False

        return (
            self.id1 == other.id1
            and self.id2 == other.id2
            and self.decision == other.decision
            and self.confidence == other.confidence
        )

    def __repr__(self):
        return f"[Proposal]: ({self.id1},{self.id2}) [{self.decision} /{self.confidence}]"


class AiMatchingError(AICoreException, abc.ABC):
    """An abstract base class for errors raised within AI Matching code during a processing of command.

    These errors are related to the processing of the commands on the foreground thread, in contrast to the
    Status.error_message, which is related to the computation steps happening in the background thread.
    """

    def __init__(self, matching_id: MatchingId, message: str = "", **kwargs):
        message_with_prefix = f"{matching_id}: {message}"
        super().__init__(message_with_prefix)
        self.matching_id = matching_id
        self.message = message_with_prefix
        self.kwargs = kwargs


class InvalidPhaseError(AiMatchingError):
    """Command called in an invalid phase of the matching."""


class UnknownMatchingError(AiMatchingError):
    """Requested matching id was not initialized yet."""

    def __init__(self, matching_id: MatchingId):
        message = f"Matching with ID {repr(matching_id)} does not exist"
        super().__init__(matching_id, message)


class NoMoreTrainingPairsError(AiMatchingError):
    """All prepared training candidates were labeled, need resampling."""


class UnknownPairError(AiMatchingError):
    """Requested training pair is unknown / not present."""

    def __init__(self, matching_id: MatchingId, pair: RecordIdsPair, message: str):
        super().__init__(matching_id, message, pair=pair)


class InvalidStateError(AiMatchingError):
    """Matching got into an invalid state it cannot recover from."""


class NotEnoughLabeledPairsError(AiMatchingError):
    """There is not enough labeled pairs to start the evaluation."""


class ParsingError(AICoreException):
    """Record data cannot be parsed."""


@dataclasses.dataclass
class RecordsMatchingStatus:
    """AI Matching status information - python counterpart for gRPC message `RecordsMatchingStatus`."""

    state: ComputationState  # State of records matching computation
    merge_proposals_count: int  # Total number of merge proposals
    split_proposals_count: int  # Total number of merge proposals
    cached_proposals_count: int  # Maximal number of cached proposals with precomputed score and explainability
    confidence_threshold: float  # Minimal confidence of proposals to be cached


@dataclasses.dataclass
class RulesExtractionStatus:
    """Decision Rule Extraction status information - python counterpart for gRPC message `RuleExtractionStatus`."""

    state: ComputationState
    rules_extracted_count: int  # Number of extracted rules
    min_match_confidence: float  # Minimal confidence of MATCH pairs used as input to rules extraction
    min_distinct_confidence: float  # Minimal confidence of DISTINCT pairs used as input to rules extraction


@dataclasses.dataclass()
class Status:
    """Status of one matching."""

    matching_id: MatchingId  # Matching this status relates to
    phase: MatchingPhase  # Current phase of the computation
    progress: float  # Progress of the whole matching in [0, 1]
    model_update_time: datetime.datetime  # Time when was the matching created or when were data from MDM last updated
    model_quality: float  # Estimated model quality from [0, 1] based on number of labeled pairs
    match_training_pairs_count: int  # Number of training pairs labeled by users as MATCH so far
    distinct_training_pairs_count: int  # Number of training pairs labeled by users as DISTINCT so far
    used_columns_count: int  # Number of columns used in the matching
    clustering_state: ComputationState  # Information about the state of the common part of the computation, i.e.
    # FETCHING_RECORDS, BLOCKING_RECORDS, SCORING_PAIRS, CLUSTERING_RECORDS
    records_matching_status: RecordsMatchingStatus  # Information about the Records matching computation
    rules_extraction_status: RulesExtractionStatus  # Information about the Rules extraction computation
    error: Optional[ErrorMessage]  # Contains information about the error in case phase == ERROR

    @classmethod
    def not_created_status(cls, matching_id: MatchingId) -> Status:
        """Status of a matching which was not yet created."""
        status = Status(
            matching_id,
            phase=MatchingPhase.NOT_CREATED,
            progress=0.0,
            model_update_time=datetime_now(),
            model_quality=0.0,
            match_training_pairs_count=0,
            distinct_training_pairs_count=0,
            used_columns_count=0,
            clustering_state=ComputationState.NOT_PLANNED,
            records_matching_status=RecordsMatchingStatus(ComputationState.NOT_PLANNED, 0, 0, 0, 0),
            rules_extraction_status=RulesExtractionStatus(ComputationState.NOT_PLANNED, 0, 0, 0),
            error=None,
        )
        return status
