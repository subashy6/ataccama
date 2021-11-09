"""De-/serialization and server-side handling of gRPC commands for Anomaly Detection."""
from __future__ import annotations

from typing import TYPE_CHECKING

import aicore.anomaly_detection.feature_provider as feature_provider
import aicore.anomaly_detection.proto.anomaly_detection_pb2 as ad_proto

from aicore.anomaly_detection.anomaly_detector import IsolationForestModel, TimeSeriesAnalysisModel, select_model_class
from aicore.anomaly_detection.definitions import Category
from aicore.anomaly_detection.registry import AnomalyDetectionMetric
from aicore.common.command import Command
from aicore.common.metrics import MetricsDAO


if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Optional

    from aicore.anomaly_detection.definitions import AnomalyDetectorModelBase
    from aicore.anomaly_detection.microservices import AnomalyDetectorService
    from aicore.anomaly_detection.types import EntityType, Feedbacks, GenericHCN, GenericHCNs, GenericId
    from aicore.common.auth import Identity
    from aicore.common.types import CorrelationId


class DetectAnomaliesCommand(Command):
    """Detect anomalies for the requested data and requested entity type based on its own history (HCNs)."""

    service = "ataccama.aicore.anomaly_detection.AnomalyDetectionService"
    method = "DetectAnomalies"
    request_class = ad_proto.DetectAnomaliesRequest
    response_class = ad_proto.DetectAnomaliesResponse
    __slots__ = ("entity_id", "entity_type", "hcn", "periodicity", "model", "categories")

    # ModelType.V are the enum proto values
    MODEL_PROTO_TYPES: dict[type[AnomalyDetectorModelBase], ad_proto.ModelType.V] = {
        IsolationForestModel: ad_proto.ModelType.TIME_INDEPENDENT,
        TimeSeriesAnalysisModel: ad_proto.ModelType.TIME_DEPENDENT,
    }

    def __init__(
        self,
        entity_id: GenericId,
        entity_type: EntityType,
        hcn: GenericHCN,
        periodicity: int,
    ):
        self.entity_id: GenericId = entity_id
        self.entity_type: EntityType = entity_type
        self.hcn: GenericHCN = hcn
        self.periodicity: int = periodicity  # [samples = days, hours etc.] Default value of 0.

        self.model: Optional[AnomalyDetectorModelBase] = None  # Default model
        self.categories: list[Category] = []

    def __repr__(self) -> str:
        return f"DetectAnomaliesCommand({self.entity_id, self.hcn, self.entity_type, self.periodicity})"

    @classmethod
    def deserialize_from_client(cls, request: ad_proto.DetectAnomaliesRequest) -> DetectAnomaliesCommand:
        """Create an instance of the command based on request."""
        return cls(request.id, request.entity_type, request.hcn, request.periodicity)

    def process(
        self,
        microservice: AnomalyDetectorService,
        correlation_id: CorrelationId,
        _identity: Optional[Identity] = None,
    ) -> None:
        """Set command's state based on results provided by given microservice."""
        metrics = microservice.metrics
        metrics.increment(AnomalyDetectionMetric.n_ad_requests_total)

        history_length = microservice.config.anomaly_detector_max_history_length
        # List of categories created inside GetHistoryCommand
        history_command = GetHistoryCommand(self.entity_id, self.entity_type, self.hcn, history_length, metrics)

        with metrics.measure_time(AnomalyDetectionMetric.duration_of_get_history_from_mmm_command_seconds):
            microservice.mmm_client.send(history_command, correlation_id)

        model_class = select_model_class(self.periodicity)
        self.model = model_class(microservice.config, history_command.hcns)

        self.categories = history_command.categories
        with metrics.measure_time(
            AnomalyDetectionMetric.duration_of_ad_per_model_seconds, model_type=self.model.__repr__()
        ):
            for category in self.categories:
                category.set_category_attributes(self.periodicity, history_command.feedbacks)
                self.model.fit_and_predict(category)

    @classmethod
    def serialize_response_model(
        cls, model: AnomalyDetectorModelBase, categories: list[Category]
    ) -> ad_proto.ModelType.V:
        """Serialize implicit used anomaly detection model to proto model type."""
        if not Category.any_evaluated_category(categories):
            # if not model.anomaly_detection_applied:
            return ad_proto.ModelType.ANOMALY_DETECTION_NOT_PERFORMED

        return cls.MODEL_PROTO_TYPES[type(model)]

    def serialize_for_client(self) -> ad_proto.DetectAnomaliesResponse:
        """Set attributes of a gRPC response (Serialize) based on internal state."""
        response = self.response_class()
        response.id = self.entity_id
        response.entity_type = self.entity_type
        response.model = self.serialize_response_model(self.model, self.categories)
        self.serialize_data_points(response)

        return response

    def serialize_data_points(self, response: ad_proto.DetectAnomaliesResponse):
        """Serialize data points to proto response if anomaly detection was performed."""
        if response.model == ad_proto.ModelType.ANOMALY_DETECTION_NOT_PERFORMED:
            return

        # We iterate in reverse order due to potential cut off at the beginning
        for index_from_end, hcn in enumerate(reversed(self.model.hcns)):
            detected_data_point: ad_proto.DetectedDataPoint = response.detected_data_points.add()
            detected_data_point.hcn = hcn
            detected_data_point.anomalous = Category.any_anomalous_category(self.categories, index_from_end)
            categories_results = self.serialize_category_results(index_from_end)
            detected_data_point.categories_results.extend(categories_results)

    def serialize_category_results(self, index_from_end: int) -> list[ad_proto.CategoryResult]:
        """Serialize category results to proto results per data point."""
        categories_results: list[ad_proto.CategoryResult] = []
        # Categories which were not cut off for the given index
        for category in Category.get_usable_categories(self.categories, index_from_end):
            category_result = ad_proto.CategoryResult()
            category_result.category_name = category.name
            category_result.anomaly_score = category.result.get_score(index_from_end)
            category_result.anomalous = category.result.get_prediction(index_from_end)
            self.serialize_feature_results(category, category_result, index_from_end)

            categories_results.append(category_result)

        return categories_results

    def serialize_feature_results(
        self, category: Category, category_result: ad_proto.CategoryResult, index_from_end: int
    ):
        """Serialize feature results to proto results per data point."""
        for feature_name, score, prediction, bounds in category.result.iter_feature_results(index_from_end):
            feature_result: ad_proto.FeatureResult = category_result.features_results[feature_name]
            feature_result.anomaly_score = score
            # For Isolation forest only features from anomalous category are saved, for Time series all are saved
            feature_result.anomalous = prediction
            # For Isolation Forest the bounds are all 0
            feature_result.expected_value_lower_bound = bounds.min_bound
            feature_result.expected_value = bounds.mean_value
            feature_result.expected_value_upper_bound = bounds.max_bound


