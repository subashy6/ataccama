"""Objects and operations representing persistent functionality."""

from __future__ import annotations

import csv
import dataclasses
import itertools
import operator

from typing import TYPE_CHECKING

import dedupe._typing as dedupe_types
import more_itertools
import numpy

from aicore.ai_matching import constants
from aicore.ai_matching.ata_dedupe.api import AtaDedupe
from aicore.ai_matching.commands import AiMatchingDataCommand
from aicore.ai_matching.constants import (
    OPTIMAL_LABELED_PAIRS,
    OPTIMAL_PAIRS_QUALITY_CONTRIBUTION,
    PROGRESS_DISTRIBUTION,
    REQUIRED_LABELED_PAIRS,
    REQUIRED_PAIRS_QUALITY_CONTRIBUTION,
    SubPhase,
)
from aicore.ai_matching.enums import (
    ComputationState,
    ErrorMessage,
    MatchingDecision,
    MatchingPhase,
    MdcColumnType,
    ParsingError,
    Proposal,
    ProposalType,
    RecordsMatchingStatus,
    RulesExtractionStatus,
    Status,
)
from aicore.ai_matching.rules_extraction import RuleExtractor, RulesWithCoverage
from aicore.ai_matching.serialization import convert_types
from aicore.common.grpc import GRPCClient


if TYPE_CHECKING:
    import datetime

    from collections.abc import Iterable, Iterator
    from typing import Any, Optional, TextIO

    from aicore.ai_matching.enums import MatchingId
    from aicore.ai_matching.types import (
        BlockingRules,
        ColumnName,
        GroupId,
        MatchingScores,
        MdcColumn,
        Proposals,
        RecordData,
        RecordId,
        RecordIdsPair,
        Records,
        TrainingPair,
    )
    from aicore.common.auth import Identity
    from aicore.common.types import CorrelationId


