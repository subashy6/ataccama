"""Helper functions for measuring time before and after a block of code."""
from __future__ import annotations

import contextlib

from typing import TYPE_CHECKING

from aicore.common.utils import datetime_now


if TYPE_CHECKING:
    import datetime

    from collections.abc import Iterator
    from typing import Optional


class TimeBounds:
    """Holds information about times before and after an event."""

    time_before: Optional[datetime.datetime]
    time_after: Optional[datetime.datetime]

    def __init__(self):
        self.time_before = datetime_now()
        self.time_after = None

    def set_time_after(self):
        """Set the time after the event to the current time."""
        self.time_after = datetime_now()

    def is_inside_bounds(self, time: datetime.datetime) -> bool:
        """Check if the time is inside bounds."""
        return self.time_before <= time <= self.time_after

    def elapsed_time(self) -> datetime.timedelta:
        """Return the duration of the event."""
        return self.time_after - self.time_before


@contextlib.contextmanager
def measure_time_bounds() -> Iterator[TimeBounds]:
    """Measure time before and after an event.

    It should be used outsize of the contextmanager as the time after is filled when the manager is being exited.
    """
    time_bounds = TimeBounds()
    yield time_bounds
    time_bounds.set_time_after()
