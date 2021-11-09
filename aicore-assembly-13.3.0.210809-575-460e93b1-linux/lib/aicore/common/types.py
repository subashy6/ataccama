"""Abbreviations of commonly used types."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    import uuid

    CorrelationId = str  # Data type of correlation id - should be 6 hexadecimal characters, or empty string in case
    # no correlation id was specified
    EntityId = uuid.UUID  # An identifier of an entity - see https://en.wikipedia.org/wiki/Universally_unique_identifier
    WSGIResponse = tuple[str, list, list]  # WSGI handler (status code and description, headers, payload)