class SingleStorage:
    """Storage of results of single AI matching."""

    def __init__(self, matching_id: MatchingId, identity: Optional[Identity] = None):
        # False means the matching was restarted and the storage can be deleted once computation finishes
        self.active: bool = True

        # Common information for all steps
        self.matching_id: MatchingId = matching_id
        self.identity: Optional[Identity] = identity  # Identity of user who initiated AI matching
        self.last_command_correlation_id: CorrelationId = ""  # Correlation id of the last user action
        # Identity of user of the last user action
        self.last_command_identity: Optional[Identity] = identity

        self.used_columns: list[MdcColumn] = []
        self.n_total_records_count_initialization: int = 0
        self.n_total_records_count_fetching: int = 0
        self.matching_id_column: Optional[MdcColumn] = None
        self.record_id_column: Optional[MdcColumn] = None

        # Progress info
        self.phase: MatchingPhase = MatchingPhase.NOT_CREATED
        self.subphase: str = SubPhase.SUBPHASE_NOT_CREATED.name  # Currently computed sub-phase of the current phase
        self._progress: float = 0.0  # Total progress of the whole matching (unadjusted by what was planned)
        self.phase_progress: float = 0.0  # Progress of the current phase
        self.model_update_time: Optional[datetime.datetime] = None
        self.model_quality: float = 0.0  # Estimated model quality from [0, 1] based on number of labeled pairs
        self.error_message: Optional[ErrorMessage] = None
        self.progress_distribution: dict[MatchingPhase, float] = PROGRESS_DISTRIBUTION.copy()

        # Initialization
        self.data_file_path: str = ""  # If filled, data will be read from a local file instead of over gRPC
        self.dialect: str = "csv_semicolon_separated"  # Dialect used when reading from file
        self.deduper: Optional[AtaDedupe] = None

        # Training
        self.prepared_training_pair: Optional[RecordIdsPair] = None
        self.skip_training_phase: bool = False  # Whether the training phase should be immediately skipped
        # Training pairs (whole records) labeled by the users, records in each pair are sorted by their id ascending
        # they are stored directly in the deduper for now - self.deduper.training_pairs: dedupe_types.TrainingData

        # Fetching (used also for sampled records during initialization and training)
        self.mdc_data: Records = {}

        # Bocking
        self.blocked_record_pairs_generator: Optional[dedupe_types.RecordPairs] = None
        self._n_blocking_rules: int = 0

        # Scoring
        # All blocked pairs with matching score = probability of them being a MATCH
        self.matching_scores: Optional[MatchingScores] = None

        # Clustering
        self.clusters: dict[RecordId, RecordData] = {}  # RecordData columns are "id", "cluster_id", "score"
        self.clustering_state: ComputationState = ComputationState.NOT_PLANNED  # State of the common part of
        # the computation (FETCHING_RECORDS, BLOCKING_RECORDS, SCORING_PAIRS, CLUSTERING_RECORDS)

        # Records matching
        self.records_matching_state: ComputationState = ComputationState.NOT_PLANNED
        self.cached_proposals_count: Optional[int] = None  # number of proposals with precomputed explainability
        self.confidence_threshold: Optional[float] = None  # confidence threshold on proposals for caching
        self.proposals: Proposals = {}
        # Number of extracted proposals of each type
        self.proposal_counts: dict[ProposalType, int] = {ProposalType.MERGE: 0, ProposalType.SPLIT: 0}
        # Proposals with computed explainability (key columns, column scores)
        self.cached_proposals: dict[ProposalType, list[Proposal]] = {ProposalType.MERGE: [], ProposalType.SPLIT: []}

        # Rules extraction
        self.rule_extractor: Optional[RuleExtractor] = None  # Instance of rule extractor with metrics
        self.rules_extraction_state: ComputationState = ComputationState.NOT_PLANNED
        self.extracted_rules: Optional[RulesWithCoverage] = None
        self.min_match_confidence: Optional[float] = None  # Minimal confidence of MATCH pairs for rules extraction
        # Minimal confidence of DISTINCT pairs for rules extraction
        self.min_distinct_confidence: Optional[float] = None

    def get_blocking_rules(self) -> BlockingRules:
        """Get the blocking rules used to group records together from storage."""
        if self.deduper is not None and hasattr(self.deduper, "predicates"):
            return list(self.deduper.predicates)
        else:
            return []

    @property
    def progress(self) -> float:
        """Return total progress of the matching adjusted for what computations were planned so that it leads to 1.0."""
        if self.clustering_state == ComputationState.NOT_PLANNED:
            return self._progress

        adjustment = 0.0
        # Skipped phase is added as if it was finished, thus making the progress 100% once the other phase finishes
        if self.rules_extraction_state == ComputationState.NOT_PLANNED:
            adjustment += self.progress_distribution[MatchingPhase.EXTRACTING_RULES]
        if self.records_matching_state == ComputationState.NOT_PLANNED:
            adjustment += self.progress_distribution[MatchingPhase.GENERATING_PROPOSALS]

        return self._progress + adjustment

    def add_phase_progress(self, finished_part: float):
        """Add global progress based on the finished part of the current phase and its contribution to the matching."""
        self.phase_progress += finished_part
        self._progress += finished_part * self.progress_distribution[self.phase]

    def set_phase_progress(self, new_progress: float):
        """Update the total progress based on the progress of the current phase and its contribution to the matching."""
        self.add_phase_progress(-self.phase_progress)
        self.add_phase_progress(new_progress)

    def get_training_counts(self, decision: MatchingDecision) -> int:
        """Return the number of training pairs labeled by the specified decision."""
        if not self.deduper:
            return 0
        return len(self.deduper.training_pairs[decision.to_dedupe()])

    def generate_status_message(self) -> Status:
        """Return a status message containing information about the matching."""
        n_rules = len(self.extracted_rules.rules) if self.extracted_rules is not None else 0

        message = Status(
            self.matching_id,
            self.phase,
            self.progress,
            self.model_update_time,
            self.model_quality,
            self.get_training_counts(MatchingDecision.MATCH),
            self.get_training_counts(MatchingDecision.DISTINCT),
            len(self.used_columns),
            self.clustering_state,
            RecordsMatchingStatus(
                self.records_matching_state,
                self.proposal_counts[ProposalType.MERGE],
                self.proposal_counts[ProposalType.SPLIT],
                self.cached_proposals_count,
                self.confidence_threshold,
            ),
            RulesExtractionStatus(
                self.rules_extraction_state,
                n_rules,
                self.min_match_confidence,
                self.min_distinct_confidence,
            ),
            dataclasses.replace(self.error_message) if self.error_message is not None else None,
        )

        return message

    def fetch_mdc_data(self, mdc_grpc_client: GRPCClient, columns: list[MdcColumn]) -> Iterator[RecordData]:
        """Stream all data records from MDC database or from a local file."""
        if self.data_file_path:
            try:
                with open(self.data_file_path, encoding="utf-8-sig") as file:
                    yield from read_file(file, columns, self.dialect)
            except Exception as error:
                raise ParsingError(
                    f"Error while fetching records from " f"file {self.data_file_path}: {repr(error)}"
                ) from error

        else:
            # Do not request ID, it is always included
            data_request_command = AiMatchingDataCommand(
                self.matching_id.layer_name, self.matching_id.entity_name, columns[1:]
            )
            mdc_grpc_client.send(data_request_command, self.last_command_correlation_id, self.identity)
            data_stream: Iterator[RecordData] = data_request_command.data_records
            yield from data_stream

    def store_mdc_data(self, mdc_data: Iterator[RecordData]) -> None:
        """Store MDC data to prevent needing requesting them from MDC often."""
        _, id_column_name = self.record_id_column  # type: ignore
        for record in mdc_data:
            self.mdc_data[record[id_column_name]] = record

    def fetch_record_details_by_ids(self, ids_to_fetch: Iterable[RecordId]) -> Records:
        """Fetch record details from local storage given their ids."""
        return {record_id: self.mdc_data[record_id] for record_id in ids_to_fetch}

    def fetch_all_training_pairs(self) -> list[TrainingPair]:
        """Fetch all training pairs."""
        record_id_name = self.record_id_column[1]
        distinct_pairs = [
            (stored_pair[0][record_id_name], stored_pair[1][record_id_name], MatchingDecision.DISTINCT)
            for stored_pair in self.deduper.training_pairs[MatchingDecision.DISTINCT.to_dedupe()]
        ]
        match_pairs = [
            (stored_pair[0][record_id_name], stored_pair[1][record_id_name], MatchingDecision.MATCH)
            for stored_pair in self.deduper.training_pairs[MatchingDecision.MATCH.to_dedupe()]
        ]
        return distinct_pairs + match_pairs

    def fetch_training_pair_data(self, pair: RecordIdsPair) -> tuple[RecordData, RecordData]:
        """Fetch pair of records from MDC by their IDs."""
        data_records = self.fetch_record_details_by_ids(pair)
        return data_records[pair[0]], data_records[pair[1]]

    def fetch_training_pair(self, pair: RecordIdsPair) -> Optional[TrainingPair]:
        """Return particular training example or None if it is not present in the storage."""
        record_id_name = self.record_id_column[1]

        for stored_pair in self.deduper.training_pairs[MatchingDecision.DISTINCT.to_dedupe()]:
            if (stored_pair[0][record_id_name], stored_pair[1][record_id_name]) == pair:
                return pair[0], pair[1], MatchingDecision.DISTINCT

        for stored_pair in self.deduper.training_pairs[MatchingDecision.MATCH.to_dedupe()]:
            if (stored_pair[0][record_id_name], stored_pair[1][record_id_name]) == pair:
                return pair[0], pair[1], MatchingDecision.MATCH

        return None  # The training example is not present in the storage.

    def remove_training_pair(self, pair: RecordIdsPair, old_decision: MatchingDecision):
        """Remove particular training example from training data."""
        record_id_name = self.record_id_column[1]

        training_pairs = self.deduper.training_pairs[old_decision.to_dedupe()]
        for stored_pair in training_pairs:
            if (stored_pair[0][record_id_name], stored_pair[1][record_id_name]) == pair:
                to_remove = stored_pair
                break
        else:
            raise KeyError(f"Pair {pair} with decision {old_decision} is not present in the training data.")
        training_pairs.remove(to_remove)

        # Removed it also from deduper
        self.deduper.remove_pair(pair, old_decision, record_id_name)

    def clear_training(self):
        """Remove all labeled training pairs."""
        self.deduper.training_pairs = dedupe_types.TrainingData(distinct=[], match=[])  # To keep the attribute there
        self.update_model_quality()

    def update_model_quality(self):
        """Update the estimation of model quality based on the number of labeled pairs provided by the users."""
        n_match_pairs = self.get_training_counts(MatchingDecision.MATCH)
        n_distinct_pairs = self.get_training_counts(MatchingDecision.DISTINCT)

        quality = self.model_quality_contribution(n_match_pairs) + self.model_quality_contribution(n_distinct_pairs)
        self.model_quality = quality

    @staticmethod
    def model_quality_contribution(n_labeled_pairs: int) -> float:
        """Return the model contribution for n number of labeled pairs for a particular `MatchDecision`."""
        perc_labeled_required_pairs = min(n_labeled_pairs / REQUIRED_LABELED_PAIRS, 1.0)
        contribution = perc_labeled_required_pairs * REQUIRED_PAIRS_QUALITY_CONTRIBUTION

        if n_labeled_pairs >= REQUIRED_LABELED_PAIRS:
            perc_labeled_optimal_pairs = min(
                (n_labeled_pairs - REQUIRED_LABELED_PAIRS) / (OPTIMAL_LABELED_PAIRS - REQUIRED_LABELED_PAIRS), 1.0
            )
            contribution += perc_labeled_optimal_pairs * OPTIMAL_PAIRS_QUALITY_CONTRIBUTION

        return contribution

    def fetch_proposal_info(self, proposal_record_ids: RecordIdsPair) -> Optional[Proposal]:
        """Try to fetch proposal from cache or stored proposals by its record its."""
        for proposal in itertools.chain.from_iterable(self.cached_proposals.values()):
            if (proposal.id1, proposal.id2) == proposal_record_ids:
                return proposal

        return self.proposals.get(proposal_record_ids)

    def discard_proposal(self, pair: RecordIdsPair) -> Optional[Proposal]:
        """Discard a proposal and do not learn from the feedback."""
        for proposal_type in self.cached_proposals:
            for proposal in self.cached_proposals[proposal_type]:
                if (proposal.id1, proposal.id2) == pair:
                    self.cached_proposals[proposal_type].remove(proposal)
                    self.proposal_counts[proposal_type] -= 1
                    break

        return self.proposals.pop(pair, None)

    def store_clusters(self, clusters: dedupe_types.Clusters) -> None:
        """Store clusters into searchable format."""
        record_id_type, record_id_column_name = self.record_id_column  # type: ignore
        for cluster_id, (cluster, scores) in enumerate(clusters):
            for record_id, score in zip(cluster, scores):
                self.clusters[record_id] = {
                    # Convert from numpy to python types
                    record_id_column_name: convert_types[record_id_type](record_id),
                    constants.CLUSTER_ID_COLUMN: cluster_id,
                    constants.SCORE_VALUE_COLUMN: score,
                }

    @classmethod
    def iter_batch_of_groups(
        cls, data_sorted_by_group: Iterable[tuple[GroupId, RecordId]], batch_size: int = 100
    ) -> Iterator[list[list[RecordId]]]:
        """Generate batches of grouped records (records with the same group_id)."""
        same_group_iterator = cls.iter_records_with_same_group_id(data_sorted_by_group)
        return more_itertools.chunked(same_group_iterator, batch_size)

    @classmethod
    def get_grouped_pairs_covered_by_ids(
        cls,
        record_ids: set[RecordId],
        data_to_query: Records,
        group_id_column_name: ColumnName,
    ) -> set[RecordIdsPair]:
        """Get all unique pairs with the same master/cluster group covered by given record IDs."""
        present_in_data: list[tuple[GroupId, RecordId]] = []
        for record_id in record_ids:
            record = data_to_query.get(record_id, None)
            if record is not None:
                present_in_data.append((record[group_id_column_name], record_id))

        sorted_by_group_id = sorted(present_in_data, key=operator.itemgetter(0))

        groups = cls.iter_records_with_same_group_id(sorted_by_group_id)
        unique_pairs = cls.get_pairs_from_groups(groups)
        return unique_pairs

    @staticmethod
    def iter_records_with_same_group_id(
        records_generator: Iterable[tuple[GroupId, RecordId]]
    ) -> Iterator[list[RecordId]]:
        """Generate lists of record IDs with same group id from a generator of sorted records."""
        for _, group in itertools.groupby(records_generator, operator.itemgetter(0)):
            yield [record_id for _, record_id in group]

    @classmethod
    def get_pairs_from_groups(cls, groups: Iterable[list[RecordId]]):
        """Return all unique pairs of ids where both belong to the same group."""
        pairs_present_in_groups = (cls.get_pairs_from_group(group) for group in groups)
        pairs = set(itertools.chain.from_iterable(pairs_present_in_groups))
        return pairs

    @staticmethod
    def get_pairs_from_group(group: list[RecordId]) -> set[RecordIdsPair]:
        """Return set of all possible pairs created from elements of given group."""
        pairs = set()
        if len(group) > 1:
            # The pairs may not be sorted by their ids from the clustering step. We need to ensure correct ordering.
            pairs = set(itertools.combinations(sorted(group), 2))
        return pairs

    def store_unscored_proposals(self, proposal_pairs: Iterable[RecordIdsPair], proposal_type: ProposalType) -> None:
        """Store not yet scored proposals into storage."""
        for id_pair in proposal_pairs:
            self.proposals[id_pair] = Proposal(id_pair[0], id_pair[1], 0.0, proposal_type)
            self.proposal_counts[proposal_type] += 1

    def fetch_proposals_batches(self, batch_size: int) -> Iterator[Proposals]:
        """Fetch stored proposals by batches."""
        for proposal_batch in more_itertools.chunked(self.proposals.items(), batch_size):
            yield dict(proposal_batch)

    @staticmethod
    def get_most_confident_proposals(scored_proposals: list[Proposal], required_counts: int) -> list[Proposal]:
        """Efficiently find UNSORTED, most confident proposals."""
        if len(scored_proposals) <= required_counts:
            return scored_proposals

        scores = numpy.array([proposal.confidence for proposal in scored_proposals])
        # Scores higher than threshold are put after the k-th score, so they are taken from the end of the array
        most_confident_indices = numpy.argpartition(scores, -required_counts)[-required_counts:]
        return [scored_proposals[idx] for idx in most_confident_indices]

    def prepare_new_training_pair_if_resolved(self):
        """
        Prepare next not yet labeled training pair with largest added informative value for user evaluation.

        New pair is prepared only if there is none prepared. None is prepared if there are no more unlabeled pairs.
        """
        if self.prepared_training_pair is not None:
            return

        # The selected pair might have been already labeled (UpdateTrainingPairCommand was called for that pair)
        # or if the service restarted and kept the training data
        while True:
            training_pair = self.pop_new_training_pair()
            if training_pair is None:
                return  # No more training pairs, stays None

            already_labeled = self.fetch_training_pair(training_pair)
            if already_labeled is None:
                break

        self.prepared_training_pair = training_pair

    def pop_new_training_pair(self) -> Optional[RecordIdsPair]:
        """
        Return a training pair giving the most information for active learning.

        It is takes trying to balance the MATCH vs DISTINCT labeled pairs to have a balanced training data.
        A new pair is returned every time this method is called (it is removed from the candidate pairs).
        None is returned if there are no more training pairs.
        The records in the pair are sorted based on the record ids.
        """
        if len(self.deduper.active_learner.candidates) == 0:
            return None  # No more training pairs to label

        labeled_counts_imbalance = self.get_training_counts(MatchingDecision.MATCH) - self.get_training_counts(
            MatchingDecision.DISTINCT
        )
        uncertain_pairs = self.deduper.uncertain_pairs_biased(labeled_counts_imbalance)

        (record_pair,) = uncertain_pairs

        # Sort the records in the pair
        record_id_column_name = self.record_id_column[1]
        ids = [record[record_id_column_name] for record in record_pair]
        return min(ids), max(ids)

    def get_proposals(self, confidence_threshold, decision, proposals_count):
        """Return at most requested number of proposals of selected type(s) with confidence over specified threshold."""
        cached_proposals = self.cached_proposals  # fetch cached proposals
        proposals_to_show = []
        if decision in [ProposalType.MERGE, ProposalType.ALL]:
            proposals_to_show.extend(
                self.select_proposals(cached_proposals[ProposalType.MERGE], confidence_threshold, proposals_count)
            )
        if decision in [ProposalType.SPLIT, ProposalType.ALL]:
            proposals_to_show.extend(
                self.select_proposals(cached_proposals[ProposalType.SPLIT], confidence_threshold, proposals_count)
            )
        return proposals_to_show

    @staticmethod
    def select_proposals(
        specific_proposals: list[Proposal], confidence_threshold: float, proposals_count: int
    ) -> list[Proposal]:
        """Prepare sorted proposals thresholded by their count and confidence."""
        proposals_to_show: list[Proposal] = []
        for proposal in sorted(specific_proposals, key=operator.attrgetter("confidence"), reverse=True):

            if proposal.confidence < confidence_threshold or len(proposals_to_show) == proposals_count:
                break

            proposals_to_show.append(proposal)

        return proposals_to_show


