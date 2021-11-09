"""Commonly used constants in the matching system."""

from __future__ import annotations

import enum

from aicore.ai_matching.enums import MatchingPhase


CLUSTER_ID_COLUMN = "cluster_id"
SCORE_VALUE_COLUMN = "score"


class SubPhase(enum.Enum):
    """Special cases of sub-phases. These are used when no method is being computed at the moment."""

    SUBPHASE_NOT_CREATED = enum.auto()  # Sub-phase for not yet created matching
    SUBPHASE_NOT_STARTED = enum.auto()  # Sub-phase until the computation of the current phase starts
    SUBPHASE_WAITING_FOR_USER = enum.auto()  # When waiting for user input in TRAINING_MODEL phase


#  How much does each phase contribute to the progress of the whole matching
PROGRESS_DISTRIBUTION = {
    MatchingPhase.NOT_CREATED: 0,
    MatchingPhase.INITIALIZING_MATCHING: 0.1,
    MatchingPhase.TRAINING_MODEL: 0.15,
    MatchingPhase.FETCHING_RECORDS: 0.1,
    MatchingPhase.BLOCKING_RECORDS: 0.15,
    MatchingPhase.SCORING_PAIRS: 0.2,
    MatchingPhase.CLUSTERING_RECORDS: 0.1,
    MatchingPhase.GENERATING_PROPOSALS: 0.1,
    MatchingPhase.EXTRACTING_RULES: 0.1,
    MatchingPhase.READY: 0,
    MatchingPhase.ERROR: 0,
}

N_SAMPLED_RECORDS_BLOCKING = 2000  # Number of sampled records for AtaDedupeBlockLearner
# (lowered from original dedupe 5000 to reduce the memory consumption from ~11GB to ~2GB on our testing data)

MIN_LABELED_PAIRS = 1  # Min. number of labeled pairs per MATCH/DISTINCT category required to start the evaluation
#  Min. number of labeled pairs per MATCH/DISTINCT category for the model to be considered sufficient
REQUIRED_LABELED_PAIRS = 3
OPTIMAL_LABELED_PAIRS = 30  # Optimal number of labeled pairs per MATCH/DISTINCT category for the AI matching
MINIMAL_MODEL_QUALITY = 0.6  # Minimal model quality required for the progress in training phase to be 100%
# Contribution to the model quality of labeling up to the REQUIRED_LABELED_PAIRS number of pairs
REQUIRED_PAIRS_QUALITY_CONTRIBUTION = 0.3
# Contribution to the model quality of labeling pairs after the first REQUIRED_LABELED_PAIRS are labeled, labeling more
# then OPTIMAL_LABELED_PAIRS of the same class does not increase the model quality any further
OPTIMAL_PAIRS_QUALITY_CONTRIBUTION = 0.2
