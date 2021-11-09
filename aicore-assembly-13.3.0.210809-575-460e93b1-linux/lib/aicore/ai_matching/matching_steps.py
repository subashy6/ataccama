"""Individual phases of matching and how they are resolved."""
from __future__ import annotations

import abc
import collections
import functools
import itertools
import operator
import random

from typing import TYPE_CHECKING

from aicore.ai_matching import constants
from aicore.ai_matching.ata_dedupe.api import AtaDedupe
from aicore.ai_matching.enums import ComputationState, InvalidStateError, MatchingDecision, MatchingPhase, ProposalType
from aicore.ai_matching.registry import (
    AIMatchingMetric,
    InteractionType,
    LogId,
    PairsType,
    RuleExtractionStage,
    RuleType,
)
from aicore.ai_matching.rules_extraction import CompositionRule, DistanceRule, NonparametricRuleBase, RuleExtractor
from aicore.ai_matching.utils.logging import log_info, log_progress
from aicore.ai_matching.utils.time_bounds import measure_time_bounds
from aicore.common.grpc import GRPCClient
from aicore.common.logging import Logger
from aicore.common.metrics import MetricsDAO
from aicore.common.utils import datetime_now, resolve_cpu_count


if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Iterator

    import dedupe._typing as dedupe_types

    from aicore.ai_matching.storage import SingleStorage
    from aicore.ai_matching.types import (
        ColumnName,
        GroupId,
        RecordData,
        RecordId,
        RecordIdsPair,
        RecordIdsPairSet,
        Records,
        TrainingData,
    )


def add_progress(fraction_of_progress: float):
    """Return a decorator with the progress as argument."""

    def decorator_add_progress(method):
        """Return a wrapper for measuring progress of a step method."""

        @functools.wraps(method)
        def add_progress_wrapper(step: StepBase, *args, **kwargs):
            """Update the progress after the wrapped step method finishes."""
            storage = step.storage
            storage.subphase = method.__name__

            with measure_time_bounds() as time_bounds:
                result = method(step, *args, **kwargs)

            storage.add_phase_progress(fraction_of_progress)
            elapsed_time = time_bounds.elapsed_time()
            log_progress(step.logger, storage, logger_depth=3, elapsed_time=elapsed_time)

            step.metrics.set_value(
                AIMatchingMetric.method_processing_seconds,
                elapsed_time.seconds,
                method=step.storage.subphase,
                matching_id=str(step.storage.matching_id),
            )

            return result

        return add_progress_wrapper

    return decorator_add_progress


class StepBase(abc.ABC):
    """One phase of the matching process."""

    def __init__(
        self,
        storage: SingleStorage,
        mdc_grpc_client: GRPCClient,
        metrics: MetricsDAO,
        logger: Logger,
        config,
    ):
        self.storage = storage
        self.mdc_grpc_client = mdc_grpc_client
        self.metrics = metrics
        self.logger = logger
        self.config = config

    @abc.abstractmethod
    def __call__(self) -> MatchingPhase:
        """Perform the computation and return the new phase which should follow."""

    def log(self, message: str, message_id: LogId, **kwargs):
        """Log the message with correct matching id prefix."""
        storage = self.storage
        log_info(
            self.logger,
            message,
            message_id,
            storage.matching_id,
            storage.last_command_correlation_id,
            storage.identity,
            **kwargs,
        )

    def collect_metrics(self):
        """Collect relevant prometheus end point metrics for each matching step."""
        pass

    def __repr__(self):
        return type(self).__name__


