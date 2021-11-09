"""Extensions of dedupe api module."""
from __future__ import annotations

import contextlib
import itertools
import sqlite3
import tempfile

from typing import TYPE_CHECKING

import affinegap
import dedupe._typing as dedupe_types
import dedupe.blocking
import dedupe.core
import dedupe.datamodel
import dedupe.predicates
import dedupe.variables.base
import dedupe.variables.string
import more_itertools
import numpy

from aicore.ai_matching.ata_dedupe.labeler import AtaDedupeDisagreementLearner, RobustRegularizedLogisticRegression
from aicore.ai_matching.enums import ProposalType


if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from typing import Optional

    from aicore.ai_matching.enums import MatchingDecision, Proposal
    from aicore.ai_matching.storage import SingleStorage
    from aicore.ai_matching.types import BlockingRules, ColumnName, RecordId, RecordIdsPair, Records


class NoIndexStringType(dedupe.variables.base.FieldType):
    """Custom data type for dedupe which does not use any index predicates."""

    type = "NoIndexString"  # Name of the data type that needs to be used in dedupe initialization
    _Predicate = dedupe.predicates.StringPredicate  # Use same predicate class as in dedupe.variables.string.StringType
    # Do not use any index predicates
    _index_predicates: Sequence[type[dedupe.predicates.IndexPredicate]] = []  # type: ignore
    # Use standard predicates as in dedupe.variables.string.StringType
    _predicate_functions = dedupe.variables.string.base_predicates + (
        dedupe.predicates.commonFourGram,
        dedupe.predicates.commonSixGram,
        dedupe.predicates.tokenFieldPredicate,
        dedupe.predicates.suffixArray,
        dedupe.predicates.doubleMetaphone,
        dedupe.predicates.metaphoneToken,
    )

    def __init__(self, definition):
        super().__init__(definition)
        # We are not using the other version of comparator anyways, so fix it here
        self.comparator = affinegap.normalizedAffineGapDistance


# Inject the custom type defined above into the mapping of dedupe types
field_classes = dedupe.datamodel.FIELD_CLASSES
field_classes[NoIndexStringType.type] = NoIndexStringType


