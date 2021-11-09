"""SQL database persistence layer for Terms Suggestion using SQLAlchemy."""

from __future__ import annotations

import collections
import uuid

from typing import TYPE_CHECKING

import numpy
import sqlalchemy
import sqlalchemy.exc
import sqlalchemy.orm

from aicore.common.constants import CORRELATION_ID_SIZE, ENCODING, UUID_SIZE
from aicore.common.database import CONSTRAINTS_CONVENTION, SQL_DATETIME_MIN, dao_retry, utcnow
from aicore.common.utils import datetime_to_utc, deserialize_entity_id, serialize_entity_id
from aicore.term_suggestions.fingerprints import FINGERPRINT_DTYPE, FINGERPRINT_SIZE, Fingerprint


if TYPE_CHECKING:
    import datetime

    from collections.abc import Callable, Collection, Iterable, Iterator
    from typing import Any

    from aicore.common.database import Database
    from aicore.common.types import CorrelationId, EntityId
    from aicore.term_suggestions.types import (
        AttributeId,
        Feedbacks,
        LearningStrategies,
        Suggestions,
        TermId,
        Thresholds,
    )


class BLOBSerializer:
    """Converts between Python containers and database BLOBs."""

    def __init__(self, record_separator: str = ";", inner_record_separator: str = ",") -> None:
        self.record_separator = record_separator  # Separator of records serialized into a BLOB
        self.inner_record_separator = inner_record_separator  # Separator of sub-records in a record

    @staticmethod
    def deserialize_entity_id(entity_id: str) -> EntityId:
        """Convert database representation of entity id its python representation."""
        return deserialize_entity_id(entity_id)

    @staticmethod
    def serialize_entity_id(entity_id: EntityId) -> str:
        """Convert entity id to database representation."""
        return serialize_entity_id(entity_id)

    def deserialize_term_ids(self, blob_data: bytes) -> set[TermId]:
        """Convert database BLOB to a set of term ids."""
        if not blob_data:
            return set()

        term_ids = blob_data.decode(ENCODING).split(self.record_separator)
        return {deserialize_entity_id(term_id) for term_id in term_ids}

    def serialize_term_ids(self, term_ids: Iterable[TermId]) -> bytes:
        """Convert term ids to a database BLOB."""
        return self.record_separator.join(serialize_entity_id(term_id) for term_id in term_ids).encode(ENCODING)

    @staticmethod
    def deserialize_fingerprint(blob_data: bytes) -> Fingerprint:
        """Convert database BLOB to fingerprint."""
        return numpy.frombuffer(blob_data, dtype=FINGERPRINT_DTYPE)

    @staticmethod
    def serialize_fingerprint(fingerprint: Fingerprint) -> bytes:
        """Convert fingerprint to database BLOB."""
        return fingerprint.tobytes()

    def deserialize_suggestions(self, blob_data: bytes) -> Suggestions:
        """Convert database BLOB to a list of suggestions."""
        if not blob_data:
            return []

        records = blob_data.decode(ENCODING).split(self.record_separator)
        suggestions = []
        for record in records:
            term_id, confidence = record.split(self.inner_record_separator)
            suggestions.append((uuid.UUID(term_id), float(confidence)))
        return suggestions

    def serialize_suggestions(self, suggestions: Suggestions) -> bytes:
        """Convert a list of suggestions to database BLOB."""
        suggestions_str = self.record_separator.join(
            [
                self.inner_record_separator.join([serialize_entity_id(term_id), str(confidence)])
                for term_id, confidence in suggestions
            ]
        )
        return suggestions_str.encode(ENCODING)


