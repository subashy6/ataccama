"""Utility functions related to logging."""
from __future__ import annotations

from typing import TYPE_CHECKING

from aicore.ai_matching.registry import LogId
from aicore.common.logging import WARNING_COLOR


if TYPE_CHECKING:
    import datetime

    from typing import Optional

    from aicore.ai_matching.enums import MatchingId
    from aicore.ai_matching.storage import SingleStorage
    from aicore.common.auth import Identity
    from aicore.common.logging import Logger
    from aicore.common.types import CorrelationId


def log_info(
    logger: Logger,
    message: str,
    message_id: LogId,
    matching_id: MatchingId,
    correlation_id: CorrelationId,
    identity: Optional[Identity],
    logger_depth: int = 2,
    **kwargs,
):
    """Log info message about a particular matching id."""
    # Add "depth" option, otherwise identical to Logger.info
    # This contextualizes the logrecord to the line of code where state change was triggered (n levels up in stack).
    logger.logger.opt(capture=True, depth=logger_depth).bind(_record_type="message").info(
        "{matching_id}: " + message,
        message_id=message_id,
        matching_id=matching_id,
        correlation_id=correlation_id,
        identity=identity,
        **kwargs,
    )


def log_warning(
    logger: Logger,
    message: str,
    message_id: LogId,
    matching_id: MatchingId,
    correlation_id: CorrelationId,
    identity: Optional[Identity],
    logger_depth: int = 2,
    **kwargs,
):
    """Log warning message about a particular matching id."""
    # Add "depth" option, otherwise identical to Logger.warning
    # This contextualizes the logrecord to the line of code where state change was triggered (n levels up in stack).
    logger.logger.opt(capture=True, depth=logger_depth).bind(_record_type="message", _color=WARNING_COLOR).warning(
        "{matching_id}: " + message,
        message_id=message_id,
        matching_id=matching_id,
        correlation_id=correlation_id,
        identity=identity,
        **kwargs,
    )


def log_progress(logger: Logger, storage: SingleStorage, logger_depth: int, elapsed_time: datetime.timedelta):
    """Log current progress of a matching."""
    log_info(
        logger,
        "Progressed in {phase}:{subphase}, took {time}, phase progress: {phase_progress}%, "
        "overall progress: {overall_progress}%",
        LogId.matching_progressed,
        storage.matching_id,
        storage.last_command_correlation_id,
        storage.identity,
        logger_depth,
        phase=storage.phase.name,
        subphase=storage.subphase,
        time=elapsed_time,
        phase_progress=int(storage.phase_progress * 100),
        overall_progress=int(storage.progress * 100),
    )
