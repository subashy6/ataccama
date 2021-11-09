"""All action, message and event ids used in NLP search logging messages."""
from __future__ import annotations

import enum


class LogId(enum.Enum):
    """Enum for all action, message and event ids used in NLP search logging."""

    autocomplete_value_unknown = enum.auto()
    spellchecker_prepare_vocabulary = enum.auto()

    def __repr__(self):
        return self.name