class InitializationStep(StepBase):
    """Initialize AI matching for particular entity on a uniform data sample from the whole MDC table."""

    def __call__(self) -> MatchingPhase:
        """Initialize AI matching for particular entity on a uniform data sample from the whole MDC."""
        # TODO: move this into train_initial_models() (probably a method on Storage)  # noqa T101 ONE-21104
        previous_training_pairs = (
            self.storage.deduper.training_pairs.copy()
            if self.storage.deduper is not None
            else {MatchingDecision.DISTINCT.to_dedupe(): [], MatchingDecision.MATCH.to_dedupe(): []}
        )

        self.storage.n_total_records_count_initialization = self.sample_data()
        self.init_deduper()
        self.prepare_training(self.storage.n_total_records_count_initialization)
        self.train_initial_models(previous_training_pairs)
        self.prepare_new_training_pair()

        # TODO: move the workflow logic to one place  # noqa T101 ONE-22954
        if self.storage.skip_training_phase:
            self.storage.skip_training_phase = False
            return MatchingPhase.FETCHING_RECORDS

        return MatchingPhase.TRAINING_MODEL

    @add_progress(0.1)
    def sample_data(self) -> int:
        """Sample MDM data and update progress."""
        self.storage.model_update_time = datetime_now()
        data_stream = prepare_data_stream(self.storage, self.mdc_grpc_client)
        _, id_column_name = self.storage.record_id_column  # type: ignore
        sampled_data, n_total_records_count = self.sample_online(
            data_stream,
            id_column_name,
            num_to_sample=self.config.initialization_sample_size,
        )
        self.log(
            "Sampled {n_sampled} records from total {n_total_records_count} fetched records",
            LogId.initialization_step_sampling,
            n_sampled=len(sampled_data),
            n_total_records_count=n_total_records_count,
        )
        self.storage.mdc_data = sampled_data  # Store sampled data because we need them during training, they will be
        # later replaced by the full MDM data fetched during the FetchingStep
        return n_total_records_count

    @add_progress(0.2)
    def init_deduper(self):
        """Initialize Dedupe's instance for particular data model."""
        columns = self.storage.used_columns
        # All data is handled as String so far, Dedupe accepts only some types (case sensitive),
        # will need conversion if we want to support more data types
        variable_fields = [{"field": column_name, "type": "NoIndexString"} for column_type, column_name in columns]
        num_cores = resolve_cpu_count(self.config.jobs)

        deduper = AtaDedupe(variable_fields, decision_threshold=self.config.decision_threshold, num_cores=num_cores)
        self.storage.deduper = deduper

    @add_progress(0.3)
    def prepare_training(self, n_total_records_count: int):
        """Prepare training data from the sampled MDM data and update progress."""
        self.storage.deduper.prepare_training(
            self.storage.mdc_data, sample_size=self.config.training_sample_size, original_length=n_total_records_count
        )

    @add_progress(0.3)
    def train_initial_models(self, previous_training_pairs: TrainingData):
        """Start the initial training, preselect blocking rules and update progress."""
        # Load already labeled training pairs and train the model on them
        n_match = len(previous_training_pairs[MatchingDecision.MATCH.to_dedupe()])
        n_distinct = len(previous_training_pairs[MatchingDecision.DISTINCT.to_dedupe()])
        self.log(
            f"Model initialized on {n_match} MATCH and {n_distinct} DISTINCT training pairs",
            LogId.initialization_step_training,
            n_pairs_match=n_match,
            n_pairs_distinct=n_distinct,
        )
        self.storage.deduper.mark_pairs(previous_training_pairs)

    @add_progress(0.1)
    def prepare_new_training_pair(self):
        """Prepare a new training pair for labelling and update progress."""
        # Prepare new training pair in advance for when the user asks for it
        self.storage.prepare_new_training_pair_if_resolved()

    @staticmethod
    def sample_online(
        data_generator: Iterator[RecordData], id_column_name: str, num_to_sample: int
    ) -> tuple[Records, int]:
        """Sample records from a steam of input records with uniform probability, return also total records count."""
        sampled_rows = []
        id_ = -1
        for id_, value in enumerate(data_generator):
            if id_ < num_to_sample:
                sampled_rows.append(value)
            else:
                random_index = random.randint(0, id_)
                if random_index < num_to_sample:
                    sampled_rows[random_index] = value

        return {record[id_column_name]: record for record in sampled_rows}, id_ + 1

    def collect_metrics(self):
        """Collect relevant prometheus end point metrics for Initialization step."""
        self.metrics.set_value(
            AIMatchingMetric.n_rows,
            self.storage.n_total_records_count_initialization,
            type=MatchingPhase.INITIALIZING_MATCHING.name,
            matching_id=str(self.storage.matching_id),
        )


