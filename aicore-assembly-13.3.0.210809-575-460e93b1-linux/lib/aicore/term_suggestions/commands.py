"""De-/serialization and server-side handling of gRPC commands for Term Suggestions."""

from __future__ import annotations

import datetime

from typing import TYPE_CHECKING, Optional

import aicore.term_suggestions.proto.term_suggestions_pb2 as ts_proto

from aicore.common.command import Command
from aicore.common.utils import DATETIME_MIN, datetime_str, deserialize_entity_id, serialize_entity_id
from aicore.term_suggestions.registry import NeighborsMetric


if TYPE_CHECKING:
    from aicore.common.auth import Identity
    from aicore.common.metrics import MetricsDAO
    from aicore.common.types import CorrelationId
    from aicore.term_suggestions.microservices import FeedbackService, NeighborsService
    from aicore.term_suggestions.types import AttributeId, Neighbors, TermId


class GetTopKNeighborsCommand(Command):
    """Find the most similar attributes for each given attribute based on their fingerprints."""

    service = "ataccama.aicore.term_suggestions.TermSuggestions"
    method = "GetTopKNeighbors"
    request_class = ts_proto.GetTopKNeighborsRequest
    response_class = ts_proto.GetTopKNeighborsResponse
    __slots__ = ("attributes", "desired_cache_freshness", "neighbors_batch", "cache_freshness")

    def __init__(
        self,
        attributes: list[AttributeId],
        desired_freshness: datetime.datetime = DATETIME_MIN,
    ):
        self.attributes = attributes
        self.desired_cache_freshness = desired_freshness  # How fresh cache is desired when processing this command

        self.cache_freshness = DATETIME_MIN  # How fresh the cache actually was when this command was processed
        self.neighbors_batch: list[Neighbors] = []

    def __repr__(self):
        printed_attributes = 2

        attributes = str(self.attributes[:printed_attributes])
        if len(self.attributes) >= printed_attributes:
            attributes = f"{attributes[:-1]}, ...]"  # "[1, 2]" => "[1, 2, ...]"

        return f"GetTopKNeighborsCommand({attributes}, {datetime_str(self.desired_cache_freshness)})"

    def serialize_for_server(self) -> ts_proto.GetTopKNeighborsRequest:
        """Create a gRPC request based on the command's requested attributes."""
        request = self.request_class()
        request.desired_cache_freshness.FromDatetime(self.desired_cache_freshness)

        for attribute in self.attributes:
            attribute_proto = request.attributes.add()
            attribute_proto.id = serialize_entity_id(attribute)

        return request

    def deserialize_from_server(self, response: ts_proto.GetTopKNeighborsResponse) -> None:
        """Set neighbors for each attribute based on the response."""
        self.neighbors_batch = []

        self.cache_freshness = response.cache_freshness.ToDatetime().replace(tzinfo=datetime.timezone.utc)
        for neighbors_proto in response.neighbors_batch:
            neighbors = [
                (deserialize_entity_id(neighbor_proto.id), neighbor_proto.distance)
                for neighbor_proto in neighbors_proto.neighbors
            ]
            self.neighbors_batch.append(neighbors)

    @classmethod
    def deserialize_from_client(cls, request: ts_proto.GetTopKNeighborsRequest) -> GetTopKNeighborsCommand:
        """Create the command from given protobuf message."""
        return cls(
            attributes=[deserialize_entity_id(attribute_proto.id) for attribute_proto in request.attributes],
            desired_freshness=request.desired_cache_freshness.ToDatetime().replace(tzinfo=datetime.timezone.utc),
        )

    def process(
        self,
        microservice: NeighborsService,
        _correlation_id: CorrelationId,
        _identity: Optional[Identity] = None,
    ) -> None:
        """Compute nearest neighbors for each attribute."""
        desired_neighbors_count = 20

        if microservice.fingerprints_freshness < self.desired_cache_freshness:
            microservice.process_changes()  # Update fingerprints cache if it isn't fresh enough

        self.cache_freshness = microservice.fingerprints_freshness
        self.neighbors_batch = microservice.neighbors.top_k(self.attributes, desired_neighbors_count)
        self.update_metrics(microservice.metrics)

    def update_metrics(self, metrics: MetricsDAO):
        """Update metrics affected by this command."""
        measured_neighbors_count = 5

        for neighbors in self.neighbors_batch:
            for k, (_, distance) in enumerate(neighbors[:measured_neighbors_count]):
                metrics.observe(NeighborsMetric.neighbors_distances, amount=distance, k=k + 1)

    def serialize_for_client(self) -> ts_proto.GetTopKNeighborsResponse:
        """Create a gRPC response based on the command's results (neighbors for each attribute)."""
        response = self.response_class()
        response.cache_freshness.FromDatetime(self.cache_freshness)

        for neighbors in self.neighbors_batch:
            neighbors_proto = response.neighbors_batch.add()

            for neighbor_id, distance in neighbors:
                neighbor_proto = neighbors_proto.neighbors.add()
                neighbor_proto.id = serialize_entity_id(neighbor_id)
                neighbor_proto.distance = distance

        return response