class TSDAO:
    """Persists Terms Suggestion data in a relational database using SQLAlchemy core API (thread-safe).

    Note: If you want your execution methods to retry, add `dao_decorator` to them.
        The decorator should be added only to the outer-most method.
    """

    def __init__(self, database: Database) -> None:
        self.database = database

        self.serializer = BLOBSerializer()
        # Empty registry of database tables, thread-safe only for read, will refuse to re-define an existing table
        # Cannot store metadata in Database - 2nd TSDAO using the same Database would fail to call its define_tables
        self.metadata = sqlalchemy.MetaData(naming_convention=CONSTRAINTS_CONVENTION)
        self.define_tables(self.metadata)  # Populates the metadata with tables

        self.deserializers: collections.defaultdict[
            sqlalchemy.Column, Callable[[bytes], Any]
        ] = collections.defaultdict(
            lambda: lambda x: x,
            {
                self.attributes.c.attribute_id: self.serializer.deserialize_entity_id,
                self.attributes.c.fingerprint: self.serializer.deserialize_fingerprint,
                self.attributes.c.suggestions: self.serializer.deserialize_suggestions,
                self.assigned_terms.c.attribute_id: self.serializer.deserialize_entity_id,
                self.assigned_terms.c.terms: self.serializer.deserialize_term_ids,
                self.rejected_terms.c.attribute_id: self.serializer.deserialize_entity_id,
                self.rejected_terms.c.terms: self.serializer.deserialize_term_ids,
                self.disabled_terms.c.term_id: self.serializer.deserialize_entity_id,
                self.similarity_thresholds.c.term_id: self.serializer.deserialize_entity_id,
                self.learning_strategies.c.term_id: self.serializer.deserialize_entity_id,
                self.feedbacks.c.term_id: self.serializer.deserialize_entity_id,
            },
        )

    def define_tables(self, metadata):
        """Define SQLAlchemy tables used by Terms Suggestions."""
        self.attributes = sqlalchemy.Table(
            "attributes",
            metadata,
            sqlalchemy.Column("attribute_id", sqlalchemy.String(UUID_SIZE), primary_key=True),
            sqlalchemy.Column("fingerprint", sqlalchemy.LargeBinary(FINGERPRINT_SIZE), nullable=False),
            sqlalchemy.Column("last_modified", sqlalchemy.TIMESTAMP(timezone=True), index=True, nullable=False),
            sqlalchemy.Column("correlation_id", sqlalchemy.String(CORRELATION_ID_SIZE), nullable=False),
            sqlalchemy.Column("suggestions", sqlalchemy.LargeBinary, nullable=True),  # Grows with number of suggestions
            sqlalchemy.Column("suggestions_freshness", sqlalchemy.TIMESTAMP(timezone=True), index=True, nullable=False),
            sqlalchemy.Column(
                "suggestions_last_modified", sqlalchemy.TIMESTAMP(timezone=True), index=True, nullable=False
            ),
            sqlalchemy.Column("deleted", sqlalchemy.Boolean, nullable=False),
        )  # Customer database attributes, their statistical features, and suggested terms for them

        self.assigned_terms = sqlalchemy.Table(
            "assigned_terms",
            metadata,
            sqlalchemy.Column("attribute_id", sqlalchemy.String(UUID_SIZE), primary_key=True),
            sqlalchemy.Column("terms", sqlalchemy.LargeBinary, nullable=False),  # Grows with number of terms
            sqlalchemy.Column("last_modified", sqlalchemy.TIMESTAMP(timezone=True), index=True, nullable=False),
            sqlalchemy.Column("correlation_id", sqlalchemy.String(CORRELATION_ID_SIZE), nullable=False),
        )  # Terms assigned to attributes by users (or accepted suggestions)

        self.rejected_terms = sqlalchemy.Table(
            "rejected_terms",
            metadata,
            sqlalchemy.Column("attribute_id", sqlalchemy.String(UUID_SIZE), primary_key=True),
            sqlalchemy.Column("terms", sqlalchemy.LargeBinary, nullable=False),  # Size grows with the number of terms
            sqlalchemy.Column("last_modified", sqlalchemy.TIMESTAMP(timezone=True), index=True, nullable=False),
            sqlalchemy.Column("correlation_id", sqlalchemy.String(CORRELATION_ID_SIZE), nullable=False),
        )  # Suggested terms for attributes rejected by users

        self.disabled_terms = sqlalchemy.Table(
            "disabled_terms",
            metadata,
            sqlalchemy.Column("term_id", sqlalchemy.String(UUID_SIZE), primary_key=True),
            sqlalchemy.Column("last_modified", sqlalchemy.TIMESTAMP(timezone=True), index=True, nullable=False),
            sqlalchemy.Column("correlation_id", sqlalchemy.String(CORRELATION_ID_SIZE), nullable=False),
            sqlalchemy.Column("deleted", sqlalchemy.Boolean, nullable=False),
        )  # Terms manually excluded from suggestions

        self.similarity_thresholds = sqlalchemy.Table(
            "similarity_thresholds",
            metadata,
            sqlalchemy.Column("term_id", sqlalchemy.String(UUID_SIZE), primary_key=True),
            sqlalchemy.Column("value", sqlalchemy.Float, nullable=False),
            sqlalchemy.Column("last_modified", sqlalchemy.TIMESTAMP(timezone=True), index=True, nullable=False),
            sqlalchemy.Column("correlation_id", sqlalchemy.String(CORRELATION_ID_SIZE), nullable=False),
        )  # How much two attributes need to be similar for a possible text label suggestion

        self.learning_strategies = sqlalchemy.Table(
            "learning_strategies",
            metadata,
            sqlalchemy.Column("term_id", sqlalchemy.String(UUID_SIZE), primary_key=True),
            sqlalchemy.Column("adaptive", sqlalchemy.Boolean, nullable=False),
            sqlalchemy.Column("correlation_id", sqlalchemy.String(CORRELATION_ID_SIZE), nullable=False),
        )  # Adaptive learning is enabled (true - thresholds are adapted by the feedback service) or disabled (false)

        self.feedbacks = sqlalchemy.Table(
            "feedbacks",
            metadata,
            sqlalchemy.Column(
                "sequential_id",
                sqlalchemy.BigInteger().with_variant(sqlalchemy.Integer, "sqlite"),  # Sqlite doesn't support BigInteger
                primary_key=True,
                autoincrement=True,
            ),
            sqlalchemy.Column("term_id", sqlalchemy.String(UUID_SIZE), nullable=False),
            sqlalchemy.Column("positive", sqlalchemy.Boolean, nullable=False),
            sqlalchemy.Column("correlation_id", sqlalchemy.String(CORRELATION_ID_SIZE), nullable=False),
        )  # Queue of feedbacks from users accepting (true) / rejecting (false) proposals, processed by feedback service

    def create_tables(self) -> None:
        """Create the database tables used by Terms Suggestion."""
        with self.database.connection(operation="create_tables") as connection:
            self.metadata.create_all(connection)

    def truncate_tables(self) -> None:
        """Delete all rows of database tables used by Terms Suggestions."""
        with self.database.connection(operation="truncate_tables") as connection:
            for table in self.metadata.sorted_tables:
                connection.execute(table.delete())  # SQLAlchemy doesn't directly support TRUNCATE TABLE

    def deserialize_rows(
        self, db_columns: list[sqlalchemy.Column], rows: Iterable[sqlalchemy.engine.LegacyRow]
    ) -> Iterator[list[Any]]:
        """Deserialize cells in each row."""
        column_deserializers = [self.deserializers[column] for column in db_columns]

        for row in rows:
            deserialized_cells = [cell_deserializer(cell) for cell, cell_deserializer in zip(row, column_deserializers)]
            yield deserialized_cells

    @dao_retry
    def get_attribute_count(self) -> int:
        """Get count of present attributes.

        WARNING: overestimates – disregards the deleted flag to prevent full table scan.
        """
        with self.database.connection(operation="get_attribute_count") as connection:
            with connection.begin():
                result = connection.execute(sqlalchemy.select(sqlalchemy.func.count()).select_from(self.attributes))
                return result.first()[0]

    @dao_retry
    def get_last_modified(self, last_modified_column: sqlalchemy.Column) -> datetime.datetime:
        """Get all rows of database columns modified since given timestamp."""
        with self.database.connection(operation="get_last_modified") as connection:
            with connection.begin():
                # Get the highest last_modified timestamp
                max_last_modified = connection.execute(sqlalchemy.func.max(last_modified_column)).first()[0]
                return datetime_to_utc(max_last_modified) if max_last_modified else SQL_DATETIME_MIN

    @dao_retry
    def get_changes(
        self,
        db_columns: list[sqlalchemy.Column],
        last_modified_column: sqlalchemy.Column,
        from_exclusive: datetime.datetime,
        to_inclusive: datetime.datetime,
    ) -> Iterator[list[Any]]:
        """Get all rows of database columns modified in the given time interval."""
        with self.database.connection(operation="get_changes") as connection:
            with connection.begin():
                # stream_results=True (see https://docs.sqlalchemy.org/en/14/core/connections.html#using-server-side-cursors-a-k-a-stream-results)  # noqa: E501
                # Change set upon startup is big (especially the fingerprints) - we need to avoid the memory peak
                results = connection.execution_options(stream_results=True).execute(
                    sqlalchemy.select(*db_columns)
                    .order_by(last_modified_column)  # Ascending
                    .where(last_modified_column > from_exclusive)
                    .where(last_modified_column <= to_inclusive)
                )

                try:
                    # `Yield from` (compared to `return iterable`) keeps the LegacyRow and the transaction context
                    #   - MSSql doesn't allow iterating over the results outside of the transaction context
                    yield from self.deserialize_rows(db_columns, results)
                finally:
                    # Cursor is automatically released only when the CursorResult exhausts all available rows
                    # See https://docs.sqlalchemy.org/en/14/core/connections.html?highlight=cursorresult#sqlalchemy.engine.CursorResult.close  # noqa: E501
                    results.close()

    @dao_retry
    def get_feedbacks(self, limit: int) -> tuple[list[int], Feedbacks]:
        """Get currently present feedbacks about accepted / rejected suggestions."""
        with self.database.connection(operation="get_feedbacks") as connection:
            # Get all columns from the feedbacks table except for the correlation_id column
            results = connection.execute(
                sqlalchemy.select(
                    self.feedbacks.c.sequential_id, self.feedbacks.c.term_id, self.feedbacks.c.positive
                ).limit(limit)
            )

            sequential_ids = []
            feedbacks = []
            for sequential_id, term_id, is_positive in results:
                sequential_ids.append(sequential_id)
                feedbacks.append((self.serializer.deserialize_entity_id(term_id), is_positive))

            return sequential_ids, feedbacks

    @dao_retry
    def get_fingerprints_freshness(self) -> datetime.datetime:
        """Get modification timestamp of the most recently modified fingerprint."""
        with self.database.connection(operation="get_fingerprints_freshness") as connection:
            query = sqlalchemy.func.max(self.attributes.c.last_modified)
            last_modified = connection.execute(query).first()[0]
        return datetime_to_utc(last_modified) if last_modified else SQL_DATETIME_MIN

    @dao_retry
    def get_learning_strategies(self) -> LearningStrategies:
        """Get learning strategies of all terms."""
        with self.database.connection(operation="get_learning_strategies") as connection:
            results = connection.execute(
                sqlalchemy.select(self.learning_strategies.c.term_id, self.learning_strategies.c.adaptive)
            )
            return {self.serializer.deserialize_entity_id(term_id): adaptive for term_id, adaptive in results}

    @dao_retry
    def get_outdated_attributes(self, limit: int, older_than: datetime.datetime) -> list[AttributeId]:
        """Get a batch of present (not deleted) attributes whose suggestions are based on old data."""
        with self.database.connection(operation="get_outdated_attributes") as connection:
            result = connection.execute(
                sqlalchemy.select(self.attributes.c.attribute_id)
                .order_by(self.attributes.c.suggestions_freshness)  # Oldest first
                .where(
                    sqlalchemy.and_(
                        self.attributes.c.suggestions_freshness < older_than,  # Outdated suggestions
                        ~self.attributes.c.deleted,  # Not deleted attributes
                    )
                )
                .limit(limit)
            )
            return [self.serializer.deserialize_entity_id(row.attribute_id) for row in result]

    @dao_retry
    def get_similarity_thresholds(self) -> Thresholds:
        """Get neighbor similarity thresholds of all terms."""
        with self.database.connection(operation="get_similarity_thresholds") as connection:
            results = connection.execute(
                sqlalchemy.select(self.similarity_thresholds.c.term_id, self.similarity_thresholds.c.value)
            )
            return {self.serializer.deserialize_entity_id(term_id): value for term_id, value in results}

    @dao_retry
    def set_learning_strategy(self, term_id: TermId, adaptive: bool, correlation_id: CorrelationId):
        """Upsert the learning strategy of a term."""
        serialized_term_id = self.serializer.serialize_entity_id(term_id)

        with self.database.connection(operation="set_learning_strategy") as connection:
            with connection.begin():
                # Delete the old strategy if it is present
                connection.execute(
                    self.learning_strategies.delete().where(self.learning_strategies.c.term_id == serialized_term_id)
                )
                # Insert the row back with updated data
                connection.execute(
                    self.learning_strategies.insert().values(
                        term_id=serialized_term_id, adaptive=adaptive, correlation_id=correlation_id
                    )
                )

    @dao_retry
    def set_similarity_thresholds(
        self,
        thresholds: dict[TermId, float],
        correlation_id: CorrelationId,
        sequential_ids: Collection[int] = (),
    ):
        """Upsert the similarity threshold of multiple terms and delete the processed feedbacks in one transaction."""
        serialized_thresholds = {
            self.serializer.serialize_entity_id(term_id): threshold for term_id, threshold in thresholds.items()
        }
        thresholds_payload = [
            {
                self.similarity_thresholds.c.term_id.name: serialized_term_id,
                self.similarity_thresholds.c.value.name: threshold,
            }
            for serialized_term_id, threshold in serialized_thresholds.items()
        ]

        with self.database.connection(operation="set_similarity_thresholds") as connection:
            with connection.begin():
                if thresholds_payload:
                    # Delete all rows with modified thresholds if they are present
                    connection.execute(
                        self.similarity_thresholds.delete().where(
                            self.similarity_thresholds.c.term_id.in_(serialized_thresholds.keys())
                        )
                    )
                    # Values shared for all inserted rows
                    shared_values = {
                        self.similarity_thresholds.c.correlation_id.name: correlation_id,
                        self.similarity_thresholds.c.last_modified.name: utcnow(),  # UTC time of the database
                    }
                    # Insert the rows back with updated data
                    connection.execute(self.similarity_thresholds.insert().values(**shared_values), thresholds_payload)

                if sequential_ids:
                    # Delete processed feedbacks
                    connection.execute(
                        self.feedbacks.delete().where(self.feedbacks.c.sequential_id.in_(sequential_ids))
                    )

    @dao_retry
    def set_suggestions_batch(
        self,
        attributes: list[AttributeId],
        suggestions_batch: list[Suggestions],
        suggestions_freshness: datetime.datetime,
    ):
        """Set suggestions and their freshness for a batch of attributes, also update their last modified timestamps."""
        if not attributes:
            return

        matching_column_name = self.attributes.c.attribute_id.name + "_"  # Must be a unique name
        payload = [
            {
                matching_column_name: self.serializer.serialize_entity_id(attribute_id),
                self.attributes.c.suggestions.name: self.serializer.serialize_suggestions(suggestions),
            }
            for attribute_id, suggestions in zip(attributes, suggestions_batch)
        ]

        with self.database.connection(operation="set_suggestions_batch") as connection:
            with connection.begin():
                connection.execute(
                    self.attributes.update()
                    .values(
                        suggestions_freshness=suggestions_freshness,
                        suggestions_last_modified=utcnow(),  # UTC time of the database
                    )
                    .where(self.attributes.c.attribute_id == sqlalchemy.bindparam(matching_column_name)),
                    payload,
                )
