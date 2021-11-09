"""Recommendation of terms for attributes using collaborative filtering."""

from __future__ import annotations

import collections
import math

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Container
    from typing import Optional

    from aicore.term_suggestions.types import Neighbors, Suggestions, TermAssignments, TermId


class Recommender:
    """Recommends terms for attributes based on terms assigned to their neighbors."""

    def __init__(
        self,
        config,
        assigned_terms: TermAssignments,
        rejected_terms: TermAssignments,
        disabled_terms: Container[TermId],
        similarity_thresholds: dict[TermId, float],
    ):
        self.config = config
        self.assigned_terms = assigned_terms
        self.rejected_terms = rejected_terms
        self.disabled_terms = disabled_terms
        self.similarity_thresholds = similarity_thresholds
        self.min_confidence_assigned = 0.75 * self.config.recommender_target_accuracy
        self.default_threshold = self.config.recommender_default_threshold

    def batch_recommend(self, neighbors_batch: list[Neighbors]) -> list[Suggestions]:
        """Suggest terms for multiple attributes at once based on terms assigned to their neighbors.

        N-th item in the result are suggestions for the n-th attribute (whose neighbors are n-th item on the input).
        """
        return [self.recommend(neighbors) for neighbors in neighbors_batch]

    def recommend(self, neighbors: Neighbors) -> Suggestions:
        """Suggest relevant terms to an attribute based on the terms assigned to its neighbors."""
        distances_to_terms = self.distances_to_terms(neighbors, self.assigned_terms)
        assigned_distances = self.mean_distances(distances_to_terms)

        distances_to_terms = self.distances_to_terms(neighbors, self.rejected_terms)
        rejected_distances = self.mean_distances(distances_to_terms)

        suggestions = self.recommend_based_on_term_distances(assigned_distances, rejected_distances)
        return suggestions

    def distances_to_terms(self, neighbors: Neighbors, terms: TermAssignments) -> dict[TermId, list[float]]:
        """For each term find relative distances of neighbors which have it assigned/rejected and are in threshold."""
        distances_to_terms: dict[TermId, list[float]] = collections.defaultdict(list)

        for neighbor_id, distance in neighbors:
            for term in terms.get(neighbor_id, ()):  # Either assigned or rejected terms, empty for unknown attribute

                relative_distance = self.relative_distance(term, distance)
                if relative_distance is not None:
                    distances_to_terms[term].append(relative_distance)

        return distances_to_terms

    def relative_distance(self, term: TermId, distance: float) -> Optional[float]:
        """Compute distance relative to threshold for term which is not disabled and not outside the threshold."""
        if term in self.disabled_terms:
            return None

        threshold = self.similarity_thresholds.get(term, self.default_threshold)  # Default for new terms
        if distance > threshold:
            return None

        return distance / threshold

    @staticmethod
    def mean_distances(distances_by_term: dict[TermId, list[float]]) -> dict[TermId, float]:
        """Compute mean distances to each term."""
        # sum / len is the fastest way to compute mean (loses precision for longer lists)
        return {term: sum(distances) / len(distances) for term, distances in distances_by_term.items()}

    def recommend_based_on_term_distances(
        self, distances_to_assigned: dict[TermId, float], distances_to_rejected: dict[TermId, float]
    ) -> Suggestions:
        """Recommend terms whose assigned distance is smaller than rejected distance."""
        recommended_terms = []

        for term_id, distance_to_assigned in distances_to_assigned.items():
            distance_to_rejected = distances_to_rejected.get(term_id, math.inf)
            if distance_to_rejected >= distance_to_assigned:  # Rejected term is closer => don't suggest the term at all
                confidence = self.confidence(distance_to_assigned, distance_to_rejected)
                recommended_terms.append((term_id, confidence))

        return recommended_terms

    def confidence(self, distance_to_assigned: float, distance_to_rejected: float) -> float:
        """Compute confidence of a suggestion as a minimum from two values, based on threshold and on rejected terms."""
        confidence_relative_to_threshold = self.confidence_relative_to_threshold(distance_to_assigned)
        confidence_relative_to_rejected = self.confidence_relative_to_rejected(
            distance_to_assigned, distance_to_rejected
        )

        confidence = min(confidence_relative_to_threshold, confidence_relative_to_rejected)
        return confidence

    def confidence_relative_to_threshold(self, distance_to_assigned: float) -> float:
        """Compute confidence based on relative distance of assigned terms to the threshold and rescale it."""
        return self.scale_confidence(1 - distance_to_assigned, self.min_confidence_assigned)

    @classmethod
    def confidence_relative_to_rejected(cls, distance_to_assigned: float, distance_to_rejected: float) -> float:
        """Compute confidence based on relative distance of assigned terms to rejected terms and rescale it."""
        assigned_rejected_ratio = distance_to_assigned / distance_to_rejected if distance_to_rejected > 0 else 1
        confidence_based_on_ratio = cls.scale_confidence(1 - assigned_rejected_ratio, minimum=0.5)
        return confidence_based_on_ratio

    @staticmethod
    def scale_confidence(unscaled_confidence: float, minimum: float) -> float:
        """Rescale confidence from [0, 1] to [minimum, 1]."""
        return minimum + unscaled_confidence * (1 - minimum)
