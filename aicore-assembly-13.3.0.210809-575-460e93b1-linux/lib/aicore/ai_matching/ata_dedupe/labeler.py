"""Modified dedupe library classes suited for AI matching module."""
from __future__ import annotations

import random

from typing import TYPE_CHECKING

import dedupe.core
import dedupe.labeler
import dedupe.training
import numpy
import rlr.lr

from aicore.ai_matching.constants import N_SAMPLED_RECORDS_BLOCKING


if TYPE_CHECKING:
    import dedupe._typing as dedupe_types
    import dedupe.datamodel


class AtaDedupeDisagreementLearner(dedupe.labeler.DisagreementLearner, dedupe.labeler.DedupeSampler):
    """Modified DedupeDisagreementLearner for AI matching needs - biased pop and handling of empty cover - see below."""

    def __init__(
        self,
        data_model: dedupe.datamodel.DataModel,
        data: dedupe_types.Data,
        blocked_proportion: float,
        sample_size: int,
        original_length: int,
        index_include: list[dedupe_types.RecordPair],
    ):

        self.data_model = data_model
        data = dedupe.core.index(data)
        self.candidates = super().sample(data, blocked_proportion, sample_size)

        random_pair = random.choice(self.candidates)
        exact_match = (random_pair[0], random_pair[0])

        index_include = index_include.copy()
        index_include.append(exact_match)

        # Modified line - to use AtaDedupeBlockLearner instead of the hardcoded DedupeBlockLearner
        self.blocker = AtaDedupeBlockLearner(data_model, self.candidates, data, original_length, index_include)

        self._common_init()

        self.mark([exact_match] * 4 + [random_pair], [1] * 4 + [0])

    def _common_init(self):
        """Inject the RobustRLRLearner to be robust to extreme scores."""
        self.classifier = RobustRLRLearner(self.data_model, candidates=self.candidates)
        self.learners = (self.classifier, self.blocker)
        self.y = numpy.array([])
        self.pairs = []

    def pop_biased(self, match_to_distinct_diff: int) -> dedupe_types.TrainingExample:
        """Pops training example of largest added information, help keep balance sets of match and distinct samples."""
        if not len(self.candidates):
            raise IndexError("No more unlabeled examples to label")

        probs = []
        for learner in self.learners:
            probabilities = learner.candidate_scores()
            probs.append(probabilities)

        probs = numpy.concatenate(probs, axis=1)
        disagreement = numpy.std(probs > 0.5, axis=1).astype(bool)  # type: ignore

        # when large difference in pairs -> trust more to RLR model to pick a pair from the smaller category
        if abs(match_to_distinct_diff) > 5:
            search_matches = match_to_distinct_diff < 0  # when much more distinct pairs than matches
            strong_rlr_decision = probs[:, 0] > 0.5 if search_matches else probs[:, 0] < 0.5  # type: ignore
            strong_disagreement = strong_rlr_decision & disagreement

            if strong_disagreement.any():
                to_choose = strong_disagreement.nonzero()[0]
            elif strong_rlr_decision.any():
                to_choose = numpy.where(strong_rlr_decision)[0]
            else:
                arg_max_indices = [numpy.argmax(probs[:, 0])]  # type: ignore
                arg_min_indices = [numpy.argmin(probs[:, 0])]  # type: ignore
                to_choose = arg_max_indices if search_matches else arg_min_indices
            uncertain_index: int = numpy.random.choice(to_choose, 1)[0]

        else:
            if disagreement.any():  # select non-agreeing pair index
                conflicts = disagreement.nonzero()[0]  # type: ignore
                uncertain_index = conflicts[numpy.argmax(probs[conflicts][:, 0])]  # type: ignore
            else:  # or that where the probability differs the most
                uncertain_index = numpy.std(probs, axis=1).argmax()  # type: ignore

        uncertain_pair = self.candidates.pop(uncertain_index)
        for learner in self.learners:
            learner._remove(uncertain_index)

        return uncertain_pair

    # Without this, bool(self) returns False if all candidates were labeled because it defaults to
    # len(self) == len(self.candidates). Is it an error in dedupe or do we miss something?
    def __bool__(self):
        """Return True (i.e. is trained) when there is at least one evaluated pair."""
        return len(self.pairs) > 0


