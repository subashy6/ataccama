"""Retrying controller with a built-in capability to stop retrying on event."""

from __future__ import annotations

import threading

from typing import TYPE_CHECKING

import tenacity


if TYPE_CHECKING:
    from collections.abc import Callable


stop_always = tenacity.stop_all()  # Stop strategy that always stops
never_retrying = tenacity.Retrying(stop=stop_always)


class stop_if(tenacity.stop.stop_base):
    """Stop strategy that stops retrying if the predicate verifies the retry state."""

    def __init__(self, predicate: Callable[[tenacity.RetryCallState], bool]):
        self.predicate = predicate

    def __call__(self, retry_state) -> bool:
        """Return True when the predicate verifies the retry state."""
        return self.predicate(retry_state)


class EventAwareRetrying(tenacity.Retrying):
    """Retrying controller which additionally stops retrying when the event is set.

    For this to work the controller additionally has to:
     a) wake up from sleep between retries when the event is set, and
     b) stop retrying when the event is set.

    Therefore, this controlled can't accept custom sleep strategy (the 'sleep' arg), as it has to sleep using the event.

    Note: controller with such behavior could be created just by crafting the right arguments to the tenacity.Retrying
    (as done here in __init__). Unfortunately, in some cases (e.g. DI of the controller) one cannot know that such
    event-awareness is present. Without taking the event-awareness into consideration, further adjustments to the
    controller's behavior (via .copy()) can lead to the event-awareness being lost (e.g. by altering the stop strategy).

    This implementation preserves the event-awareness even when using .copy().
    """

    def __init__(
        self,
        cancel_event: threading.Event,
        **kwargs,  # See tenacity.BaseRetrying.__init__ for full list of possible arguments
    ):
        if "sleep" in kwargs:
            raise TypeError("__init__() got forbidden argument 'sleep'")

        self.cancel_event = cancel_event
        # self.stop is already taken in the base class
        self.additional_stop = kwargs.pop("stop", None)

        # sleep strategy used to sleep between retries, wakes up from sleeping when the event is set
        sleep = tenacity.sleep_using_event(cancel_event)

        # stop strategy used to stop the retrying process, stops the retrying when the event is set
        stop = tenacity.stop_when_event_set(cancel_event)

        if self.additional_stop:
            stop |= self.additional_stop  # stop when the event is set OR when the additional stop says so

        super().__init__(sleep, stop, **kwargs)

    def copy(self, **kwargs):  # See tenacity.BaseRetrying.__init__ for full list of possible arguments
        """Return copy of this object, optionally with some parameters changed to alter the retrying behavior."""
        if "sleep" in kwargs:
            raise TypeError("copy() got forbidden argument 'sleep'")

        if self.additional_stop:
            # Can't simply set kwarg stop=self.stop (as other kwargs are set below), as self.stop it is a crafted object
            # (see __init__). What the __init__ received as "stop" argument is stored in self.additional_stop.
            kwargs.setdefault("stop", self.additional_stop)

        for copied_attr in (
            "cancel_event",
            "wait",
            "retry",
            "before",
            "after",
            "before_sleep",
            "reraise",
            "retry_error_cls",
            "retry_error_callback",
        ):
            kwargs.setdefault(copied_attr, getattr(self, copied_attr))

        return type(self)(**kwargs)
