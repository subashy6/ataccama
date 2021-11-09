"""In this module we define the basic object types used within the NlpSearch module."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    AQLString = str
    # Filter-like Query part type (e.g. entityType, term) and constraint-like query part value (e.g. PII)
    QueryPart = tuple[str, str]
    # Historical query consisting of multiple filled QueryParts
    HistoricalQuery = tuple[QueryPart, ...]
    # Mapping of entity names to all their instances
    EntityInstances = dict[str, set[str]]