class GetHistoryCommand(Command):
    """Fetch last n data versions with HCN for anomaly detection."""

    service = "ataccama.aicore.anomaly_detection.DataProviderService"
    method = "GetHistory"
    method_type = "unary_stream"  # Response is a stream of data to be detected for anomalies
    request_class = ad_proto.GetHistoryRequest
    response_class = ad_proto.GetHistoryResponse

    __slots__ = (
        "entity_id",
        "entity_type",
        "hcn",
        "history_length",
        "metrics",
        "hcns",
        "feedbacks",
        "categories",
        "fetched_history_length",
    )

    def __init__(
        self,
        entity_id: GenericId,
        entity_type: EntityType,
        hcn: GenericHCN,
        history_length: int,
        metrics: MetricsDAO,
    ):
        # Identification of the entity for which AD is requested, (attribute ID, catalog ID, etc.)
        self.entity_id: GenericId = entity_id
        self.entity_type: EntityType = entity_type  # e.g. catalog-level, attribute-level, DQ rule
        self.hcn: GenericHCN = hcn  # History change number of the version of the data
        self.history_length = history_length  # Maximum number of data version to be fetched
        self.metrics = metrics  # AI metrics to measure performance and behaviour of anomaly detector

        self.hcns: GenericHCNs = []  # History change numbers for all fetched data versions
        self.feedbacks: Feedbacks = []  # Feedback for each fetched data instance
        self.categories: list[Category] = []  # Collection of categories to run chosen AD model on
        self.fetched_history_length: int = 0  # Number of history versions fetched from MMM

    def __repr__(self) -> str:
        return f"GetHistoryCommand({self.entity_id, self.entity_type, self.hcn, self.history_length}]"

    def serialize_for_server(self) -> ad_proto.GetHistoryRequest:
        """Set attributes of a gRPC request based on internal state."""
        request = self.request_class()
        request.id = self.entity_id
        request.entity_type = self.entity_type
        request.hcn = self.hcn
        request.history_length = self.history_length

        return request

    def deserialize_from_server(self, response: Iterable[ad_proto.GetHistoryResponse]):
        """Set command's state based on protobuf response message."""
        response = list(response)

        self.hcns = [data_version.hcn for data_version in response]
        self.feedbacks = [data_version.feedback == ad_proto.FeedbackType.ANOMALOUS for data_version in response]
        # We take sum of feedbacks to get how many positive (true = 1) feedbacks were there
        self.metrics.observe(AnomalyDetectionMetric.n_positive_anomaly_feedbacks_total, sum(self.feedbacks))

        self.categories = feature_provider.deserialize_to_categories(response)
        self.fetched_history_length = len(response)

        self.metrics.observe(AnomalyDetectionMetric.n_fetched_data_points_total, self.fetched_history_length)
