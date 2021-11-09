"""All action, message and event ids used in Metadata Fetcher logging messages."""
from __future__ import annotations

import enum


class LogId(enum.Enum):
    """Enum for all action, message and event ids used in Metadata Fetching logging."""

    entities_fetching_error = enum.auto()
    entity_types_unsupported = enum.auto()
    fetched_info = enum.auto()
    fetching_entity = enum.auto()
    property_types_unsupported = enum.auto()
    dump_created = enum.auto()

    def __repr__(self):
        return self.name
