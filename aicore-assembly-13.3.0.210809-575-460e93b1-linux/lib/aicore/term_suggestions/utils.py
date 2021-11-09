"""Utility classes and functions."""

from __future__ import annotations

import dataclasses

from typing import TYPE_CHECKING

import numpy

from aicore.common.exceptions import AICoreException


if TYPE_CHECKING:
    from typing import Iterable, Union


class ArrayFullError(AICoreException):
    """Trying to append into a full array."""


class ArrayEmptyError(AICoreException):
    """Trying to pop from an empty array."""


class ResizableNumpyArray:
    """A wrapper for numpy array which supports efficient appending and popping of items (of predefined shape)."""

    def __init__(self, capacity: int, item_shape: Iterable[int], dtype):
        self.storage = numpy.empty(shape=(capacity, *item_shape), dtype=dtype)
        self.occupied = 0

    def append(self, item: Union[list, tuple, numpy.ndarray]):
        """Add an item to the end of the array."""
        if self.occupied == self.capacity:
            raise ArrayFullError("Appending into a full array")

        self.storage[self.occupied] = item
        self.occupied += 1

    def pop(self) -> numpy.ndarray:
        """Remove and return the last item in the array."""
        if self.occupied == 0:
            raise ArrayEmptyError("Popping from an empty array")

        self.occupied -= 1
        last_item = self.storage[self.occupied]

        return last_item.copy()

    @property
    def capacity(self) -> int:
        """Get the number of items that can be held in currently allocated storage."""
        return self.storage.shape[0]

    @property
    def view(self) -> numpy.ndarray:
        """Get a writable view of the currently present items; cached views become invalid after append/pop (!!)."""
        return self.storage[: self.occupied]

    def __getitem__(self, idx):
        return self.view[idx]

    def __setitem__(self, idx, value):
        self.view[idx] = value

    def __len__(self) -> int:
        return self.occupied

    def __repr__(self) -> str:
        return f"{type(self).__name__}(occupied={self.occupied}, capacity={self.capacity}, {self.view!r})"


@dataclasses.dataclass
class ConfusionMatrix:
    """Holds information useful for evaluating performance of a model on a classification task.

    See: https://en.wikipedia.org/wiki/Confusion_matrix
    """

    true_positive: int = 0
    false_positive: int = 0
    false_negative: int = 0
    true_negative: int = 0
