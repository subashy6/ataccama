"""All action, message and event ids used in upgrade logging messages."""

from __future__ import annotations

import enum


class LogId(enum.Enum):
    """Enum for all action, message and event ids used in upgrade logging."""

    db_upgrade = enum.auto()

    def __repr__(self):
        return self.name
