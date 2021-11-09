"""Microservice configuration."""

from __future__ import annotations

from aicore.common.config import ConfigOptionsBuilder, connection_options, server_options


CONFIG_OPTIONS = (
    ConfigOptionsBuilder()
    .common_options("microservice_commons", "mmm")
    .start_section("Anomaly detection", 130)
    .create_options(
        lambda builder: server_options(
            builder,
            module_name="Anomaly detection",
            microservice_name="Anomaly Detector",
            grpc_port=8547,
            http_port=8047,
        )
    )
    .create_options(
        lambda builder: connection_options(builder, server_name="Anomaly Detector microservice", http_port=8047)
    )
    .option(
        "anomaly_detector_max_history_length",
        "ataccama.one.aicore.anomaly-detection.anomaly-detector.max-history-length",
        int,
        """The maximum number of catalog item profile versions fetched from MMM on which anomaly detection is run. If
        the total number of profile versions in MMM exceeds the value set for this property, the versions are retrieved
        starting from the most recent. For example, if there are 30 profile versions in MMM and the property is set to
        100, all 30 versions are fetched. However, if there are 200 profile versions in MMM and the value provided is
        100, the last 100 profile versions are retrieved.""",
        default_value=100,
    )
    .option(
        "anomaly_detector_isolation_forest_threshold",
        "ataccama.one.aicore.anomaly-detection.anomaly-detector.isolation-forest-threshold",
        float,
        """An internal parameter for the time-independent anomaly detection model (Isolation Forest) that defines the
        sensitivity of anomaly detection. Setting the value higher than the default value (for example, -0.5) can
        result in more false positive anomalies, while setting it lower than the default value (for example, -0.7) can
        lead to more false negative anomalies.""",
        default_value=-0.6,
    )
    .option(
        "anomaly_detector_time_series_std_threshold",
        "ataccama.one.aicore.anomaly-detection.anomaly-detector.time-series-std-threshold",
        float,
        """An internal parameter for the time-dependent anomaly detection model (time series analysis) that defines the
        sensitivity of anomaly detection. The property describes the number of standard deviations (std) from the mean
        after which a point is considered as anomalous. Setting the value higher than the default value (for example, 4)
        reduces the total number of anomalies and results in more false negative anomalies, while setting it lower than
        the default value (for example, 2) increases the total number of detected anomalies and results in more false
        positive anomalies.""",
        default_value=3.0,
    )
    .end_section()
    .options
)