def read_file(file: TextIO, columns: list[MdcColumn], dialect: str = "csv_semicolon_separated") -> Iterator[RecordData]:
    """Iterate over selected columns read from a local data file."""
    columns_types = {column_name: column_type for column_type, column_name in columns}
    reader = csv.DictReader(file, dialect=dialect)

    for row in reader:
        parsed_row_selected_columns = (
            (column_name, preprocess_data_value(row[column_name], column_type))
            for column_name, column_type in columns_types.items()
        )

        yield dict(parsed_row_selected_columns)


def preprocess_data_value(value: Any, column_type: MdcColumnType) -> Any:
    """Process data value given the column type."""
    if not value:
        return None

    type_function = convert_types[column_type]
    return type_function(value)


class CsvSemicolonSeparated(csv.Dialect):
    """Describe the usual properties of Excel-generated CSV files - separated by semicolons."""

    delimiter = ";"
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = "\r\n"
    quoting = csv.QUOTE_MINIMAL


class CsvCommaSeparated(csv.Dialect):
    """Describe the usual properties of Excel-generated CSV files - separated by commas."""

    delimiter = ","
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = "\r\n"
    quoting = csv.QUOTE_MINIMAL


csv.register_dialect("csv_semicolon_separated", CsvSemicolonSeparated)
csv.register_dialect("csv_comma_separated", CsvCommaSeparated)
