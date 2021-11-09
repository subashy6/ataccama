"""Relational database wrapper using SQLAlchemy and Alembic."""

from __future__ import annotations

import contextlib
import functools
import traceback

from typing import TYPE_CHECKING

import alembic.script
import sqlalchemy
import sqlalchemy.ext.compiler
import tenacity

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from aicore.common.exceptions import AICoreException
from aicore.common.registry import DatabaseMetric, LogId
from aicore.common.resource import ReadinessDependency
from aicore.common.retry import never_retrying
from aicore.common.utils import datetime_fromtimestamp


if TYPE_CHECKING:
    from typing import Any, Optional

    from aicore.common.logging import Logger
    from aicore.common.metrics import MetricsDAO

# Supported DB dialects can be found in `common.constants`
# An agreed upon value (with Java) which fits into range of datetime types of all the supported backends
SQL_DATETIME_MIN = datetime_fromtimestamp(0)
CONSTRAINTS_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}  # See https://alembic.sqlalchemy.org/en/latest/naming.html#the-importance-of-naming-constraints


class utcnow(sqlalchemy.sql.expression.FunctionElement):
    """SQL function providing current date and time in UTC."""

    type = sqlalchemy.TIMESTAMP(timezone=True)


@sqlalchemy.ext.compiler.compiles(utcnow, "sqlite")
def sqlite_utcnow(_element, _compiler, **_kwargs):
    """SQLite function providing the current date and time in UTC."""  # noqa: D403
    # https://www.sqlite.org/lang_datefunc.html
    return "strftime('%Y-%m-%d %H:%M:%f', 'now')"  # 'now' is in UTC


@sqlalchemy.ext.compiler.compiles(utcnow, "postgresql")
def postgresql_utcnow(_element, _compiler, **_kwargs):
    """PostgreSQL function providing current date and time in UTC."""  # noqa: D403
    # https://www.postgresql.org/docs/current/functions-datetime.html#FUNCTIONS-DATETIME-CURRENT
    # No precision specified == full available precision
    # Based on https://www.enterprisedb.com/postgres-tutorials/postgres-time-zone-explained
    # Timestamp + time zone + cast into timezone-aware data type
    return "CURRENT_TIMESTAMP AT TIME ZONE 'utc' AT TIME ZONE 'utc'"


def get_latest_schema_version(migrations_path):
    """Get the latest schema version by parsing Alembic's migration scripts."""
    # Avoids importing Alembic's env.py and logging
    return alembic.script.ScriptDirectory(migrations_path).get_heads()[0]


class DatabaseError(AICoreException):
    """Wrapper for all database-related errors."""


class DatabaseOperationalError(DatabaseError):
    """Wrapper for database-related errors corresponding to the sqlalchemy.exc.OperationalError."""


class DatabaseTimeoutError(DatabaseError):
    """Wrapper for database-related errors corresponding to the sqlalchemy.exc.TimeoutError."""


def dao_retry(func):
    """Retry decorator for DAO objects."""

    @functools.wraps(func)
    def retry_wrapper(dao, *args, **kwargs):
        return dao.database.retrying(func, dao, *args, **kwargs)

    return retry_wrapper


