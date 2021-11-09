"""All action, message and event ids used in Term Suggestions logging messages."""
from __future__ import annotations

import enum
import math

from aicore.common.metrics import MetricEnum, MetricType


class LogId(enum.Enum):
    """Enum for all action, message and event ids used in Term Suggestions logging."""

    recommender_all_suggestions_uptodate = enum.auto()
    recommender_batch_suggest = enum.auto()
    recommender_cache_update = enum.auto()
    recommender_fingerprints_changed = enum.auto()
    recommender_outdated_fingerprints = enum.auto()
    recommender_recalculate_all_suggestions = enum.auto()
    feedback_cache_update = enum.auto()
    feedback_recalculate = enum.auto()
    neighbors_cache_update = enum.auto()
    neighbors_cache_limit_exceeded = enum.auto()
    neighbors_too_many_attributes = enum.auto()

    def __repr__(self):
        return self.name


class RecommenderMetric(MetricEnum):
    """Metrics collected in the recommender service."""

    __name_prefix__ = "ai_ts_recommender"

    attributes_processed_total = (MetricType.counter, "The number of attributes for which suggestions were computed.")
    suggestions_created_total = (MetricType.counter, "The number of suggestions created.")

    terms_known = (MetricType.gauge, "The number of known terms.")
    terms_disabled = (MetricType.gauge, "The number of disabled terms.")

    recommendation_starts_total = (MetricType.counter, "The number of times all suggestions were rendered outdated.")
    recommendation_finishes_total = (MetricType.counter, "The number of times all suggestions were brought up to date.")

    recommendation_progress = (MetricType.gauge, "The number of attributes that have up-to-date suggestions.")
    recommendation_progress_with_ground_truth = (
        MetricType.gauge,
        "The number of attributes that have up-to-date suggestions and for which the ground truth is known.",
    )

    suggestions_confusion_matrix = (
        MetricType.gauge,
        "The confusion matrix computed between suggestions and assigned terms.",
        ["entry"],
    )


class NeighborsMetric(MetricEnum):
    """Metrics collected in the neighbors service."""

    __name_prefix__ = "ai_ts_neighbors"

    database_attributes_present = (
        MetricType.gauge,
        "The number of attributes available to the Term Suggestions microservices. Warning: The value might be overestimated.",  # noqa E501
    )
    index_attributes_present = (MetricType.gauge, "The number of attributes currently stored in the memory.")
    index_attributes_limit = (MetricType.gauge, "The maximum number of attributes that can be stored in the memory.")
    neighbors_distances = (
        MetricType.histogram,
        "Distances to k-th nearest neighbors.",
        ["k"],
        # Logarithmic scale: 0.01 * (10 ** (i/2))
        # Distances are from [0, sqrt(128)≈11.313]
        {"buckets": (0.01, 0.0316, 0.1, 0.316, 1.0, 3.16, math.inf)},
    )


class FeedbackMetric(MetricEnum):
    """Metrics collected in the feedback service."""

    __name_prefix__ = "ai_ts_feedback"

    feedbacks_total = (
        MetricType.counter,
        "The total number of positive or negative feedbacks received from users.",
        ["type"],
    )
    thresholds = (
        MetricType.histogram,
        "The current distance thresholds.",
        [],
        # Logarithmic scale: 0.01 * (10 ** (i/4))
        # Distances are from [0, sqrt(128)≈11.313] and thresholds shouldn't climb over this either
        {"buckets": (0.01, 0.0177, 0.0316, 0.0562, 0.1, 0.177, 0.316, 0.562, 1.0, 1.77, 3.16, math.inf)},
    )


METRICS = [RecommenderMetric, NeighborsMetric, FeedbackMetric]
