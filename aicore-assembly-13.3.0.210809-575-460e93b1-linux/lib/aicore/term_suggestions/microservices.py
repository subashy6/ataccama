"""Microservices (processes or Docker containers) provided by Term Suggestions."""

from __future__ import annotations

import collections
import enum
import itertools
import math

from typing import TYPE_CHECKING

from aicore.common.database import SQL_DATETIME_MIN
from aicore.common.exceptions import AICoreException
from aicore.common.microservice import Microservice, sleep_between_periods
from aicore.common.utils import datetime_str, random_correlation_id
from aicore.term_suggestions import FEEDBACK, NEIGHBORS, RECOMMENDER, commands
from aicore.term_suggestions.database import TSDAO, BLOBSerializer
from aicore.term_suggestions.neighbors import (
    AttributeLimit,
    FingerprintsIndex,
    FingerprintsIndexFullError,
    NeighborsCalculator,
)
from aicore.term_suggestions.recommender import Recommender
from aicore.term_suggestions.registry import FeedbackMetric, LogId, NeighborsMetric, RecommenderMetric
from aicore.term_suggestions.thresholds import ThresholdCalculator
from aicore.term_suggestions.utils import ConfusionMatrix


if TYPE_CHECKING:
    import datetime

    from collections.abc import Callable
    from typing import Any, Collection, Iterable, Optional

    import sqlalchemy

    from aicore.common.metrics import MetricsDAO
    from aicore.common.resource import Health
    from aicore.common.types import CorrelationId
    from aicore.term_suggestions.types import (
        AttributeId,
        CachedTables,
        Feedbacks,
        Suggestions,
        TableName,
        TermAssignments,
        TermId,
    )


class FreshnessError(AICoreException):
    """Freshness of underlying data is too old."""


class CacheChange(enum.Enum):
    """Types of changes that happen when updating cache."""

    update = enum.auto()
    delete = enum.auto()


class DBPoller:
    """Incrementally polls for changes of data persisted in a database."""

    def __init__(self, dao: TSDAO, tables: list[PolledTable]):
        self.dao = dao
        self.tables = tables

        self.last_modified: collections.defaultdict[TableName, datetime.datetime] = collections.defaultdict(
            lambda: SQL_DATETIME_MIN
        )

    def poll(self) -> CachedTables:
        """Get changes since last poll from the database (changed rows + deleted rows)."""
        changes: CachedTables = collections.defaultdict(list)  # {table name: iterator[deserialized_data_columns]}

        for polled_table in self.tables:
            table_name = polled_table.table.name
            last_modified = self.last_modified[table_name]

            new_last_modified = self.dao.get_last_modified(polled_table.last_modified_column)

            if new_last_modified != last_modified:
                changes[table_name] = self.dao.get_changes(
                    polled_table.columns,
                    polled_table.last_modified_column,
                    from_exclusive=last_modified,
                    to_inclusive=new_last_modified,
                )

                self.last_modified[table_name] = new_last_modified

        return changes


class PolledTable:
    """Defines a table which should be polled, columns of interest and optionally a filer for rows."""

    def __init__(
        self,
        table: sqlalchemy.Table,
        columns: list[sqlalchemy.Column],
        row_validator: Optional[Callable[[Any], bool]] = None,
    ):
        self.table = table
        self.columns = columns
        self.row_validator = row_validator if row_validator else lambda row: True  # Detects valid vs deleted rows
        # Column storing last modification timestamps, needs to be present in the table
        self.last_modified_column: sqlalchemy.Column = self.table.c.last_modified


