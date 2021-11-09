"""Application-wide structured logging and distributed tracing."""

from __future__ import annotations

import json
import logging
import sys
import traceback

from typing import TYPE_CHECKING

import loguru

from aicore.common.exceptions import AICoreException


if TYPE_CHECKING:
    from typing import Optional

    from aicore.common.auth import Identity
    from aicore.common.types import CorrelationId

COLOR = "<white>"
WARNING_COLOR = "<yellow><bold>"
ERROR_COLOR = "<red><bold>"


def remove_nonroot_handlers():
    """Remove all non-root stdlib log handlers."""
    open_handlers = set()
    loggers = logging.getLogger().manager.loggerDict.values()

    for logger in loggers:
        if hasattr(logger, "handlers"):  # Skip logging.PlaceHolder
            for handler in logger.handlers:
                logger.removeHandler(handler)
                open_handlers.add(handler)

            logger.addHandler(logging.NullHandler())
            logger.propagate = True

    for handler in open_handlers:
        handler.flush()
        handler.close()


class InterceptHandler(logging.Handler):
    """Capture all logrecords emitted by stdlib and pass them to Loguru."""

    def emit(self, record):
        """Capture a logrecord from stdlib."""
        try:
            level = loguru.logger.level(record.levelname).name  # Get corresponding Loguru level if exists
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2  # Find who emitted the original logrecord
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        loggers = logging.getLogger().manager.loggerDict
        loggers["root"] = logging.getLogger("root")  # Add the root logger explicitly as it is not part of the dict
        # (e.g. dedupe library loggs sometimes incorrectly directly as root)
        if record.levelno >= loggers[record.name].getEffectiveLevel():  # Obey the configured Logger.level from stdlib
            # Uses Loguru logger directly instead of injecting Logger to avoid always having multiple Logger instances
            # and because stdlib logging must be initialised exactly once which requires module-level globals anyway
            logger = loguru.logger.opt(depth=depth, exception=record.exc_info)
            logger = logger.bind(_record_type="message", message_id=record.name)
            logger.log(level, record.getMessage())


remove_nonroot_handlers()  # Disable all stdlib handlers except the root handler
logging.basicConfig(handlers=[InterceptHandler()], level=0)  # Redirect the stdlib root handler to Loguru


class InvalidLogRecord(AICoreException):
    """The logrecord is invalid."""


class LogConfig:
    """Adapter between Java logback configuration and Loguru."""

    PYTHON_LEVEL_NAMES = {  # Java name -> Python name
        "WARN": "WARNING"
    }  # Other log level names are the same in Java and Python

    def __init__(
        self,
        mode: Optional[dict[str, str]] = None,
        level: str = "INFO",
        rotation: str = "4 days",
        filename: str = "aicore_{self.name}.log",
        compression: str = "zip",
    ):
        # Modes:
        # Local ... {"stdout": "plaintext"}
        # Bare-metal ... {"stdout": "plaintext", "rotated_file": "json"}
        # Docker ... {"stdout": "json"}
        self.mode = mode or {"stdout": "plaintext"}
        self.level = level  # Loguru loglevel name
        self.rotation = rotation  # Loguru rotation
        # Template for str.format(), can refer to Logger attributes via self
        self.filename = filename  # Path + filename for logfile
        self.compression = compression  # Loguru compression

        # See https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.add

    @classmethod
    def from_config(cls, config):
        """Extract the logging configuration from the application-wide configuration."""
        mode = {}

        if config.log_stdout_plaintext:
            mode["stdout"] = "plaintext"
        elif config.log_stdout_json:
            mode["stdout"] = "json"

        if config.log_file_plaintext:
            mode["rotated_file"] = "plaintext"
        elif config.log_file_json:
            mode["rotated_file"] = "json"

        level = cls.PYTHON_LEVEL_NAMES.get(config.log_level, config.log_level)

        return cls(mode, level, config.log_rotation, config.log_filename, config.log_compression)


