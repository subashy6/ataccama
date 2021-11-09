"""Abbreviations for commonly used types."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:  # Avoid polluting the namespace by annotation-only symbols
    import collections.abc

    from typing import Any, Iterator

    from aicore.common.types import EntityId

    AttributeId = EntityId  # Id of an attribute
    TermId = EntityId  # Id on a term
    Suggestion = tuple[TermId, float]  # Suggested term and its confidence
    Suggestions = list[Suggestion]  # All suggested terms for one attribute and their confidences
    TermAssignments = dict[AttributeId, set[TermId]]  # Terms assigned to attributes
    Neighbor = tuple[AttributeId, float]  # Attribute with its distance
    Neighbors = list[Neighbor]  # Neighbors for one attribute
    Thresholds = dict[TermId, float]  # Thresholds assigned to each term
    LearningStrategies = dict[TermId, bool]  # True if adaptive learning is enabled, False if disabled, for each term
    Feedbacks = list[tuple[TermId, bool]]  # Positive (True) and negative (False) feedbacks for terms

    TableName = str  # Name of a DB table
    PrimaryKey = EntityId  # Primary key of the cached data for a table (e.g. AttributeId, TermId, ...)
    CachedTables = collections.defaultdict[
        TableName, Iterator[list[Any]]
    ]  # Data deserialized from DB tables cached in a format suitable for ML algorithms