class RecommenderMetricsTracker:
    """Tracks and updates recommender metrics."""

    def __init__(self, metrics: MetricsDAO):
        self.metrics = metrics
        self.assigned_terms: TermAssignments = {}
        self.confusion_matrix = ConfusionMatrix()
        self.disabled_terms: set[TermId] = set()
        self.known_terms: set[TermId] = set()

        self.metrics.register(RecommenderMetric)

        metric = RecommenderMetric.suggestions_confusion_matrix
        self.metrics.set_callback(metric, lambda: self.confusion_matrix.true_positive, entry="true_positive")
        self.metrics.set_callback(metric, lambda: self.confusion_matrix.false_positive, entry="false_positive")
        self.metrics.set_callback(metric, lambda: self.confusion_matrix.false_negative, entry="false_negative")
        self.metrics.set_callback(metric, lambda: self.confusion_matrix.true_negative, entry="true_negative")

        self.metrics.set_callback(RecommenderMetric.terms_disabled, lambda: len(self.disabled_terms))
        self.metrics.set_callback(RecommenderMetric.terms_known, lambda: len(self.known_terms))

    def terms_updated(
        self, assigned_terms: TermAssignments, rejected_terms: TermAssignments, disabled_terms: Iterable[TermId]
    ):
        """Inform the tracker that assigned, rejected or disabled terms were updated."""
        self.assigned_terms = assigned_terms
        self.disabled_terms = set(disabled_terms)

        self.known_terms = set()
        for terms in itertools.chain(self.assigned_terms.values(), rejected_terms.values()):
            self.known_terms |= terms
        self.known_terms -= self.disabled_terms

    def all_suggestions_outdated(self):
        """Inform the tracker that all suggestions are outdated."""
        self.metrics.increment(RecommenderMetric.recommendation_starts_total)
        # No suggestions are up-to-date => reset all metrics based on currently up-to-date suggestions
        self.confusion_matrix = ConfusionMatrix()
        self.metrics.set_value(RecommenderMetric.recommendation_progress, value=0)
        self.metrics.set_value(RecommenderMetric.recommendation_progress_with_ground_truth, value=0)

    def all_suggestions_uptodate(self):
        """Inform the tracker that all suggestions are up-to-date."""
        self.metrics.increment(RecommenderMetric.recommendation_finishes_total)

    def new_uptodate_suggestions(self, attributes: Collection[AttributeId], suggestions_batch: Collection[Suggestions]):
        """Inform the tracker that new up-to-date suggestions exist."""
        self.metrics.increment(RecommenderMetric.recommendation_progress, amount=len(attributes))

        for attribute, suggestions_with_confidence in zip(attributes, suggestions_batch):
            assigned = self.assigned_terms.get(attribute)
            if assigned:
                self.metrics.increment(RecommenderMetric.recommendation_progress_with_ground_truth)

                assignments = assigned - self.disabled_terms  # Ground truth
                suggestions = {term for term, _ in suggestions_with_confidence}  # Prediction

                self.confusion_matrix.true_positive += len(assignments & suggestions)
                self.confusion_matrix.false_positive += len(suggestions - assignments)
                self.confusion_matrix.false_negative += len(assignments - suggestions)
                self.confusion_matrix.true_negative += len(self.known_terms - (assignments | suggestions))

    def suggestions_batch_processed(
        self, attributes: Collection[AttributeId], suggestions_batch: Collection[Suggestions]
    ):
        """Inform the tracker that a batch of suggestions was processed and new up-to-date suggestions exist."""
        suggestion_count = sum(len(suggestions) for suggestions in suggestions_batch)
        self.metrics.increment(RecommenderMetric.attributes_processed_total, amount=len(attributes))
        self.metrics.increment(RecommenderMetric.suggestions_created_total, amount=suggestion_count)
        self.new_uptodate_suggestions(attributes, suggestions_batch)


