"""Microservices (processes or Docker containers) provided by Term Suggestions."""
from __future__ import annotations

from aicore.anomaly_detection import ANOMALY_DETECTOR, commands
from aicore.anomaly_detection.registry import AnomalyDetectionMetric
from aicore.common.microservice import Microservice


class AnomalyDetectorService(Microservice):
    """Analyze received profiles for anomalies."""

    def __init__(self, config):
        super().__init__("anomaly_detector", config)

        self.mmm_client = self.grpc_client("mmm")

        self.grpc_server(commands=[commands.DetectAnomaliesCommand])
        self.wsgi = self.wsgi_server()

        self.add_external_dependency("mmm")
        self.metrics.register(AnomalyDetectionMetric)


MICROSERVICES = {
    ANOMALY_DETECTOR: AnomalyDetectorService,
}