class Database(ReadinessDependency):
    """Manages a relational database using SQLAlchemy.

    Can be used directly in the self.health.state == NOT_READY; .start() just initiates the readiness checking.
    """

    def __init__(
        self,
        name: str,
        logger: Logger,
        connection_string: str,
        latest_version: str,
        metrics: MetricsDAO,
        onstart_retrying: tenacity.Retrying,
        retrying: tenacity.Retrying = never_retrying,
        **engine_kwargs,
    ) -> None:
        super().__init__(name, logger, onstart_retrying, readiness_predicate=self.is_ready, tracks_liveness=False)
        self.connection_string = connection_string  # dialect://username:urllib.parse(password)@host:port/database
        self.latest_version = latest_version  # Output of "alembic head"
        self.retrying = retrying.copy(
            retry=tenacity.retry_if_exception_type((DatabaseOperationalError, DatabaseTimeoutError)),
            before_sleep=self._log_execute_attempt,
            reraise=True,
        )

        # Useful Engine kwargs:
        # echo="debug" - Print every SQL query to stdout
        # pool_pre_ping=False - Do not check if DB is alive for every connection connecting (via dummy SELECT)
        # pool_size=5 - Maximum number of permanent (but lazily created) database connections
        # max_overflow=10 - Maximum number of additional temporary database connections
        # timeout=5 - [s] How long to wait for getting a connection from the pool before raising an exception
        # isolation_level="SERIALIZABLE" - Default isolation level depends on dialect
        # reset_on_return="rollback" - Abort open transactions when returning a connection back to the pool
        # max_identifier_length=128 - Suppress a warning on limitations of old Oracle versions

        # Connection pooling, thread-safe but not fork-safe
        try:
            self.engine: sqlalchemy.engine.Engine = sqlalchemy.create_engine(self.connection_string, **engine_kwargs)
        except Exception as error:
            parsed_kwargs = ", ".join(f"{key}={value}" for key, value in engine_kwargs.items())
            raise DatabaseError(f"Failed to create DB engine with options: {parsed_kwargs or 'None'}") from error

        # Schema version management via Alembic
        self.schema_version = sqlalchemy.table(
            "alembic_version", sqlalchemy.column("version_num")
        )  # For faster "alembic current"

        self.current_version = "not set"  # Equivalent to output of "alembic current"

        self.metrics = metrics
        self.metrics.register(DatabaseMetric)

    def __repr__(self):
        return f"Database {self.name!r} ({self.engine.url!r})"

    @contextlib.contextmanager
    def connection(self, operation: Optional[str] = None) -> sqlalchemy.engine.Connection:
        """Context manager for a thread-safe database connection."""
        measure_time = (
            self.metrics.measure_time(DatabaseMetric.query_seconds, operation=operation)
            if operation
            else contextlib.nullcontext()
        )

        try:
            with measure_time:
                with self.engine.connect() as connection:  # Borrow a connection from the pool (for thread safety)
                    yield connection
        except sqlalchemy.exc.OperationalError as error:
            raise DatabaseOperationalError from error
        except sqlalchemy.exc.TimeoutError as error:
            raise DatabaseTimeoutError from error
        except Exception as error:
            raise DatabaseError from error  # Beware, line number in traceback points to commit of whole transaction

        # The connection can be used for multiple queries
        # sqlalchemy.Engine is thread-safe, sqlalchemy.engine.Connection/Transaction are not
        # Borrowing a connection from exhausted pool may block and timeout when other threads are busy
        # Connection pool creates new sockets lazily and keeps some of them (pool_size) open for reuse
        # Connection pool can create more sockets than the pool_size (max_overflow) but closes them after use
        # SQLAlchemy rolls back the transaction and resets the connection after database outage
        # Iteration over sqlalchemy.ResultProxy outside of the transaction context fails with HY010 error on MS SQL
        # SQLAlchemy lacks UPSERT due limitations of some dialects - use DELETE WHERE + INSERT instead

    def create_database(self, database_name: str, user_name: str) -> None:
        """Create a new database."""
        with self.engine.connect() as connection:
            connection.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)  # Close transaction on connection

            create_db_query = f'CREATE DATABASE "{database_name}" WITH OWNER {user_name}'
            grant_rights_query = f'GRANT ALL PRIVILEGES ON DATABASE "{database_name}" TO {user_name}'

            connection.execute(create_db_query)
            connection.execute(grant_rights_query)

    def drop_all_tables(self) -> None:
        """Discover all database tables and drop them including the contained data."""
        # Naming convention is not needed, the metadata are used only for dropping the tables
        actual_metadata = sqlalchemy.MetaData()  # Do not make any assumptions on the existing database schema

        with contextlib.suppress(sqlalchemy.exc.NoSuchTableError):
            actual_metadata.reflect(self.engine)  # Too slow for regular use but fine for dropping the schema

        actual_metadata.drop_all(self.engine)  # Correctly resolves the foreign key dependencies

    def drop_database(self, database_name: str) -> None:
        """Drop given database."""
        # https://sqlalchemy-utils.readthedocs.io/en/latest/_modules/sqlalchemy_utils/functions/database.html#drop_database  # noqa: E501

        with self.engine.connect() as connection:
            connection.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)  # Close transaction on connection

            drop_db_query = f'DROP DATABASE IF EXISTS "{database_name}"'
            connection.execute(drop_db_query)

    def is_ready(self) -> bool:
        """Indicate whether the database uses the latest schema version."""
        try:
            self.current_version = self.get_current_schema_version()
        except DatabaseError as error:
            self.health.not_ready(str(error.__cause__))
            return False

        if self.current_version == self.latest_version:
            return True

        if not self.current_version:
            self.health.not_ready(f"Schema version is not set (should be set to {self.latest_version!r}).")
        else:
            self.health.not_ready(f"Schema version {self.current_version!r} is different than {self.latest_version!r}.")

        return False

    def shutdown(self) -> None:
        """Disconnect from the database and shut down the connection pool."""
        self.engine.dispose()
        super().shutdown()

    def prepare_state_change_log_record(self) -> tuple[str, dict[str, Any]]:
        """Return log message and kwargs appropriate for the new state the database is in."""
        return "{self!r} is {health!r}", {"event_id": LogId.db_state_change}

    def get_current_schema_version(self):
        """Get the current version of database schema."""
        with self.connection() as connection:
            if not self.engine.dialect.has_table(connection, self.schema_version.name):
                schema_version = ""  # DB table is not present
            else:
                schema_version = connection.execute(sqlalchemy.select(self.schema_version.c.version_num)).first()[0]

        return schema_version

    def _log_execute_attempt(self, retry_state: tenacity.RetryCallState):
        """Log failed attempt to execute database query."""
        error = retry_state.outcome.exception()

        if retry_state.fn:
            # When retrying is done via `dao_retry` decorator
            function_name = retry_state.fn.__name__
        else:
            # When retrying is done via the `for attempt in retrying` and `with attempt:`
            function_name = traceback.extract_stack(error.__traceback__.tb_frame, limit=1)[0].name

        self.logger.warning(
            "Database {name!r} raised {error_name!r} while executing {function_name!r} query at {connection_string!r}, next attempt in {sleep} s",  # noqa: E501
            name=self.name,
            error=error,
            error_name=type(error).__name__,
            function_name=function_name,
            connection_string=repr(self.engine.url),  # repr() masks the password inside
            attempt=retry_state.attempt_number,
            sleep=retry_state.next_action.sleep,
            message_id=LogId.db_execute,
        )


# Used both by manage and Alembic - must be located in common to avoid cyclic dependencies
def create_database(connection_string=None, name="cli_db", **engine_kwargs):
    """Create database with its logger either on the default or the provided connection string."""
    from aicore.common.config import DB_CONFIG_OPTIONS, LOGGING_CONFIG_OPTIONS, get_config
    from aicore.common.constants import RESPONSIVENESS_PERIOD
    from aicore.common.logging import LogConfig, Logger
    from aicore.common.metrics import MetricsDAO

    log_config = LogConfig.from_config(get_config(LOGGING_CONFIG_OPTIONS))
    logger = Logger(name, log_config)
    connection_string = connection_string or get_config(DB_CONFIG_OPTIONS).connection_string
    retrying = tenacity.Retrying(wait=tenacity.wait_fixed(wait=RESPONSIVENESS_PERIOD))
    metrics = MetricsDAO()

    return Database(name, logger, connection_string, "fake_latest_version", metrics, retrying, **engine_kwargs)