class RecommenderService(Microservice):
    """Calculates recommended terms for batches of influenced attributes."""

    def __init__(self, config):
        super().__init__("recommender", config, period=config.db_poll_period)

        self.add_external_dependency("neighbors")
        self.grpc_server()
        self.neighbors_client = self.grpc_client("neighbors")
        self.dao = TSDAO(self.database())
        self.wsgi = self.wsgi_server()

        self.assigned_terms = {}
        self.assigned_terms_table = PolledTable(
            self.dao.assigned_terms, [self.dao.assigned_terms.c.attribute_id, self.dao.assigned_terms.c.terms]
        )

        self.rejected_terms = {}
        self.rejected_terms_table = PolledTable(
            self.dao.rejected_terms, [self.dao.rejected_terms.c.attribute_id, self.dao.rejected_terms.c.terms]
        )

        self.disabled_terms = {}
        self.disabled_terms_table = PolledTable(
            self.dao.disabled_terms,
            [self.dao.disabled_terms.c.term_id, self.dao.disabled_terms.c.deleted],
            row_validator=lambda row: not row[1],
        )  # Disabled terms with deleted flag set to True are re-enabled - delete them from disabled terms when polling

        self.similarity_thresholds = {}
        self.similarity_thresholds_table = PolledTable(
            self.dao.similarity_thresholds,
            [self.dao.similarity_thresholds.c.term_id, self.dao.similarity_thresholds.c.value],
        )

        self.term_cache = DBPoller(
            self.dao,
            [
                self.assigned_terms_table,
                self.rejected_terms_table,
                self.disabled_terms_table,
                self.similarity_thresholds_table,
            ],  # up to 100k (400k theoretical limit) frequently-read but seldom updated rows per cached table
        )
        self.recommender = Recommender(
            self.config,
            self.assigned_terms,
            self.rejected_terms,
            self.disabled_terms.keys(),
            self.similarity_thresholds,
        )

        self.all_suggestions_uptodate = False

        self.fingerprints_freshness = SQL_DATETIME_MIN
        self.terms_freshness = SQL_DATETIME_MIN
        self.thresholds_freshness = SQL_DATETIME_MIN

        self.metrics_tracker = RecommenderMetricsTracker(self.metrics)

    def on_start(self):
        """Update the cache on start."""
        self.process_changes(first_run=True)

    def process_once_per_period(self) -> None:
        """Keep the cache up-to-date."""
        self.process_changes()

    def process_changes(self, first_run: bool = False) -> None:
        """Process newest terms and thresholds updates from the DB."""
        changes = self.term_cache.poll()
        fingerprints_freshness = self.dao.get_fingerprints_freshness()
        terms_freshness, thresholds_freshness = self._get_terms_and_thresholds_freshnesses()

        self.update_cache(changes, terms_freshness, thresholds_freshness)
        self.update_freshness(fingerprints_freshness, terms_freshness, thresholds_freshness, first_run)

    def update_cache(
        self, changes: CachedTables, terms_freshness: datetime.datetime, thresholds_freshness: datetime.datetime
    ) -> None:
        """Update terms and thresholds cache based on supplied changes."""
        change_counters = collections.Counter()

        POLLED_TABLE_CACHES = [
            (self.assigned_terms, self.assigned_terms_table),
            (self.rejected_terms, self.rejected_terms_table),
            (self.disabled_terms, self.disabled_terms_table),
            (self.similarity_thresholds, self.similarity_thresholds_table),
        ]

        for cache, polled_table in POLLED_TABLE_CACHES:
            for row in changes[polled_table.table.name]:
                change_type = self.update_cached_row(polled_table, cache, row)
                change_counters[change_type] += 1

        if change_counters[CacheChange.update] or change_counters[CacheChange.delete]:
            self.logger.info(
                "Term and threshold cache updated: {update_count} updated, {delete_count} deleted, last modified {freshness}",  # noqa: E501
                update_count=change_counters[CacheChange.update],
                delete_count=change_counters[CacheChange.delete],
                freshness=datetime_str(max(terms_freshness, thresholds_freshness)),
                message_id=LogId.recommender_cache_update,
            )

    @classmethod
    def update_cached_row(cls, polled_table: PolledTable, cache: dict, row: list[Any]) -> Optional[CacheChange]:
        """Update cache based on single row."""
        primary_key, *data = row
        is_update = polled_table.row_validator(row)

        if is_update:
            extracted_data = data[0] if len(data) == 1 else data  # Extract if there is only one cell
            cache[primary_key] = extracted_data

            return CacheChange.update
        else:
            if primary_key in cache:  # Delete only if present in the cache
                del cache[primary_key]

                return CacheChange.delete

        return None  # Cache not updated

    def update_freshness(
        self,
        new_fingerprints_freshness: datetime.datetime,
        new_terms_freshness: datetime.datetime,
        new_thresholds_freshness: datetime.datetime,
        first_run: bool,
    ) -> None:
        """Update freshness for all watched data."""
        fingerprints_changed = self.fingerprints_freshness != new_fingerprints_freshness
        terms_changed = self.terms_freshness != new_terms_freshness
        thresholds_changed = self.thresholds_freshness != new_thresholds_freshness
        data_changed = fingerprints_changed or terms_changed or thresholds_changed

        self.fingerprints_freshness = new_fingerprints_freshness
        self.terms_freshness = new_terms_freshness
        self.thresholds_freshness = new_thresholds_freshness

        if terms_changed:
            self.metrics_tracker.terms_updated(self.assigned_terms, self.rejected_terms, self.disabled_terms.keys())

        if fingerprints_changed:
            self.logger.info(
                "Fingerprints were modified since last poll, last modified {freshness}",
                freshness=datetime_str(self.fingerprints_freshness),
                message_id=LogId.recommender_fingerprints_changed,
            )

        # During the first run we can't tell if the suggestions are up-to-date until process_frequently() is called
        if data_changed and not first_run:
            self.all_suggestions_uptodate = False
            self.metrics_tracker.all_suggestions_outdated()
            self.logger.info(
                "Underlying data were modified, all suggestions have to be recalculated",
                message_id=LogId.recommender_recalculate_all_suggestions,
            )

    def process_frequently(self) -> bool:
        """Recommend and persist terms for a batch of the least fresh attributes."""
        if self.all_suggestions_uptodate:
            return True  # Nothing to do

        desired_batch_size = self.config.recommender_batch_size  # Processing should take ~ seconds
        data_freshness = max(self.fingerprints_freshness, self.terms_freshness, self.thresholds_freshness)
        attributes = self.dao.get_outdated_attributes(desired_batch_size, data_freshness)

        if attributes:  # Some attributes have outdated suggested terms => (re)calculate up-to-date ones for them
            correlation_id = random_correlation_id()
            suggestions_batch = self.recommend(attributes, correlation_id)
            self.dao.set_suggestions_batch(attributes, suggestions_batch, data_freshness)

            attribute_count = len(attributes)
            suggestion_count = sum(len(suggestions) for suggestions in suggestions_batch)
            self.logger.info(
                "Created suggestions for {attribute_count} attributes (total {suggestion_count} suggestions)",
                attribute_count=attribute_count,
                suggestion_count=suggestion_count,
                correlation_id=correlation_id,
                message_id=LogId.recommender_batch_suggest,
            )
            self.metrics_tracker.suggestions_batch_processed(attributes, suggestions_batch)

        # All suggestions are up-to-date once we process an incomplete batch
        if len(attributes) != desired_batch_size and not self.all_suggestions_uptodate:
            self.all_suggestions_uptodate = True
            self.metrics_tracker.all_suggestions_uptodate()
            self.logger.info("All suggestions are up-to-date", message_id=LogId.recommender_all_suggestions_uptodate)

        return self.all_suggestions_uptodate

    def recommend(self, attributes: list[AttributeId], correlation_id: CorrelationId) -> list[Suggestions]:
        """Recommend terms for a batch of attributes."""
        neighbors_command = commands.GetTopKNeighborsCommand(attributes, self.fingerprints_freshness)
        self.neighbors_client.send(neighbors_command, correlation_id)

        if neighbors_command.cache_freshness < neighbors_command.desired_cache_freshness:
            self.logger.error(
                "Received neighbors are based on outdated fingerprints ({actual} instead of {desired}), refusing to recommend",  # noqa: E501
                actual=datetime_str(neighbors_command.cache_freshness),
                desired=datetime_str(neighbors_command.desired_cache_freshness),
                correlation_id=correlation_id,
                message_id=LogId.recommender_outdated_fingerprints,
            )  # Check the log of Neighbors for last fingerprint cache update
            raise FreshnessError("Neighbors are based on outdated fingerprints")

        return self.recommender.batch_recommend(neighbors_command.neighbors_batch)

    def _get_terms_and_thresholds_freshnesses(self) -> tuple[datetime.datetime, datetime.datetime]:
        """Get terms freshness and thresholds freshness of the cache."""
        terms_table_names = [
            self.dao.assigned_terms.name,
            self.dao.rejected_terms.name,
            self.dao.disabled_terms.name,
        ]
        thresholds_table_name = self.dao.similarity_thresholds.name

        terms_freshness = max(self.term_cache.last_modified[name] for name in terms_table_names)
        thresholds_freshness = self.term_cache.last_modified[thresholds_table_name]
        return terms_freshness, thresholds_freshness