class FetchingStep(StepBase):
    """Fetch all party data from the MDC and store them in the storage."""

    def __call__(self) -> MatchingPhase:
        """Fetch all party data from the MDC and store them in the storage."""
        self.storage.model_update_time = datetime_now()
        self.fetch_data()
        self.storage.n_total_records_count_fetching = len(self.storage.mdc_data)
        self.log(
            "Fetched {n_records} records",
            LogId.fetching_step_fetching,
            n_records=self.storage.n_total_records_count_fetching,
        )
        return MatchingPhase.BLOCKING_RECORDS

    @add_progress(1.0)
    def fetch_data(self):
        """Fetch MDM data, store them and update the progress."""
        # TODO: Step should not know about grpc  # noqa T101 ONE-21104
        all_data_generator = prepare_data_stream(self.storage, self.mdc_grpc_client)
        self.storage.store_mdc_data(all_data_generator)

    def collect_metrics(self):
        """Collect relevant prometheus end point metrics for Fetching step."""
        self.metrics.set_value(
            AIMatchingMetric.n_rows,
            self.storage.n_total_records_count_fetching,
            type=MatchingPhase.FETCHING_RECORDS.name,
            matching_id=str(self.storage.matching_id),
        )


class BlockingStep(StepBase):
    """Perform blocking over all records and generate distinct record id pairs."""

    def __call__(self) -> MatchingPhase:
        """Perform blocking over all records and generate distinct record id pairs."""
        self.train_model()
        self.prepare_blocked_pairs_generator()
        return MatchingPhase.SCORING_PAIRS

    @add_progress(0.5)
    def train_model(self):
        """Train model on up-to date training pairs and update progress."""
        self.storage.deduper.train(index_predicates=False)  # Train the model on up-to-date training pairs
        n_match = len(self.storage.deduper.training_pairs[MatchingDecision.MATCH.to_dedupe()])
        n_distinct = len(self.storage.deduper.training_pairs[MatchingDecision.DISTINCT.to_dedupe()])
        self.log(
            "Model trained on {n_training_pairs} training pairs " "({n_match} matching + {n_distinct} distinct)",
            LogId.blocking_step_training,
            n_training_pairs=n_match + n_distinct,
            n_match=n_match,
            n_distinct=n_distinct,
        )

    @add_progress(0.5)
    def prepare_blocked_pairs_generator(self):
        """Store prepared blocked pairs and update the progress."""
        blocked_record_pairs = self.storage.deduper.record_pairs_from_storage(self.storage)
        self.storage.blocked_record_pairs_generator = blocked_record_pairs

        blocking_rules = list(self.storage.deduper.predicates)
        self.log(
            "Selected {n_blocking_rules} blocking rules: {blocking_rules}",
            LogId.blocking_step_rules,
            n_blocking_rules=len(blocking_rules),
            blocking_rules=blocking_rules,
        )

    def collect_metrics(self):
        """Collect relevant prometheus end point metrics for Blocking step."""
        blocking_functions = []
        rule_types = []

        n_blocking_rules = len(self.storage.get_blocking_rules())
        self.metrics.set_value(
            AIMatchingMetric.n_blocking_rules, n_blocking_rules, matching_id=str(self.storage.matching_id)
        )

        for blocking_rule in self.storage.deduper.predicates:
            if blocking_rule.type == "CompoundPredicate":
                for simple_blocking_rule in blocking_rule:
                    blocking_functions.append(simple_blocking_rule.func.__name__)

            else:  # If type SimplePredicate
                blocking_functions.append(blocking_rule.func.__name__)

            rule_types.append(blocking_rule.type)

        blocking_rule_types_value_counts = collections.Counter(rule_types)
        for blocking_rule_type, occurrence in blocking_rule_types_value_counts.items():
            self.metrics.set_value(
                AIMatchingMetric.n_blocking_rules_types,
                occurrence,
                type=blocking_rule_type,
                matching_id=str(self.storage.matching_id),
            )

        value_counts = collections.Counter(blocking_functions)

        for blocking_rule_function, occurrence in value_counts.items():
            self.metrics.set_value(
                AIMatchingMetric.n_blocking_rules_functions,
                occurrence,
                blocking_rule_function=blocking_rule_function,
                matching_id=str(self.storage.matching_id),
            )