class SetThresholdCommand(Command):
    """Set similarity threshold associated with a term."""

    service = "ataccama.aicore.term_suggestions.TermSuggestions"
    method = "SetThreshold"
    request_class = ts_proto.SetThresholdRequest
    response_class = ts_proto.SetThresholdResponse
    __slots__ = ("term_id", "threshold", "previous_threshold")

    def __init__(self, term_id: TermId, threshold: float):
        self.term_id = term_id
        self.threshold = threshold
        self.previous_threshold: Optional[float] = None

    def __repr__(self):
        return f"SetThresholdCommand({self.term_id}: {self.threshold})"

    @classmethod
    def deserialize_from_client(cls, request: ts_proto.SetThresholdRequest) -> SetThresholdCommand:
        """Create the command from given protobuf message."""
        return cls(term_id=deserialize_entity_id(request.term_id), threshold=request.threshold)

    def process(
        self,
        microservice: FeedbackService,
        correlation_id: CorrelationId,
        _identity: Optional[Identity] = None,
    ) -> None:
        """Update the threshold in the database and in the feedback service."""
        # Process all feedback which were created before this command to keep serial behavior
        all_feedbacks_processed = False
        while not all_feedbacks_processed:
            all_feedbacks_processed = microservice.process_frequently()

        self.previous_threshold = microservice.calculator.thresholds[self.term_id]
        microservice.dao.set_similarity_thresholds({self.term_id: self.threshold}, correlation_id, sequential_ids=[])
        microservice.calculator.thresholds[self.term_id] = self.threshold
        microservice.update_thresholds_metrics()

    def serialize_for_client(self) -> ts_proto.SetThresholdResponse:
        """Create a gRPC response with old and new thresholds."""
        response = self.response_class()
        response.previous_threshold = self.previous_threshold
        response.new_threshold = self.threshold

        return response


class SetAdaptiveLearningCommand(Command):
    """Enable / disable adaptive learning for a term."""

    service = "ataccama.aicore.term_suggestions.TermSuggestions"
    method = "SetAdaptiveLearning"
    request_class = ts_proto.SetAdaptiveLearningRequest
    response_class = ts_proto.SetAdaptiveLearningResponse
    __slots__ = ("term_id", "adaptive", "previous_adaptive")

    def __init__(self, term_id: TermId, adaptive: bool):
        self.term_id = term_id
        self.adaptive = adaptive
        self.previous_adaptive: Optional[bool] = None

    def __repr__(self):
        return f"SetAdaptiveLearningCommand({self.term_id}: {self.adaptive})"

    @classmethod
    def deserialize_from_client(cls, request: ts_proto.SetAdaptiveLearningRequest) -> SetAdaptiveLearningCommand:
        """Create the command from given protobuf message."""
        return cls(term_id=deserialize_entity_id(request.term_id), adaptive=request.adaptive)

    def process(
        self,
        microservice: FeedbackService,
        correlation_id: CorrelationId,
        _identity: Optional[Identity] = None,
    ) -> None:
        """Enable adaptive learning in the database and in the feedback service."""
        # Process all feedback which were created before this command to keep serial behavior
        all_feedbacks_processed = False
        while not all_feedbacks_processed:
            all_feedbacks_processed = microservice.process_frequently()

        self.previous_adaptive = microservice.calculator.learning_enabled[self.term_id]

        microservice.dao.set_learning_strategy(self.term_id, self.adaptive, correlation_id)
        microservice.calculator.learning_enabled[self.term_id] = self.adaptive

    def serialize_for_client(self) -> ts_proto.SetAdaptiveLearningResponse:
        """Create a gRPC response with previous and new state."""
        response = self.response_class()
        response.previous_adaptive = self.previous_adaptive
        response.new_adaptive = self.adaptive

        return response