class LearnerHandlingEmptyCover(dedupe.training.DedupeBlockLearner):
    """Overriding the DedupeBlockLearner to handle the cover which is empty."""

    def learn(self, matches, recall):
        """Modification of DedupeBlockLearner to handle empty cover (no blocker predicate could be applied).

        Takes in a set of training pairs and predicates and tries to find a good set of blocking rules.
        """
        comparison_count = self.comparison_count  # type: ignore

        dupe_cover = dedupe.training.Cover(self.blocker.predicates, matches)  # type: ignore
        dupe_cover.compound(2)
        dupe_cover.intersection_update(comparison_count)

        dupe_cover.dominators(cost=comparison_count)

        # Original line # coverable_dupes = set.union(*dupe_cover.values())
        # Added lines
        coverable_dupes = set.union(*dupe_cover.values(), set())

        uncoverable_dupes = [pair for i, pair in enumerate(matches) if i not in coverable_dupes]

        epsilon = int((1.0 - recall) * len(matches))

        if len(uncoverable_dupes) > epsilon:
            # Original logs: # logger.warning(OUT_OF_PREDICATES_WARNING) # logger.debug(uncoverable_dupes)
            epsilon = 0
        else:
            epsilon -= len(uncoverable_dupes)

        for pred in dupe_cover:
            pred.count = comparison_count[pred]

        searcher = dedupe.training.BranchBound(len(coverable_dupes) - epsilon, 2500)
        final_predicates = searcher.search(dupe_cover)

        # Original log: logger.info('Final predicate set:') # for predicate in final_predicates: logger.info(predicate)

        return final_predicates


class AtaDedupeBlockLearner(dedupe.labeler.DedupeBlockLearner):
    """An extension of DedupeBlockLearner which uses LearnerHandlingEmptyCover to handle None values better."""

    def __init__(
        self,
        data_model: dedupe.datamodel.DataModel,
        candidates: list[dedupe_types.RecordPair],
        data: dedupe_types.Data,
        original_length: int,
        _index_include: list[dedupe_types.RecordPair],
    ):
        # The code from super().__init__() is copied here and modified to use LearnerHandlingEmptyCover
        dedupe.labeler.BlockLearner.__init__(self, data_model, candidates)

        # Removed preparation of index data as we don't use them
        preds = self.data_model.predicates()
        sampled_records = dedupe.labeler.Sample(data, N_SAMPLED_RECORDS_BLOCKING, original_length)

        # Modified to use custom learner
        self.block_learner = LearnerHandlingEmptyCover(preds, sampled_records, sampled_records)


def sigmoid(values: numpy.ndarray) -> numpy.ndarray:
    """Compute a sigmoid function for an array of values."""
    truncated_values = numpy.clip(values, a_min=None, a_max=700)
    exp_values = numpy.exp(truncated_values)
    return exp_values / (1 + exp_values)


def predict_probabilities(examples: numpy.ndarray, weights: numpy.ndarray, bias: numpy.ndarray) -> numpy.ndarray:
    """Predict probabilities using trained regularized regression.

    Unlike in rlr.lr.RegularizedLogisticRegression, too extreme scores are limited so that the returned probability is
    in [0, 1] and not `nan`.
    """
    scores = numpy.dot(examples, weights) + bias
    probabilities = sigmoid(scores)
    return probabilities.reshape(-1, 1)


class RobustRegularizedLogisticRegression(rlr.lr.RegularizedLogisticRegression):
    """A more robust version of regularized logistic regression which does not return nan values for extreme scores."""

    def predict_proba(self, examples: numpy.ndarray) -> numpy.ndarray:
        """Compute probabilities as in the parent class, but resolving extreme cases in a more safe way."""
        return predict_probabilities(examples, self.weights, self.bias)


class RobustRLRLearner(dedupe.labeler.RLRLearner):
    """RLR learner with fixed computation of probabilities for high scores."""

    def predict_proba(self, examples: numpy.ndarray) -> numpy.ndarray:
        """Compute probabilities as in the parent class, but resolving extreme cases in a more safe way."""
        return predict_probabilities(examples, self.weights, self.bias)