class AtaDedupe(dedupe.Dedupe):
    """Implementation of Dedupe class to allow extended user operations."""

    classifier = RobustRegularizedLogisticRegression()  # Use our robust RLR to avoid problems with nans

    def __init__(
        self,
        variable_definition: list[dict],
        decision_threshold: float,
        num_cores: int = 1,  # 1 means no parallelization
        **kwargs,
    ) -> None:
        self.variable_definition = variable_definition
        super().__init__(self.variable_definition, num_cores=num_cores, **kwargs)

        self.active_learner: Optional[AtaDedupeDisagreementLearner] = None
        self.ActiveLearner = AtaDedupeDisagreementLearner
        self.decision_threshold = decision_threshold

    def remove_pair(self, pair_to_remove: RecordIdsPair, old_decision: MatchingDecision, record_id_name: str) -> bool:
        """Remove a pair from training data."""
        training_pairs = self.training_pairs[old_decision.to_dedupe()]
        for pair in training_pairs:
            if (pair[0][record_id_name], pair[1][record_id_name]) == pair_to_remove:
                training_pairs.remove(pair)
                return True

        return False

    def record_pairs_from_storage(
        self, storage: SingleStorage, batch_size: int = 5000
    ) -> Iterator[dedupe_types.RecordPairs]:
        """Perform blocking over all data and create distinct pairs of records from the blocks, see Dedupe pairs()."""
        pairs = self.perform_blocking(storage.mdc_data)

        for pairs_batch in more_itertools.chunked(pairs, batch_size):
            record_id_set = set(itertools.chain.from_iterable(pairs_batch))
            yield from generate_pairs_with_details(record_id_set, pairs_batch, storage)  # type: ignore

    def perform_blocking(
        self, mdc_records: Records, blocking_rules: Optional[BlockingRules] = None
    ) -> Iterator[RecordIdsPair]:
        """Perform blocking over all data and create distinct pairs of records from the blocks, see Dedupe pairs()."""
        with keep_original_predicates(self.fingerprinter):
            if blocking_rules is not None:
                self.fingerprinter.predicates = blocking_rules

            id_type = dedupe.core.sqlite_id_type(mdc_records)

            # Blocking and pair generation are typically the first memory bottlenecks,
            # so we'll use sqlite3 to avoid doing them in memory
            with tempfile.TemporaryDirectory() as temp_dir:
                con = sqlite3.connect(temp_dir + "/blocks.db")

                con.execute(f"CREATE TABLE blocking_map(block_key text, record_id {id_type})")

                con.executemany("INSERT INTO blocking_map values (?, ?)", self.fingerprinter(mdc_records.items()))

                con.execute("""CREATE INDEX block_key_idx ON blocking_map (block_key)""")
                pairs = con.execute(
                    """SELECT DISTINCT a.record_id, b.record_id
                                               FROM blocking_map a
                                               INNER JOIN blocking_map b
                                               USING (block_key)
                                               WHERE a.record_id < b.record_id"""
                )

                yield from pairs

                pairs.close()
                con.close()

    def uncertain_pairs_biased(self, match_distinct_diff: int) -> list[dedupe_types.TrainingExample]:
        """Provide a pair of records that gives the most information when labeled and remove it from the candidates."""
        assert self.active_learner, "Please initialize with the sample method"
        return [self.active_learner.pop_biased(match_distinct_diff)]

    def get_proposal_column_weights(self, proposal: Proposal, record_details: Records) -> dict[ColumnName, float]:
        """Get weighted distances of individual columns of a proposed pair."""
        record1 = record_details[proposal.id1]
        record2 = record_details[proposal.id2]
        # D0 ~ distances for identical entities
        zero_distances = self.data_model.distances([(record1, record1)])

        # Offset = Sum(D0*W) ~ addition to the decision for identical entities
        threshold_offset = numpy.sum(zero_distances * self.classifier.weights)

        # T ~ actual decision threshold, of score < T then SPLIT, else MERGE
        th = self.decision_threshold
        pair_score_threshold = numpy.log(th / (1 - th)) - self.classifier.bias

        # T0 = T-Offset ~ actual threshold taking the zero distance into account
        corrected_threshold = pair_score_threshold - threshold_offset

        # D ~ actual proposals distances
        field_distances = self.data_model.distances([(record1, record2)])

        # (D - D0) * W ~ scores shifted by zero distance
        shifted_scores = (field_distances - zero_distances) * self.classifier.weights

        # (D - D0) * W / T0 ~ normalized scores
        normalized_scores = shifted_scores / corrected_threshold
        normalized_scores = numpy.clip(normalized_scores, 0.0, 1.0)

        # scale weights into interval 0-1 according to how much the column adds to the decision
        if proposal.decision == ProposalType.MERGE:
            normalized_scores = 1 - normalized_scores

        variable_names = [var.field for var in self.data_model._variables]
        col_weights = {
            col_name: w
            for col_name, w in zip(variable_names, normalized_scores.ravel().tolist())
            if record1.get(col_name) and record2.get(col_name)
        }
        return col_weights

    def used_blocking_rule_columns(self, proposal: Proposal, record_details: Records) -> list[ColumnName]:
        """Get names of columns used for blocking the records in the proposal."""
        if proposal.decision == ProposalType.SPLIT:  # Split proposals were not blocked together
            return []

        column_names = []
        for predicate in self.predicates:
            record1_blocks = predicate(record_details[proposal.id1])
            record2_blocks = predicate(record_details[proposal.id2])

            if set(record1_blocks).isdisjoint(set(record2_blocks)):
                continue

            if isinstance(predicate, dedupe.predicates.CompoundPredicate):
                column_names += [simple_predicate.field for simple_predicate in predicate]
            else:
                column_names.append(predicate.field)

        # The names shouldn't be duplicated but we might want to keep order
        deduplicated: list[ColumnName] = []
        [deduplicated.append(x) for x in column_names if x not in deduplicated]  # type: ignore
        return deduplicated


def generate_pairs_with_details(
    record_id_set: set[RecordId], record_pairs: Iterator[RecordIdsPair], storage: SingleStorage
) -> Iterator[dedupe_types.RecordPairs]:
    """Produce pairs of records with details."""
    fetched_records_details = storage.fetch_record_details_by_ids(record_id_set)
    for record_id1, record_id2 in record_pairs:
        yield (record_id1, fetched_records_details[record_id1]), (record_id2, fetched_records_details[record_id2])


@contextlib.contextmanager
def keep_original_predicates(fingerprinter: dedupe.blocking.Fingerprinter):
    """Retain original blocking predicates in dedupe fingerprinter if they are overwritten."""
    original_predicates = fingerprinter.predicates

    yield  # Allow blocking process to finish before restoring original predicates in the fingerprinter.

    fingerprinter.predicates = original_predicates
