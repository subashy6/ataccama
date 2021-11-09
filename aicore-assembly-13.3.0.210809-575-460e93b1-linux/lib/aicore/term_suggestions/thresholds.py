"""Adaptive learning based on user feedbacks."""

from __future__ import annotations

import collections

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from aicore.term_suggestions.types import Feedbacks, LearningStrategies, Thresholds


class ThresholdCalculator:
    """Calculates term similarity thresholds based on user feedback to provided suggestions."""

    def __init__(self, config):
        self.config = config
        # Similarity thresholds for each term - used for suggesting in recommender
        self.thresholds: Thresholds = collections.defaultdict(lambda: self.config.recommender_default_threshold)
        # Whether to adapt the threshold based on feedback or not - by default enabled
        self.learning_enabled: LearningStrategies = collections.defaultdict(lambda: True)

    def process_feedbacks(self, feedbacks: Feedbacks) -> Thresholds:
        """Recalculate the similarity thresholds based on given feedbacks."""
        changed_thresholds = {}
        for term_id, is_positive in feedbacks:
            if self.learning_enabled[term_id]:
                new_threshold = self.calculate_new_threshold(
                    observed_accuracy=float(is_positive),
                    target_accuracy=self.config.recommender_target_accuracy,
                    current_threshold=self.thresholds[term_id],
                    max_threshold=self.config.recommender_max_threshold,
                    step=self.config.recommender_threshold_step,
                )
                self.thresholds[term_id] = new_threshold
                changed_thresholds[term_id] = new_threshold

        return changed_thresholds

    @staticmethod
    def calculate_new_threshold(
        observed_accuracy: float, target_accuracy: float, current_threshold: float, max_threshold: float, step: float
    ):
        """Calculate updated similarity threshold."""
        relative_change = 1 + step * abs(target_accuracy - observed_accuracy)

        if observed_accuracy < target_accuracy:
            new_threshold = current_threshold / relative_change
        else:
            new_threshold = current_threshold * relative_change
            new_threshold = min(new_threshold, max_threshold)

        return new_threshold