class ScoringStep(StepBase):
    """Match record pairs and generate matching scores."""

    def __call__(self) -> MatchingPhase:
        """Match record pairs and generate matching scores."""
        self.compute_matching_scores()
        return MatchingPhase.CLUSTERING_RECORDS

    @add_progress(1.0)
    def compute_matching_scores(self):
        """Store the computed matching scores for each blocked record pair and update the progress."""
        self.storage.matching_scores = self.storage.deduper.score(self.storage.blocked_record_pairs_generator)
        self.log(
            "Computed matching scores for {n_pairs} record pairs",
            LogId.scoring_step_scoring,
            n_pairs=len(self.storage.matching_scores),
        )

    def collect_metrics(self):
        """Collect relevant prometheus end point metrics for Scoring step."""
        match_training_count = self.storage.get_training_counts(MatchingDecision.MATCH)
        distinct_training_count = self.storage.get_training_counts(MatchingDecision.DISTINCT)

        self.metrics.set_value(
            AIMatchingMetric.n_training_pairs_per_decision,
            match_training_count,
            decision=MatchingDecision.MATCH.name,
            matching_id=str(self.storage.matching_id),
        )
        self.metrics.set_value(
            AIMatchingMetric.n_training_pairs_per_decision,
            distinct_training_count,
            decision=MatchingDecision.DISTINCT.name,
            matching_id=str(self.storage.matching_id),
        )
        self.metrics.set_value(
            AIMatchingMetric.model_quality,
            self.storage.model_quality,
            matching_id=str(self.storage.matching_id),
        )


class ClusteringStep(StepBase):
    """Cluster matched pairs."""

    def __call__(self) -> MatchingPhase:
        """Cluster matched pairs."""
        clusters = self.cluster_records()
        self.store_clusters(clusters)

        storage = self.storage
        next_phase = next_phase_after_clustering(storage)
        if next_phase == MatchingPhase.READY:
            raise InvalidStateError(
                storage.matching_id,
                f"Clustering phase finished but neither rule extraction "
                f"({storage.rules_extraction_state}) nor record matching "
                f"({storage.records_matching_state}) is planned",
                rules_extraction_state=storage.rules_extraction_state,
                records_matching_state=storage.records_matching_state,
            )
        return next_phase

    @add_progress(0.9)
    def cluster_records(self) -> dedupe_types.Clusters:
        """Return the clustered records and update the progress."""
        deduper = self.storage.deduper
        deduper.decision_threshold = self.config.decision_threshold
        # Computation of the cluster(s) and storing them are separated in order to report more granular progress.
        clusters = deduper.cluster(self.storage.matching_scores, threshold=deduper.decision_threshold)
        return clusters

    @add_progress(0.1)
    def store_clusters(self, clusters: dedupe_types.Clusters):
        """Store the computed cluster of records and update the progress."""
        storage = self.storage
        storage.store_clusters(clusters)
        self.log(
            "Computed {n_clusters} clusters",
            LogId.clustering_step_clustering,
            n_clusters=len(storage.clusters),
        )

        storage.clustering_state = ComputationState.FINISHED


