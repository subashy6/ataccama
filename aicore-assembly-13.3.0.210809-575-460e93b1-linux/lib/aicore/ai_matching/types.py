"""In this module we define the basic object types used within the AIMatching module."""
from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import Any, Literal, Optional, Union

    import dedupe.predicates as dedupe_predicates
    import numpy

    from dedupe import _typing as dedupe_types

    from aicore.ai_matching.enums import MatchingDecision, MdcColumnType, Proposal

    RecordId = int  # Unique id for each record
    ClusterId = int  # Id of a cluster the record belongs to (produced by AI matching)
    GroupId = Union[ClusterId, str]  # Id of a group the record belongs to (produced by either AI matching or MDC)
    ColumnName = str  # Name of a column in a DB
    RecordIdsPair = tuple[RecordId, RecordId]  # A pair of records ordered by their record_id (lower first)
    ColumnScores = dict[ColumnName, float]  # How much a column contributes to a proposal matching score
    TrainingPair = tuple[RecordId, RecordId, MatchingDecision]  # Labeled pair of records used for training
    TrainingData = dedupe_types.TrainingData  # dict[DedupeDecision, list[RecordIdsPair]]
    MdcColumn = tuple[MdcColumnType, ColumnName]  # Column in the MDC table
    MdcColumns = Sequence[MdcColumn]  # A sequence of MDC columns
    # A numpy `structured array <https://docs.scipy.org/doc/numpy/user/basics.rec.html>`_ with a dtype of
    # `[('pairs', id_type, 2), ('score', 'f4')]` where dtype is either a str or int, and score is a number between
    # 0 and 1. The 'pairs' column contains pairs of ids of the records compared and the 'score' column should contains
    # the similarity score for that pair of records. It is used in `dedupe.cluster()` method.
    MatchingScores = numpy.ndarray
    RecordData = dict[ColumnName, Any]  # Content of one row from the MDC table (column name: data converted to python)
    Records = dict[RecordId, RecordData]  # Records accessible by their id
    Proposals = dict[RecordIdsPair, Proposal]  # Record pair ids stored as (id_low, id_high) for fixed order in DB
    DedupeDecision = Literal["match", "distinct"]  # Internal dedupe representation of matching decision
    CoverageValue = float  # Rule coverage percentage (with range 0.0 to 1.0) - what percentage of remaining positive
    # pairs does the rule match
    DistanceValue = float  # Distance [0, MAX_DISTANCE] calculated by the distance function
    ThresholdValue = Optional[DistanceValue]  # Match two records if their distance < threshold.
    CoveredPairsCount = int  # Number of positive pairs covered by a rule.
    RecordIdsPairSet = set[RecordIdsPair]  # Set of pairs of records (with their ids).
    # One Blocking Rule from deduper
    BlockingRule = Union[
        dedupe_predicates.StringPredicate, dedupe_predicates.CompoundPredicate, dedupe_predicates.Predicate
    ]
    BlockingRules = list[BlockingRule]  # Learnt Blocking Rules from deduper - Fingerprinter
    DistanceFunction = Callable[[Any, Any], DistanceValue]  # Returns distance [0, MAX_DISTANCE] of two column cells
