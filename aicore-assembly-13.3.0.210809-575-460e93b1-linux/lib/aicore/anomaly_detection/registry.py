"""AI metrics for Anomaly Detection to measure performance and behaviour of the module."""
from __future__ import annotations

from aicore.common.metrics import MetricEnum, MetricType


class AnomalyDetectionMetric(MetricEnum):
    """Definition of Anomaly detection metrics."""

    __name_prefix__ = "ai_ad"

    n_ad_requests_total = (
        MetricType.counter,
        "The number of requests for anomaly detection issued from MMM.",
    )

    duration_of_get_history_from_mmm_command_seconds = (
        MetricType.summary,
        "The number of seconds needed for fetching and processing data from MMM.",
    )

    n_fetched_data_points_total = (
        MetricType.summary,
        "The number of data points (for example, profiling versions) that were fetched from MMM.",
    )

    # How long anomaly detection (fit and predict method) takes per chosen model; Isolation Forest or Time series
    duration_of_ad_per_model_seconds = (
        MetricType.summary,
        "The number of seconds needed to complete anomaly detection processing for the chosen model.",
        ["model_type"],
    )

    n_positive_anomaly_feedbacks_total = (
        MetricType.summary,
        "The number of confirmed anomalies (feedback) that users provided.",
    )

    n_detected_anomalous_data_points_total = (
        MetricType.summary,
        "The number of data points that were identified as anomalous by the model.",
    )


METRICS = [AnomalyDetectionMetric]