class NeighborsService(Microservice):
    """Finds the most similar attributes based on their fingerprints."""

    def __init__(self, config):
        super().__init__("neighbors", config, period=config.db_poll_period)

        self.serializer = BLOBSerializer()
        self.dao = TSDAO(self.database())

        self.fingerprints_table = PolledTable(
            self.dao.attributes,
            [self.dao.attributes.c.attribute_id, self.dao.attributes.c.fingerprint, self.dao.attributes.c.deleted],
            row_validator=lambda row: not row[2],  # Deleted flag means attribute is deleted
        )

        self.changed_fingerprints = DBPoller(self.dao, [self.fingerprints_table])

        self.attribute_limit = AttributeLimit(
            "attribute_limit",
            self.logger,
            self.retrying_controller(on_start=True),
            self.dao,
            limit=self.config.neighbors_index_limit,
        )
        self.contained_resources.add(self.attribute_limit)

        self.neighbors: Optional[NeighborsCalculator] = None

        self.grpc_server(commands=[commands.GetTopKNeighborsCommand])
        self.wsgi = self.wsgi_server()

        self.fingerprints_freshness: datetime.datetime = SQL_DATETIME_MIN

        self.metrics.register(NeighborsMetric)
        self.metrics.set_value(NeighborsMetric.index_attributes_limit, value=self.attribute_limit.limit)

    def on_start(self):
        """Update the fingerprints cache on start."""
        self.neighbors = NeighborsCalculator(FingerprintsIndex(self.attribute_limit.limit))
        self.process_changes(first_run=True)

    def process_once_per_period(self):
        """Keep the fingerprint cache up-to-date."""
        self.process_changes()

    def process_changes(self, first_run: bool = False):
        """Update the fingerprints by changes since last poll."""
        changes = self.changed_fingerprints.poll()
        fingerprints_freshness = self.changed_fingerprints.last_modified[self.dao.attributes.name]

        self.update_cache(changes, fingerprints_freshness)

        if self.fingerprints_freshness != fingerprints_freshness or first_run:
            self.fingerprints_freshness = fingerprints_freshness
            self.metrics.set_value(NeighborsMetric.database_attributes_present, value=self.dao.get_attribute_count())
            self.metrics.set_value(
                NeighborsMetric.index_attributes_present, value=len(self.neighbors.fingerprints_index)
            )
        # Detection of neighboring attributes is done by gRPC server, see GetTopKNeighborsCommand

    def update_cache(self, changes: CachedTables, fingerprints_freshness: datetime.datetime) -> None:
        """Update fingerprints index based on supplied changes."""
        change_counters = collections.Counter()

        for row in changes[self.fingerprints_table.table.name]:
            change_type = self.update_cached_row(row)
            change_counters[change_type] += 1

        if change_counters[CacheChange.update] or change_counters[CacheChange.delete]:
            self.logger.info(
                "Updated the fingerprint cache: {present_count} present, {update_count} updated, {delete_count} deleted, last modified {freshness}",  # noqa: E501
                present_count=len(self.neighbors.fingerprints_index),
                update_count=change_counters[CacheChange.update],
                delete_count=change_counters[CacheChange.delete],
                freshness=datetime_str(fingerprints_freshness),
                message_id=LogId.neighbors_cache_update,
            )

    def update_cached_row(self, row: list[Any]) -> Optional[CacheChange]:
        """Update cache based on single row."""
        fingerprints_index = self.neighbors.fingerprints_index

        attribute_id, fingerprint, _ = row
        is_update = self.fingerprints_table.row_validator(row)

        if is_update:
            fingerprints_index[attribute_id] = fingerprint

            return CacheChange.update
        else:
            if attribute_id in fingerprints_index:  # Delete only if present in the cache
                del fingerprints_index[attribute_id]

                return CacheChange.delete

        return None  # Cache not updated

    def run_processing_forever(self, processing_thread_health: Health):
        """Process work as usual, additionally trigger graceful shutdown on index full exception."""
        try:
            super().run_processing_forever(processing_thread_health)
        except FingerprintsIndexFullError:
            self.logger.error(
                "The fingerprint cache limit={limit} got exceeded as the DB contains {attribute_count!r} attributes => shutting down",  # noqa: E501
                limit=self.neighbors.fingerprints_index.capacity,
                attribute_count=self.dao.get_attribute_count(),
                message_id=LogId.neighbors_cache_limit_exceeded,
            )
            self.shutdown()  # Trigger shutdown of the microservice
            # No resource should shut itself down before it's asked to do so
            sleep_between_periods(processing_thread_health, sleep=math.inf)  # Stay alive until asked to shut down