class GeneratingProposalsStep(StepBase):
    """Compare master and cluster groups, generate proposals and cache the most confident ones."""

    def __call__(self) -> MatchingPhase:
        """Compare master and cluster groups, generate proposals and cache the most confident ones."""
        self.generate_proposals()
        self.log(
            "Generated {n_merge_proposals} MERGE and {n_split_proposals} SPLIT proposals against MDC data",
            LogId.generating_proposals_step_generation,
            n_merge_proposals=self.storage.proposal_counts[ProposalType.MERGE],
            n_split_proposals=self.storage.proposal_counts[ProposalType.SPLIT],
        )
        self.score_and_threshold_proposals()
        self.extract_most_confident_proposals()
        self.explain_proposals()
        self.log(
            "Explained and cached {n_merge_proposals} MERGE and {n_split_proposals} SPLIT proposals",
            LogId.generating_proposals_step_evaluation,
            n_merge_proposals=len(self.storage.cached_proposals[ProposalType.MERGE]),
            n_split_proposals=len(self.storage.cached_proposals[ProposalType.SPLIT]),
        )
        self.storage.records_matching_state = ComputationState.FINISHED
        return next_phase_after_clustering(self.storage)

    @add_progress(0.4)
    def generate_proposals(self) -> None:
        """Generate MERGE/SPLIT proposals by comparing master groups and AI cluster groups."""
        groups_fetching_batch_size = self.config.groups_fetching_batch_size
        record_column_name = self.storage.record_id_column[1]
        ai_group_column_name = constants.CLUSTER_ID_COLUMN
        mdc_group_column_name = self.storage.matching_id_column[1]

        # SPLIT proposals
        # Maybe in production this should be acquired as a stream for a DB query for records sorted group_id_column_name
        mdc_data_groups = (
            (record[mdc_group_column_name], record[record_column_name]) for record in self.storage.mdc_data.values()
        )
        mdc_data1 = sorted(mdc_data_groups, key=operator.itemgetter(0))
        ai_data1 = self.storage.clusters
        split_proposals = self.generate_proposals_one_way(
            mdc_data1, ai_data1, ai_group_column_name, groups_fetching_batch_size
        )
        self.storage.store_unscored_proposals(split_proposals, ProposalType.SPLIT)

        # MERGE proposals
        ai_data_groups = (
            (record[ai_group_column_name], record[record_column_name]) for record in self.storage.clusters.values()
        )
        ai_data2 = sorted(ai_data_groups, key=operator.itemgetter(0))
        mdc_data2 = self.storage.mdc_data
        merge_proposals = self.generate_proposals_one_way(
            ai_data2, mdc_data2, mdc_group_column_name, groups_fetching_batch_size
        )
        self.storage.store_unscored_proposals(merge_proposals, ProposalType.MERGE)

    @add_progress(0.3)
    def score_and_threshold_proposals(self):
        """Assign scores to the found proposals and cache the most confident ones."""
        scoring_batch_size = self.config.scoring_batch_size

        for proposals_batch in self.storage.fetch_proposals_batches(scoring_batch_size):
            for pair_ids, score in self.score_pairs(proposals_batch.keys()):
                proposal = proposals_batch[pair_ids]
                proposal.confidence = score if proposal.decision == ProposalType.MERGE else (1 - score)  # Store scores

                if proposal.confidence >= self.storage.confidence_threshold:
                    self.storage.cached_proposals[proposal.decision].append(proposal)  # Store confident proposals

    @add_progress(0.1)
    def extract_most_confident_proposals(self):
        """Limit most confident proposals to at most `cached_proposals_count`."""
        for proposal_type in (ProposalType.MERGE, ProposalType.SPLIT):
            most_confident = self.storage.get_most_confident_proposals(
                self.storage.cached_proposals[proposal_type], self.storage.cached_proposals_count
            )
            self.storage.cached_proposals[proposal_type] = most_confident

    @add_progress(0.2)
    def explain_proposals(self):
        """Explain the cached proposals."""
        most_confident_splits = self.storage.cached_proposals[ProposalType.SPLIT]
        most_confident_merges = self.storage.cached_proposals[ProposalType.MERGE]

        covered_record_ids = set(
            itertools.chain.from_iterable(
                ((proposal.id1, proposal.id2) for proposal in most_confident_merges + most_confident_splits)
            )
        )

        record_details = self.storage.fetch_record_details_by_ids(covered_record_ids)

        for proposal in most_confident_merges + most_confident_splits:
            key_columns = self.storage.deduper.used_blocking_rule_columns(proposal, record_details)
            column_scores = self.storage.deduper.get_proposal_column_weights(proposal, record_details)
            proposal.add_explanation(key_columns, column_scores)

    def score_pairs(self, pairs: Collection[RecordIdsPair]) -> Iterator[tuple[RecordIdsPair, float]]:
        """Compute merge confidence of each pair of records."""
        record_ids_to_fetch = set(itertools.chain.from_iterable(pairs))  # Consider fetching by batches for more data
        record_details = self.storage.fetch_record_details_by_ids(record_ids_to_fetch)

        pairs_with_details = [((id1, record_details[id1]), (id2, record_details[id2])) for (id1, id2) in pairs]
        matching_scores = self.storage.deduper.score(pairs_with_details)

        for pair_ids, score in zip(matching_scores["pairs"], matching_scores["score"]):
            yield tuple(pair_ids), score  # type: ignore

    def generate_proposals_one_way(
        self,
        data1_sorted_by_group_id: Iterable[tuple[GroupId, RecordId]],
        data2: Records,
        group_column_name2: ColumnName,
        batch_size: int,
    ) -> set[RecordIdsPair]:
        """Compare two groupings - return pairs which are grouped in the first data source but not in second one."""
        proposals = set()
        for batch_of_groups1 in self.storage.iter_batch_of_groups(data1_sorted_by_group_id, batch_size=batch_size):
            grouped_pairs1 = self.storage.get_pairs_from_groups(batch_of_groups1)

            unique_ids = set(itertools.chain.from_iterable(batch_of_groups1))
            grouped_pairs2 = self.storage.get_grouped_pairs_covered_by_ids(unique_ids, data2, group_column_name2)

            proposals |= grouped_pairs1 - grouped_pairs2

        return proposals

    def collect_metrics(self):
        """Collect relevant prometheus end point metrics for Proposal Generation step."""
        match_proposals = self.storage.get_proposals(0, ProposalType.MERGE, int(1e9))
        distinct_proposals = self.storage.get_proposals(0, ProposalType.SPLIT, int(1e9))

        self.metrics.set_value(
            AIMatchingMetric.n_proposals,
            len(match_proposals),
            type=InteractionType.GENERATED.name,
            decision=ProposalType.MERGE.name,
            matching_id=str(self.storage.matching_id),
        )
        self.metrics.set_value(
            AIMatchingMetric.n_proposals,
            len(distinct_proposals),
            type=InteractionType.GENERATED.name,
            decision=ProposalType.SPLIT.name,
            matching_id=str(self.storage.matching_id),
        )