class LoggedAction:
    """Context manager for logrecords of 'action' type."""

    def __init__(
        self,
        logger,
        action_id,
        correlation_id: Optional[CorrelationId] = None,
        identity: Optional[Identity] = None,
        color=None,
        error_color=None,
        warning_color=None,
    ):
        self.action_id = action_id
        self.correlation_id = correlation_id
        self.identity = identity
        self.color = color or COLOR
        self.error_color = error_color or ERROR_COLOR
        self.warning_color = warning_color or WARNING_COLOR

        self.logger = logger.logger

    def patch_record(self, record):
        """Add action id and correlation id to the logged record."""
        if self.correlation_id:
            record["extra"].update(correlation_id=self.correlation_id)

        if self.identity:
            record["extra"].update(identity=self.identity)

        record["extra"].update(action_id=self.action_id)

    def __enter__(self):
        # Add the action_id to kwargs of all messages logged within the context
        self.logger = self.logger.patch(self.patch_record)

        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        return False

    @property
    def start(self):
        """Log a record for start of the action."""
        return self.logger.opt(capture=True).bind(_record_type="action", status="start", _color=self.color).info

    @property
    def finish(self):
        """Log a record for successfull finish of the action."""
        return self.logger.opt(capture=True).bind(_record_type="action", status="finish", _color=self.color).info

    @property
    def info(self):
        """Log a record for message happening in the context of the action."""
        return self.logger.opt(capture=True).bind(_record_type="message").info

    @property
    def warning(self):
        """Log a record for message happening in the context of the action."""
        return self.logger.opt(capture=True).bind(_record_type="message", _color=self.warning_color).warning

    @property
    def error(self):
        """Log a record for unsuccessful finish of the action (but do not include the traceback)."""
        return (
            self.logger.opt(capture=True).bind(_record_type="action", status="failure", _color=self.error_color).error
        )

    @property
    def exception(self):
        """Log a record for unsuccessful finish of the action and include the traceback (needs error in kwargs)."""
        return (
            self.logger.opt(capture=True, exception=True)
            .bind(_record_type="action", status="failure", _color=self.error_color)
            .exception
        )