class FeedbackService(Microservice):
    """Re-trains term similarity thresholds based on accepted/rejected recommendations."""

    def __init__(self, config):
        super().__init__("feedback", config, period=config.db_poll_period)

        self.dao = TSDAO(self.database())
        self.calculator = ThresholdCalculator(self.config)
        self.grpc_server(commands=[commands.SetThresholdCommand, commands.SetAdaptiveLearningCommand])
        self.wsgi = self.wsgi_server()

        self.metrics.register(FeedbackMetric)

    def on_start(self):
        """Load all term similarity thresholds and learning strategies from the database."""
        thresholds = self.dao.get_similarity_thresholds()
        learning_strategies = self.dao.get_learning_strategies()

        self.calculator.thresholds.update(thresholds)
        self.calculator.learning_enabled.update(learning_strategies)
        self.update_thresholds_metrics()

        self.logger.info(
            "Updated the cache: {threshold_count} thresholds, {learning_strategy_count} learning strategies",
            threshold_count=len(thresholds),
            learning_strategy_count=len(learning_strategies),
            message_id=LogId.feedback_cache_update,
        )

    def process_frequently(self) -> bool:
        """Update term similarity thresholds based on a batch of feedback from users."""
        feedback_ids, feedbacks = self.dao.get_feedbacks(self.config.feedback_batch_size)
        if not feedbacks:
            return True

        thresholds = self.calculator.process_feedbacks(feedbacks)
        correlation_id = random_correlation_id()
        # Must be performed even if thresholds are empty - deletes the processed feedbacks
        self.dao.set_similarity_thresholds(thresholds, correlation_id, feedback_ids)
        self.update_feedbacks_metrics(feedbacks)
        self.update_thresholds_metrics()

        if thresholds:
            self.logger.info(
                "Recalculated {threshold_count} thresholds based on {feedback_count} feedbacks",
                threshold_count=len(thresholds),
                feedback_count=len(feedbacks),
                message_id=LogId.feedback_recalculate,
                correlation_id=correlation_id,
            )

        # All feedbacks are processed if the batch was not complete
        return len(feedbacks) < self.config.feedback_batch_size

    def update_feedbacks_metrics(self, feedbacks: Feedbacks):
        """Update metrics related to feedbacks."""
        for _, feedback in feedbacks:
            feedback_type = "positive" if feedback else "negative"
            self.metrics.increment(FeedbackMetric.feedbacks_total, type=feedback_type)

    def update_thresholds_metrics(self):
        """Update metrics related to distance thresholds."""
        for threshold in self.calculator.thresholds.values():
            self.metrics.observe(FeedbackMetric.thresholds, amount=threshold)


MICROSERVICES = {
    RECOMMENDER: RecommenderService,
    NEIGHBORS: NeighborsService,
    FEEDBACK: FeedbackService,
}