class ExtractingRulesStep(StepBase):
    """Extract rules covering the scored pairs found in ScoringStep."""

    def __call__(self) -> MatchingPhase:
        """Extract rules covering the scored pairs found in ScoringStep."""
        positive_pairs, negative_pairs = self.prepare_confident_pairs()
        rule_extractor = self.initialize_rules_extractor(positive_pairs, negative_pairs)
        self.extract_rules(rule_extractor)

        self.storage.rules_extraction_state = ComputationState.FINISHED
        self.storage.rule_extractor = rule_extractor
        return next_phase_after_clustering(self.storage)

    @add_progress(0.15)
    def prepare_confident_pairs(self) -> tuple[RecordIdsPairSet, RecordIdsPairSet]:
        """Prepare positive and negative pairs and extract those more confident than the thresholds."""
        positive_pairs_ids = self.prepare_positive_pairs_ids()

        positive_threshold = self.storage.min_match_confidence
        negative_threshold = self.storage.min_distinct_confidence

        positive_pairs = set()
        negative_pairs = set()
        for (id1, id2), score in zip(self.storage.matching_scores["pairs"], self.storage.matching_scores["score"]):
            pair_id = id1.item(), id2.item()
            if pair_id in positive_pairs_ids:
                if score >= positive_threshold:
                    positive_pairs.add(pair_id)
            else:
                # Confidence that a pair is DISTINCT is 1 - confidence it is MATCH
                if 1.0 - score >= negative_threshold:
                    negative_pairs.add(pair_id)

        n_all_positive_pairs = len(positive_pairs_ids)
        n_all_negative_pairs = len(self.storage.matching_scores["score"]) - n_all_positive_pairs

        self.log(
            "Selected {n_confident_positive_pairs} out of {n_positive_pairs} positive pairs with confidence >= "
            "{positive_threshold:0.2f} and {n_confident_negative_pairs} out of {n_negative_pairs} negative pairs with "
            "confidence >= {negative_threshold:0.2f} for rule extraction",
            LogId.rules_extraction_step_positive_pairs,
            n_confident_positive_pairs=len(positive_pairs),
            n_positive_pairs=n_all_positive_pairs,
            positive_threshold=positive_threshold,
            n_confident_negative_pairs=len(negative_pairs),
            n_negative_pairs=n_all_negative_pairs,
            negative_threshold=negative_threshold,
        )

        return positive_pairs, negative_pairs

    @add_progress(0.05)
    def initialize_rules_extractor(
        self, positive_pairs: RecordIdsPairSet, negative_pairs: RecordIdsPairSet
    ) -> RuleExtractor:
        """Use positive and negative pairs to initialize the Rule Extractor and update the progress."""
        columns = [name for _, name in self.storage.used_columns]
        rule_extractor = RuleExtractor(
            self.storage.mdc_data,
            positive_pairs,
            columns,
            self.logger,
            self.storage.matching_id,
            self.storage.last_command_correlation_id,
            self.storage.last_command_identity,
            negative_pairs,
            max_columns_per_rule=self.config.max_columns,
        )
        self.log(
            "Rules extractor initialized with {n_positive_pairs} positive pairs, {n_negative_pair} "
            "negative pairs, max {max_columns} columns per rule and {n_columns} columns: {columns}",
            LogId.rules_extraction_step_initialization,
            n_positive_pairs=len(positive_pairs),
            n_negative_pair=len(negative_pairs),
            max_columns=self.config.max_columns,
            n_columns=len(columns),
            columns=columns,
        )
        return rule_extractor

    @add_progress(0.8)
    def extract_rules(self, rule_extractor: RuleExtractor):
        """Extract the most useful rules from the initialized Rule Extractor and update the progress."""
        self.storage.extracted_rules = rule_extractor.extract_rules()

    def prepare_positive_pairs_ids(self) -> RecordIdsPairSet:
        """Prepare all positive pairs, i.e. pairs matched by AI Matching."""
        record_column_name = self.storage.record_id_column[1]
        ai_group_column_name = constants.CLUSTER_ID_COLUMN

        ai_data_groups = (
            (record[ai_group_column_name], record[record_column_name]) for record in self.storage.clusters.values()
        )
        ai_data = sorted(ai_data_groups, key=operator.itemgetter(0))

        pairs = set()
        for cluster in self.storage.iter_records_with_same_group_id(ai_data):
            pairs.update(self.storage.get_pairs_from_group(cluster))

        return pairs

    def collect_metrics(self):
        """Collect relevant prometheus end point metrics for Rule Extraction step."""
        self.metrics.observe(
            AIMatchingMetric.rule_coverage,
            self.storage.extracted_rules.overall_coverage,
            matching_id=str(self.storage.matching_id),
        )

        self._collect_rule_extraction_metrics()

        self.metrics.set_value(
            AIMatchingMetric.rules_min_confidences,
            self.storage.min_match_confidence,
            type=MatchingDecision.MATCH.name,
            matching_id=str(self.storage.matching_id),
        )

        self.metrics.set_value(
            AIMatchingMetric.rules_min_confidences,
            self.storage.min_distinct_confidence,
            type=MatchingDecision.DISTINCT.name,
            matching_id=str(self.storage.matching_id),
        )

        self.collect_n_rules_per_category_metrics()

    def collect_n_rules_per_category_metrics(self):
        """Collect relevant prometheus end point metrics for each rule per category ["parametric, non_parametric ..]."""
        n_simple_parametric_rules, _ = self._get_counts_for_rule_type(DistanceRule)
        n_simple_nonparametric_rules, _ = self._get_counts_for_rule_type(NonparametricRuleBase)
        n_composition_rules, n_rule_depth = self._get_counts_for_rule_type(CompositionRule)

        self.metrics.set_value(
            AIMatchingMetric.n_rules_per_category,
            n_simple_nonparametric_rules,
            type=RuleType.SIMPLE_NON_PARAMETRIC.name,
            matching_id=str(self.storage.matching_id),
        )
        self.metrics.set_value(
            AIMatchingMetric.n_rules_per_category,
            n_simple_parametric_rules,
            type=RuleType.SIMPLE_PARAMETRIC.name,
            matching_id=str(self.storage.matching_id),
        )

        self.metrics.set_value(
            AIMatchingMetric.n_rules_per_category,
            n_composition_rules,
            type=RuleType.COMPOSITION.name,
            matching_id=str(self.storage.matching_id),
        )
        self.metrics.set_value(
            AIMatchingMetric.n_composition_rules_depth,
            n_rule_depth,
            matching_id=str(self.storage.matching_id),
        )

    def _get_counts_for_rule_type(self, rule_type):
        """Count the number of different rule types [Parametric, Nonparametric, Composition]."""
        n_simple_type_rules = 0
        n_rule_depth = 0
        for rule_with_statistics in self.storage.extracted_rules.rules:
            if rule_type == CompositionRule and isinstance(rule_with_statistics.rule, CompositionRule):
                base_depth = len(rule_with_statistics.rule.non_parametric_rules)
                n_rule_depth = base_depth if rule_with_statistics.rule.parametric_rule is None else base_depth + 1

            if isinstance(rule_with_statistics.rule, rule_type):
                n_simple_type_rules += 1

        return n_simple_type_rules, n_rule_depth

    def _collect_rule_extraction_metrics(self):
        """Collect relevant prometheus end point metrics for each rule extraction step."""
        for interaction_type in [InteractionType.VALID, InteractionType.INVALID, InteractionType.REDUNDANT]:
            interaction_name = interaction_type.name
            for value in self.storage.rule_extractor.metrics_iter.n_rules_category[interaction_name]:
                self.metrics.set_value(
                    AIMatchingMetric.n_rule_extraction_iteration,
                    value,
                    type=interaction_name,
                    matching_id=str(self.storage.matching_id),
                )

        for value in self.storage.rule_extractor.metrics_iter.n_rules_category[InteractionType.GENERATED.name]:
            self.metrics.set_value(
                AIMatchingMetric.n_rule_extraction_iteration_rules_generated,
                value,
                matching_id=str(self.storage.matching_id),
            )

        for value in self.storage.rule_extractor.metrics_iter.time_spent:
            self.metrics.set_value(
                AIMatchingMetric.rule_extraction_iteration_processing_seconds,
                value,
                matching_id=str(self.storage.matching_id),
            )

        for interaction_type in [InteractionType.GENERATED, InteractionType.EVALUATED, InteractionType.EXTRACTED]:
            interaction_name = interaction_type.name
            self.metrics.set_value(
                AIMatchingMetric.n_rule_extraction_rules_total,
                self.storage.rule_extractor.metrics_total.n_rules_process[interaction_name],
                type=interaction_name,
                matching_id=str(self.storage.matching_id),
            )

        for pairs_type in [PairsType.POSITIVE, PairsType.NEGATIVE, PairsType.COVERED]:
            pairs_type_name = pairs_type.name
            self.metrics.set_value(
                AIMatchingMetric.n_rule_extraction_pairs_total,
                self.storage.rule_extractor.metrics_total.n_pairs_category[pairs_type_name],
                type=pairs_type_name,
                matching_id=str(self.storage.matching_id),
            )

        for stage in [RuleExtractionStage.GENERATION, RuleExtractionStage.EVALUATION, RuleExtractionStage.EXTRACTION]:
            stage_name = stage.name
            self.metrics.set_value(
                AIMatchingMetric.rule_extraction_total_processing_seconds,
                self.storage.rule_extractor.metrics_total.time_spent_process[stage_name],
                type=stage_name,
                matching_id=str(self.storage.matching_id),
            )


def next_phase_after_clustering(storage: SingleStorage) -> MatchingPhase:
    """Return the next phase based on the planned evaluation."""
    if storage.rules_extraction_state == ComputationState.PLANNED:
        return MatchingPhase.EXTRACTING_RULES
    elif storage.records_matching_state == ComputationState.PLANNED:
        return MatchingPhase.GENERATING_PROPOSALS
    else:
        return MatchingPhase.READY


def prepare_data_stream(storage: SingleStorage, mdc_grpc_client: GRPCClient) -> Iterator[RecordData]:
    """Create a stream of data from either MDC or a local file."""
    # Always fetch the id columns
    columns_to_fetch = [storage.record_id_column, storage.matching_id_column] + storage.used_columns
    data_stream = storage.fetch_mdc_data(mdc_grpc_client, columns_to_fetch)
    return data_stream