class Logger:
    """Logger used by a microservice."""

    # See also https://bitbucket.atc.services/projects/DEV-LIBS/repos/logging/browse/modules/ata-semantic-logger-logback

    JAVA_LEVEL_VALUES = {  # Python name -> Java value
        "TRACE": 5000,
        "DEBUG": 10000,
        "INFO": 20000,
        "WARNING": 30000,
        "ERROR": 40000,
    }  # See https://github.com/qos-ch/logback/blob/master/logback-classic/src/main/java/ch/qos/logback/classic/Level.java  # noqa: E501

    def __init__(self, name: str, log_config: LogConfig, version=None):
        self.name = name  # Name of the microservice
        self.version = version  # Version of the microservice
        self.log_config = log_config

        self.logger = loguru.logger
        self.remove_existing_handlers()  # Work-around for multiple instances of Logger and hacks in Alembic's logging
        self.escaping_translation = str.maketrans({"{": r"{{", "}": r"}}", "<": r"\<", ">": r"\>"})

        for sink_type, format_type in self.log_config.mode.items():
            log_format = self.format_json if format_type == "json" else self.format_plaintext

            # Beware, JSON logging depends on having the kwargs available in record['extra'] via .opt(capture=True)
            # Beware, chained .opt() will reset the options and has to include all existing options manually
            if sink_type == "stdout":
                self.logger.add(
                    sys.stdout,
                    level=self.log_config.level,
                    format=log_format,
                    diagnose=False,
                    backtrace=False,
                )
            else:
                self.logger.add(
                    self.log_config.filename.format(self=self),
                    level=self.log_config.level,
                    format=log_format,
                    diagnose=False,  # Avoid leaking sensitive data from local variables to the log
                    rotation=self.log_config.rotation,
                    compression=self.log_config.compression,
                    colorize=False,
                )

    def action(
        self,
        action_id,
        correlation_id: Optional[CorrelationId] = None,
        identity: Optional[Identity] = None,
        _color=None,
        _error_color=None,
    ):
        """Provide a context manager for logging of messages happening while performing an action."""
        return LoggedAction(self, action_id, correlation_id, identity, _color, _error_color)

    @property
    def event(self):
        """Log an event coming from outside (needs event_id in kwargs)."""
        return self.logger.opt(capture=True).bind(_record_type="event").info

    # Messages:

    @property
    def info(self):
        """Log a message with indication of progress, stage or additional information (needs message_id in kwargs)."""
        return self.logger.opt(capture=True).bind(_record_type="message").info

    @property
    def warning(self):
        """Log a warning message (needs message_id in kwargs)."""
        return self.logger.opt(capture=True).bind(_record_type="message", _color=WARNING_COLOR).warning

    @property
    def error(self):
        """Log an unexpected error without a stacktrace (needs message_id in kwargs)."""
        return self.logger.opt(capture=True).bind(_record_type="message", _color=ERROR_COLOR).error

    @property
    def exception(self):
        """Log an unhandled exception including a stacktrace (needs message_id and error in kwargs)."""
        return self.logger.opt(capture=True, exception=True).bind(_record_type="message", _color=ERROR_COLOR).exception

    def format_plaintext(self, record):
        """Format the logrecord as human-readable string."""
        record_type = record["extra"].get("_record_type")
        correlation_id = record["extra"].get("correlation_id", "")
        identity = record["extra"].get("identity")
        identity = repr(identity) if identity else ""
        action_id = record["extra"].get("action_id", "")
        event_id = record["extra"].get("event_id", "")
        message_id = record["extra"].get("message_id", "")
        context = " ".join(repr(context_id) for context_id in (action_id, event_id, message_id) if context_id)
        action_status = record["extra"].get("status", "")

        if not record_type:
            raise InvalidLogRecord(f"Type of the logrecord is missing: {record!r}")

        if not context:
            raise InvalidLogRecord(f"Context of the logrecord is empty: {record!r}")

        if record_type == "action" and action_status not in {"start", "finish", "failure"}:
            raise InvalidLogRecord(f"Action status {action_status!r} of the logrecord is invalid: {record!r}")

        color = record["extra"].get("_color", "<white>")
        end_color = "</>" * color.count("<")
        time = "<green>{time:YYYY-MM-DD HH:mm:ss!UTC}Z</green>"
        level = f"{color}{{level}}{end_color}"
        context = f"{color}{context}{end_color}"
        record_info = f'{color}{record_type.upper()} {context}{" " if action_status else ""}{action_status.upper()}{end_color}'  # noqa: E501
        name = f"<cyan>{self.name}</cyan>"
        location = ":<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>"
        message = f"{color}{{message}}{end_color}"
        exception = "{exception}"

        return f"{time} | {level} [{correlation_id}][{identity}][{record_info}] | {name}{location} - {message}\n{exception}"  # noqa: E501

    def escape(self, text):
        """Escape all special characters used by Loguru."""
        return str(text).translate(self.escaping_translation)

    def java_name(self, key):
        """Convert the key from Python to Java naming convention."""
        RENAMED_KEYS = {
            "correlation_id": "correlationId",
            "identity": "authenticatedUser",
            "action_id": "actionId",
            "event_id": "eventId",
            "message_id": "messageId",
        }

        return RENAMED_KEYS.get(key, key)

    def format_json(self, record):
        """Format the logrecord as JSON object serialized to string."""
        payload = {
            "@timestamp": "{time:YYYY-MM-DDTHH:mm:ss.SSS!UTC}Z",
            "@version": "1",
            "logger_name": f"ataccama.one.aicore.{self.name}",
            "thread_name": "{thread.name}",
            "severity": "{level}",
            "level_value": self.JAVA_LEVEL_VALUES[record["level"].name],  # Different values than in Python
            "application": "oneApplication",
            "microservice": self.name,
            "microservice_version": self.version,
            "location": "{name}:{function}:{line}",
            "message": "{message}",
        }  # "one." prefix and keys like "hostname" are added later by FluentD when parsing the scraped logs

        public_kwargs = {}
        for key, value in record["extra"].items():
            if not key.startswith("_"):
                if key in ["action_id", "event_id", "message_id"]:
                    value = repr(value)

                public_kwargs[self.escape(self.java_name(key))] = self.escape(value)

        for key, value in public_kwargs.items():
            payload[key] = value

        if record["exception"]:
            # Loguru's "{exception}" doesn't escape quotes and control characters
            payload["stacktrace"] = "".join(traceback.format_tb(record["exception"].traceback))

        return f"{{{json.dumps(payload)}}}\n"

    def shutdown(self):
        """Wait for the flush of Loguru internal multiprocessing queues."""
        self.logger.complete()
        self.logger.remove()

    def remove_existing_handlers(self):
        """Remove all existing log handlers."""
        for handler in self.logger._core.handlers:
            self.logger.remove(handler)
