"""All action, message and event ids used in AI Matching logging messages."""
from __future__ import annotations

import enum

from aicore.common.metrics import MetricEnum, MetricType


class LogId(enum.Enum):
    """Enum for all action, message and event ids used in AI Matching logging."""

    blocking_step_training = enum.auto()
    blocking_step_rules = enum.auto()
    cleared_training_data = enum.auto()
    clustering_step_clustering = enum.auto()
    error_in_step = enum.auto()
    evaluation_start = enum.auto()
    fetching_step_fetching = enum.auto()
    generating_proposals_step_evaluation = enum.auto()
    generating_proposals_step_generation = enum.auto()
    initialization_step_sampling = enum.auto()
    initialization_step_training = enum.auto()
    matching_phase_changed = enum.auto()
    matching_progressed = enum.auto()
    matching_restarted = enum.auto()
    matching_worker_thread_startup = enum.auto()
    no_user_identity = enum.auto()
    old_process_finished = enum.auto()
    rule_evaluation = enum.auto()
    rule_extraction = enum.auto()
    rule_extraction_zero_pairs = enum.auto()
    rules_extraction_step_positive_pairs = enum.auto()
    rules_extraction_step_negative_pairs = enum.auto()
    rules_extraction_step_initialization = enum.auto()
    rule_generation_columns = enum.auto()
    rule_generation_total = enum.auto()
    scoring_step_scoring = enum.auto()
    metrics_collection = enum.auto()

    def __repr__(self):
        return self.name


class InteractionType(enum.Enum):
    """Proposal/Suggestion states -- purely used for metrics collection."""

    GENERATED = enum.auto()
    SUGGESTED = enum.auto()
    EXTRACTED = enum.auto()
    ACCEPTED = enum.auto()  # Currently not implemented or used - see ONE-22071
    DISCARDED = enum.auto()  # Currently not implemented or used - see ONE-22071
    REJECTED = enum.auto()  # Currently not implemented or used - see ONE-22071
    EVALUATED = enum.auto()
    VALID = enum.auto()
    INVALID = enum.auto()
    REDUNDANT = enum.auto()


class RuleValidity(enum.Enum):
    """Rule states -- purely used for metrics collection."""

    VALID = enum.auto()
    INVALID = enum.auto()
    REDUNDANT = enum.auto()


class RuleExtractionStage(enum.Enum):
    """Rule extraction step/stage -- purely used for metrics collection."""

    GENERATION = enum.auto()
    EVALUATION = enum.auto()
    EXTRACTION = enum.auto()


class PairsType(enum.Enum):
    """Type of pairs being measured -- purely used for metrics collection."""

    POSITIVE = enum.auto()
    NEGATIVE = enum.auto()
    COVERED = enum.auto()


class RuleType(enum.Enum):
    """Type of rule(s) being measured -- purely used for metrics collection."""

    SIMPLE_PARAMETRIC = enum.auto()
    SIMPLE_NON_PARAMETRIC = enum.auto()
    SIMPLE = enum.auto()
    COMPOSITION = enum.auto()
    COMPOUND = enum.auto()


class AIMatchingMetric(MetricEnum):
    """Definition of all AI Matching related metrics to be filled in through matching steps accordingly."""

    __name_prefix__ = "ai_aim"

    # CTX related metrics
    n_manager_instances = (
        MetricType.gauge,
        "The number of active instances.",
    )
    step_processing_seconds = (
        MetricType.gauge,
        "The computation time of each matching step for each instance, expressed in seconds.",
        ["matching_step", "matching_id"],
    )
    n_columns = (
        MetricType.summary,  # Keep this as summary for experimentation
        "The number of columns provided.",
        ["matching_id"],
    )
    n_rows = (
        MetricType.gauge,
        "The number of rows provided in phases `INITIALIZING_MATCHING` and `FETCHING_RECORDS`.",
        ["type", "matching_id"],
    )

    method_processing_seconds = (
        MetricType.gauge,
        "The processing time of each method in a matching step for each instance, expressed in seconds.",
        ["method", "matching_id"],
    )

    # AI research related metrics
    n_blocking_rules = (MetricType.gauge, "The number of blocking rules used.", ["matching_id"])

    n_blocking_rules_functions = (
        MetricType.gauge,
        "The number of occurrences for each blocking rule function.",
        ["blocking_rule_function", "matching_id"],
    )
    n_blocking_rules_types = (
        MetricType.gauge,
        "The number of occurrences for each blocking rule type: `simple` and `compound`.",
        ["type", "matching_id"],
    )
    n_training_pairs_per_decision = (
        MetricType.gauge,
        "The number of training pairs provided for each AI decision.",
        ["decision", "matching_id"],
    )
    model_quality = (
        MetricType.gauge,
        "The model quality represented as a floating point value between 0 and 1.",
        ["matching_id"],
    )
    rule_coverage = (
        MetricType.histogram,  # Keep this as histogram (with default bins) for experimentation.
        "A floating point value between 0 and 1 representing the percentage of matches covered by the current set of extracted rules.",  # noqa E501
        ["matching_id"],
    )
    n_rule_extraction_iteration_rules_generated = (
        MetricType.gauge,
        "The number of rules generated in one iteration of rule extraction.",
        ["matching_id"],
    )

    n_rule_extraction_iteration = (
        MetricType.gauge,
        "The number of n column rules of type `VALID`, `INVALID`, and `REDUNDANT` for one iteration of rule extraction.",  # noqa E501
        ["type", "matching_id"],
    )

    rule_extraction_iteration_processing_seconds = (
        MetricType.gauge,
        "The computation time of each iteration of rule extraction, expressed in seconds.",
        ["matching_id"],
    )

    n_rule_extraction_rules_total = (
        MetricType.gauge,
        "The total number of rules of type `GENERATED`, `EVALUATED`, and `EXTRACTED` used for rule extraction.",
        ["type", "matching_id"],
    )

    n_rule_extraction_pairs_total = (
        MetricType.gauge,
        "The total number of pairs of type `POSITIVE`, `NEGATIVE`, and `COVERED` used for rule extraction.",
        ["type", "matching_id"],
    )

    rule_extraction_total_processing_seconds = (
        MetricType.gauge,
        "The computation time of type `GENERATION`, `EVALUATION`, and `EXTRACTION` needed for "
        "a complete rule extraction run, expressed in seconds.",
        ["type", "matching_id"],
    )

    rules_min_confidences = (
        MetricType.gauge,
        "The minimum confidence level for rule extraction of type `MATCH` and `DISTINCT`.",
        ["type", "matching_id"],
    )

    n_rules_per_category = (
        MetricType.gauge,
        "The number of parametric rules extracted for categories `PARAMETRIC`, `NON_PARAMETRIC`, and `COMPOSITION`.",
        ["type", "matching_id"],
    )

    n_extract_rules_command_calls = (
        MetricType.counter,
        "The number of times that the rule extraction command was called.",
        ["matching_id"],
    )

    n_composition_rules_depth = (
        MetricType.gauge,
        "The number of simple rules contained in one composition rule.",
        ["matching_id"],
    )

    n_proposals = (
        MetricType.gauge,
        "The number of proposals of type `GENERATED` for `MATCH` and `SPLIT/DISTINCT` decisions.",
        ["type", "decision", "matching_id"],
    )

    n_evaluate_records_matching_command_calls = (
        MetricType.counter,
        "The number of times the command for generating proposals was called.",
        ["matching_id"],
    )


METRICS = [AIMatchingMetric]
