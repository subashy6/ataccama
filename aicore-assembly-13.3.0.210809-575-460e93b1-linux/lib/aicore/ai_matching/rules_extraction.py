"""Decision Rules extraction counterpart for AI Matching."""
from __future__ import annotations

import abc
import dataclasses
import enum
import itertools

from typing import TYPE_CHECKING, TypeVar

import affinegap.affinegap as affinegap
import jellyfish
import more_itertools

from aicore.ai_matching.enums import MatchingId
from aicore.ai_matching.registry import InteractionType, LogId, PairsType, RuleExtractionStage
from aicore.ai_matching.utils.logging import log_info, log_warning
from aicore.common.logging import Logger
from aicore.common.utils import datetime_now


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Sequence
    from typing import Any, Optional

    from aicore.ai_matching.types import (
        ColumnName,
        CoverageValue,
        DistanceFunction,
        DistanceValue,
        RecordData,
        RecordIdsPair,
        RecordIdsPairSet,
        Records,
        ThresholdValue,
    )
    from aicore.common.auth import Identity
    from aicore.common.types import CorrelationId


@dataclasses.dataclass
class NamedDistanceFunction:
    """Distance function with an associated name."""

    name: str
    function: DistanceFunction

    def __call__(self, string1: str, string2: str) -> DistanceValue:
        """Compute the distance between two strings."""
        return self.function(string1, string2)  # type: ignore #[call-arg]


def jaro_winkler_distance(string1: str, string2: str) -> DistanceValue:
    """Return Jaro-Winkler distance of two strings (https://en.wikipedia.org/wiki/Jaro%E2%80%93Winkler_distance)."""
    return 1.0 - jellyfish.jaro_winkler_similarity(string1, string2)


# Distance function used to compare two strings - the only one Rules extraction supports for now
AFFINE_GAP_DISTANCE = NamedDistanceFunction("affine gap distance", affinegap.affineGapDistance)
DAMERAU_LEVENSHTEIN_DISTANCE = NamedDistanceFunction("Damerau-Levenshtein", jellyfish.damerau_levenshtein_distance)
JARO_WINKLER_DISTANCE = NamedDistanceFunction("Jaro-Winkler", jaro_winkler_distance)
MAX_DISTANCE = 999999
DEFAULT_MAX_COLUMNS = 5  # Maximum number of columns considered in one rule

SINGLE_COLUMN_PARAMETRIC_RULES: list[Callable[[ColumnName], ParametricRuleBase]] = [
    lambda column: DistanceRule(column, DAMERAU_LEVENSHTEIN_DISTANCE, match_empty=False),
    lambda column: DistanceRule(column, DAMERAU_LEVENSHTEIN_DISTANCE, match_empty=True),
]

SINGLE_COLUMN_NONPARAMETRIC_RULES: list[Callable[[ColumnName], NonparametricRuleBase]] = [
    lambda column: EqualityRule(column, match_empty=False),
    lambda column: EqualityRule(column, match_empty=True),
]

MULTI_COLUMN_RULES: list[Callable[[list[NonparametricRuleBase], Optional[ParametricRuleBase]], CompositionRule]] = [
    lambda non_parametric_rules, parametric_rule: CompositionRule(non_parametric_rules, parametric_rule),
]


class RuleValidity(enum.Enum):
    """Describes validity of a rule with respect to all possible generated rules."""

    INVALID = 0  # The rule covers some negative example
    VALID = 1  # The rule covers no negative example but one/ many positive examples
    REDUNDANT = 2  # The rule is not necessary as existing rules already cover these cases


T = TypeVar("T")


class RuleBase(abc.ABC):
    """Apply an appropriate function on a record pair and decide whether they should be matched."""

    def __init__(self):
        self.validity: Optional[RuleValidity] = None  # Validity of the rule, None means it has not yet been validated
        # Name and hash need to be updated after changes of a tunable param
        self.precomputed_name: str = self.compute_full_name()
        self.precomputed_hash: int = self.compute_hash()

    @abc.abstractmethod
    def match(self, record1: RecordData, record2: RecordData) -> bool:
        """Decide if two records should be matched."""

    @abc.abstractmethod
    def clone(self: T) -> T:
        """Return a new instance of the same rule, with the same config params."""

    def compute_full_name(self) -> str:
        """Compute full name of the rule based on its config and tunable params."""
        params = self.get_params()
        return f"{self.get_rule_name()}{self.columns} {params}"

    def compute_hash(self) -> int:
        """Compute hash of the rule."""
        return hash(self.precomputed_name)

    def update_name_and_hash(self):
        """Update the precomputed name and hash."""
        self.precomputed_name = self.compute_full_name()
        self.precomputed_hash = self.compute_hash()

    def get_rule_name(self) -> str:
        """Get name of the Rule in string form."""
        class_name = self.__class__.__name__
        return class_name.replace("Rule", "")

    def get_params(self) -> dict[str, Any]:
        """Get the names and values of both the rule tunable and config parameters."""
        return {}

    @property
    @abc.abstractmethod
    def columns(self) -> list[ColumnName]:
        """Columns used by the rule."""

    def __repr__(self) -> str:
        return self.precomputed_name

    # Overriding the default __eq__ method also removes the corresponding __hash__ method causing Set operations to fail
    # Need to implement our own __hash__ method to retain this functionality
    def __hash__(self):
        return self.precomputed_hash

    def __eq__(self, other: Any) -> bool:
        """Two rules are equal if they equal in the repr, as it contains its name and all config and tunable params."""
        if not isinstance(other, RuleBase):
            return NotImplemented

        return self.precomputed_name == other.precomputed_name


class ParametricRuleBase(RuleBase, abc.ABC):
    """A rule with one or more parameters which can be tuned."""

    @abc.abstractmethod
    def get_params(self) -> dict[str, Any]:
        """Get the names and values of both the rule tunable and config parameters."""

    def set_best_params_and_validate(self, records: Records, negative_pairs: Iterable[RecordIdsPair]):
        """Set best params and validate (see `_set_best_params_and_validate()`) and the recompute the rule name."""  # noqa D402
        self._set_best_params_and_validate(records, negative_pairs)
        self.update_name_and_hash()

    @abc.abstractmethod
    def _set_best_params_and_validate(self, records: Records, negative_pairs: Iterable[RecordIdsPair]):
        """
        Find and set the best params and validity of the rule.

        Find and set best values of the tunable parameters so that the rule covers as most positive examples as possible
        and no negative one.

        Set validity as:
             - INVALID if no such parameters exist
             - REDUNDANT if it is guaranteed that a simpler VALID rule covering the same positive pairs exists
             - VALID if the rule covers some positive pairs and no negative ones and is not REDUNDANT
        """


class NonparametricRuleBase(RuleBase, abc.ABC):
    """A rule which does not have any tunable parameters, just the config ones."""

    @abc.abstractmethod
    def validate(self, records: Records, negative_pairs: Iterable[RecordIdsPair]):
        """Validate if the rule does not cover any negative pair or is redundant.

        Set validity as:
             - INVALID if the rule covers some negative pair
             - REDUNDANT if it is guaranteed that a simpler VALID rule covering the same positive pairs exists
             - VALID if the rule covers some positive pairs and no negative ones and is not REDUNDANT
        """


class AlwaysMatchRule(NonparametricRuleBase):
    """Rule which matches any records, is valid only if ther are no negative pairs.

    Its purpose is to be able to create a tree where the REDUNDANT rules can be discarded as there is in such case
    always a parent which is simpler and has the same coverage.
    """

    def clone(self) -> AlwaysMatchRule:
        """Return a new instance of the same rule, with the same config params."""
        return AlwaysMatchRule()

    @property
    def columns(self) -> list[ColumnName]:
        """Return an empty list as the rule does not use any column."""
        return []

    def get_params(self) -> dict[str, Any]:
        """Return an empty dict as the rule has no config params."""
        return {}

    def match(self, _record1: RecordData, _record2: RecordData) -> bool:
        """Return True as this rule matches anything."""
        return True

    def validate(self, _records: Records, negative_pairs: Iterable[RecordIdsPair]):
        """Set validity of the rule."""
        negative_pair = more_itertools.first(negative_pairs, default=None)
        # If there is a negative pair it matches it as it matches everything and thus is invalid
        self.validity = RuleValidity.VALID if negative_pair is None else RuleValidity.INVALID


class EqualityRule(NonparametricRuleBase):
    """Matches two records if they are equal in one column."""

    def __init__(self, column: ColumnName, match_empty: bool):
        self._column = column
        self._match_empty = match_empty  # Config param - consider an empty value equal to anything else / dissimilar to
        # anything else (even other empty value)
        super().__init__()

    def clone(self) -> EqualityRule:
        """Return a new instance of the same rule, with the same config params."""
        return EqualityRule(self._column, self._match_empty)

    @property
    def columns(self) -> list[ColumnName]:
        """Return column used by the rule."""
        return [self._column]

    def get_params(self) -> dict[str, Any]:
        """Return the config param and its value."""
        return {"match_empty": self._match_empty}

    def match(self, record1: RecordData, record2: RecordData) -> bool:
        """Compare the selected columns if they are equal."""
        value1 = record1[self._column]
        value2 = record2[self._column]
        if value1 is None or value2 is None:
            return self._match_empty

        return value1 == value2

    def validate(self, records: Records, negative_pairs: Iterable[RecordIdsPair]):
        """Check if it doesn't match any negative example."""
        matches_at_least_one_pair = False

        for pair in negative_pairs:
            matches_at_least_one_pair = True
            if self.match(records[pair[0]], records[pair[1]]):
                self.validity = RuleValidity.INVALID
                return

        # AlwaysMatchRule is simpler if there are no positive pairs this rule would match
        self.validity = RuleValidity.REDUNDANT if not matches_at_least_one_pair else RuleValidity.VALID


class DistanceRule(ParametricRuleBase):
    """Matches two records if a distance between them w.r.t one column is smaller than a threshold."""

    def __init__(
        self,
        column: ColumnName,
        distance_function: NamedDistanceFunction,  # Config param
        match_empty: bool,  # Config param  - None values will be considered similar vs dissimilar
        threshold: ThresholdValue = None,  # Tunable param
    ):
        self._column = column
        self._match_empty = match_empty
        self._distance_function = distance_function
        self._threshold = threshold
        # Beware: When changing the params manually, recompute_full_name_and_hash() needs to be called, otherwise
        # the name and hash are not updated and thus equality and hash does not work well
        super().__init__()

    def clone(self) -> DistanceRule:
        """Return a new instance of the same rule, with the same config params."""
        return DistanceRule(self._column, self._distance_function, self._match_empty)

    @property
    def columns(self) -> list[ColumnName]:
        """Return the column used by the rule."""
        return [self._column]

    def get_params(self) -> dict[str, Any]:
        """Get the names and values of the parameters used by the rule."""
        return {
            "function": self._distance_function.name,
            "match_empty": self._match_empty,
            "threshold": self._threshold,
        }

    def distance(self, record1: RecordData, record2: RecordData) -> DistanceValue:
        """Apply the desired distance function to a record pair of interest."""
        value1 = record1[self._column]
        value2 = record2[self._column]

        if value1 is None or value2 is None:
            if self._match_empty:  # Consider empty values to be similar
                return 0
            else:
                return MAX_DISTANCE  # Consider empty values to be different

        return self._distance_function(value1, value2)

    def match(self, record1: RecordData, record2: RecordData) -> bool:
        """Compare if the distance between two records is lower than the threshold."""
        return self.distance(record1, record2) < self._threshold

    def _set_best_params_and_validate(self, records: Records, negative_pairs: Iterable[RecordIdsPair]):
        """Find maximum threshold which does not match any negative pair (thus matches most of the positive pairs)."""
        min_distance = min(
            (self.distance(records[id1], records[id2]) for id1, id2 in negative_pairs), default=MAX_DISTANCE
        )
        self._threshold = min_distance

        if min_distance == 0:  # Could be improved if we knew that the a higher value is the theoretical minimum
            self.validity = RuleValidity.INVALID
        elif min_distance == MAX_DISTANCE:
            # This means one of:
            # - there are no negative pairs: AlwaysMatchRule is simpler
            # - all negative pairs have None and self._match_empty == True: EqualityRule(match_empty=True) is simpler
            self.validity = RuleValidity.REDUNDANT
        else:
            self.validity = RuleValidity.VALID


class CompositionRule(ParametricRuleBase):
    """Combines at most one parametric rule and 1 to N non-parametric by conjunction (Rule1 AND Rule2 AND ... )."""

    def __init__(
        self,
        non_parametric_rules: list[NonparametricRuleBase],
        parametric_rule: Optional[ParametricRuleBase] = None,
    ):
        self.non_parametric_rules = non_parametric_rules
        self.parametric_rule = parametric_rule

        # Marks which of the non-parametric rules has the potential to be useful
        self.useful_rules: set[NonparametricRuleBase] = set()
        super().__init__()

    def clone(self) -> CompositionRule:
        """Return a new instance of the same rule, with the same config params."""
        cloned_parametric_rule = self.parametric_rule.clone() if self.parametric_rule is not None else None
        cloned_nonparametric_rules = [rule.clone() for rule in self.non_parametric_rules]
        return CompositionRule(cloned_nonparametric_rules, cloned_parametric_rule)

    @property
    def columns(self) -> list[ColumnName]:
        """Return empty list because the rule does not work with any columns directly."""
        return []

    @property
    def subrules_columns(self) -> list[ColumnName]:
        """Return columns used by the subrules."""
        all_columns = itertools.chain.from_iterable(rule.columns for rule in self.all_rules)
        # Deduplicate the names while keeping the deterministic order
        deduplicated: list[ColumnName] = []
        for x in all_columns:
            if x not in deduplicated:
                deduplicated.append(x)
        return deduplicated

    def get_params(self) -> dict[str, Any]:
        """Return an empty dictionary because the rule does not have any params (aside from those in the sub-rules)."""
        return {}

    @property
    def all_rules(self) -> Iterator[RuleBase]:
        """Iterate over all sub rules."""
        yield from self.non_parametric_rules
        if self.parametric_rule is not None:
            yield self.parametric_rule

    def match(self, record1: RecordData, record2: RecordData) -> bool:
        """Match the records if all of the rules match them."""
        return all(rule.match(record1, record2) for rule in self.all_rules)

    def matched_using_nonparametric(
        self, records: Records, negative_pairs: Iterable[RecordIdsPair]
    ) -> Iterator[RecordIdsPair]:
        """Filter the negative pairs by non-parametric rules, yielding only pairs which are matched by all subrules.

        Also mark as useful the non-parametric subrules which NOT match at least one pair which all other do match.
        I.e., rule is useful if by removing it the non-parametric subrules would match more negative pairs.
        """
        self.useful_rules.clear()
        for pair in negative_pairs:
            record0, record1 = records[pair[0]], records[pair[1]]
            unmatched_by = iter(rule for rule in self.non_parametric_rules if not rule.match(record0, record1))
            first_nonmatching = next(unmatched_by, None)
            if first_nonmatching is None:  # Matched by all
                yield pair
            else:
                if first_nonmatching not in self.useful_rules:
                    second_nonmatching = next(unmatched_by, None)
                    if second_nonmatching is None:  # Unmatched thanks to only `first_nonmatching` rule -> it is useful
                        self.useful_rules.add(first_nonmatching)

    def _set_best_params_and_validate(self, records: Records, negative_pairs: Iterable[RecordIdsPair]):
        """Find the best param of the parametric rule and set the validity of the whole composition rule."""
        matched_negative_pairs = self.matched_using_nonparametric(records, negative_pairs)

        if self.parametric_rule is not None:  # Validity depends also on the validity of the parametric rule
            self.parametric_rule.set_best_params_and_validate(records, matched_negative_pairs)
            self.validity = self.parametric_rule.validity
        else:  # Validity depends on the result of application of the non-parametric rules
            first_matched = more_itertools.first(matched_negative_pairs, default=None)
            self.validity = RuleValidity.VALID if first_matched is None else RuleValidity.INVALID

        if self.validity == RuleValidity.VALID:
            rule_redundant = len(self.non_parametric_rules) > len(self.useful_rules)
            if rule_redundant:  # At least one rule can be removed without loss of coverage or validity
                self.validity = RuleValidity.REDUNDANT

    def compute_full_name(self) -> str:
        """Combine its name from names of the sub-rules."""
        subrule_names = ", ".join(rule.precomputed_name for rule in self.all_rules)
        return f"{self.get_rule_name()}({subrule_names})"

    def update_name_and_hash(self):
        """Update names and hashes of subrules and then own."""
        for subrule in self.all_rules:
            subrule.update_name_and_hash()

        super().update_name_and_hash()


@dataclasses.dataclass
class RuleWithStatistics:
    """A single rule and its coverage."""

    rule: RuleBase
    covered_positive_cases: CoverageValue


@dataclasses.dataclass
class RulesWithCoverage:
    """List of rules and they overall coverage if applied all together (connected by OR relation)."""

    rules: list[RuleWithStatistics]
    overall_coverage: CoverageValue


class RulesIterationMetrics:
    """List of metrics collected for each iteration of rule extraction procedure."""

    n_rules_category: dict[str, list[int]]
    time_spent: list[int]

    def __init__(self):
        self.n_rules_category = {k.name: [] for k in InteractionType}
        self.time_spent = []


class RulesMetrics:
    """List of metrics collected for the rule extraction procedure."""

    n_rules_process: dict[str, int]
    n_pairs_category: dict[str, int]
    time_spent_process: dict[str, int]

    def __init__(self):
        self.n_rules_process = {k.name: 0 for k in InteractionType}
        self.n_pairs_category = {k.name: 0 for k in PairsType}
        self.time_spent_process = {k.name: 0 for k in RuleExtractionStage}


class RuleExtractor:
    """Finds a set of rules covering the positive pairs in training examples while not covering any negative pair."""

    def __init__(
        self,
        records: Records,
        positive_pairs: RecordIdsPairSet,
        columns: list[ColumnName],
        logger: Logger,
        matching_id: MatchingId,
        correlation_id: CorrelationId = "",
        identity: Optional[Identity] = None,
        negative_pairs: Optional[RecordIdsPairSet] = None,
        max_columns_per_rule: int = DEFAULT_MAX_COLUMNS,
    ):
        self.records = records
        self.positive_pairs = positive_pairs
        self.columns = columns
        self.logger = logger
        self.matching_id = matching_id
        self.correlation_id = correlation_id
        self.identity = identity

        if negative_pairs is None:
            all_pairs = itertools.combinations(records.keys(), 2)
            self.negative_pairs = {pair for pair in all_pairs if pair not in positive_pairs}
        else:
            self.negative_pairs = negative_pairs

        self.max_columns = max_columns_per_rule
        self.evaluation: dict[RuleBase, RecordIdsPairSet] = {}  # Set of pairs matched by each rule

        # ------------------- Prometheus metrics -------------------
        self.metrics_iter = RulesIterationMetrics()
        self.metrics_total = RulesMetrics()

    def log_info(self, message: str, message_id: LogId, **kwargs):
        """Log info message about the rules extraction progress."""
        log_info(self.logger, message, message_id, self.matching_id, self.correlation_id, self.identity, **kwargs)

    def log_warning(self, message: str, message_id: LogId, **kwargs):
        """Log warning message about the rules extraction."""
        log_warning(self.logger, message, message_id, self.matching_id, self.correlation_id, self.identity, **kwargs)

    def extract_rules(self) -> RulesWithCoverage:
        """Extract best rules and ratio of positive examples they cover using a greedy algorithm + total coverage."""
        time_start = datetime_now()
        n_positive_pairs = len(self.positive_pairs)
        n_negative_pairs = len(self.negative_pairs)

        if n_positive_pairs == 0:
            self.log_warning(
                "There were 0 positive pairs so no rules could be extracted",
                LogId.rule_extraction_zero_pairs,
            )
            return RulesWithCoverage(rules=[], overall_coverage=1.0)

        time_previous = time_start
        rules_to_evaluate: list[RuleBase] = []
        for n_columns, rules in enumerate(self.generate_rules()):
            n_evaluated = len(rules)
            valid_rules = [rule for rule in rules if rule.validity == RuleValidity.VALID]
            n_valid = len(valid_rules)
            rules_to_evaluate += valid_rules

            n_redundant = sum(rule.validity == RuleValidity.REDUNDANT for rule in rules)
            n_invalid = sum(rule.validity == RuleValidity.INVALID for rule in rules)

            time_now = datetime_now()
            time_spent = time_now - time_previous

            self.metrics_iter.n_rules_category[InteractionType.GENERATED.name].append(n_evaluated)
            self.metrics_iter.n_rules_category[InteractionType.VALID.name].append(n_valid)
            self.metrics_iter.n_rules_category[InteractionType.INVALID.name].append(n_invalid)
            self.metrics_iter.n_rules_category[InteractionType.REDUNDANT.name].append(n_redundant)
            self.metrics_iter.time_spent.append(time_spent.seconds)
            self.log_info(
                "Generated {n_evaluated} {n_columns}-column rules: {n_valid} valid, {n_redundant} redundant, "
                "{n_invalid} invalid, computation took {time_spent}",
                LogId.rule_generation_columns,
                n_columns=n_columns,
                n_evaluated=n_evaluated,
                n_valid=n_valid,
                n_redundant=n_redundant,
                n_invalid=n_invalid,
                time_spent=time_spent,
            )
            time_previous = time_now

        time_after_generation = datetime_now()
        time_spent_generation = time_after_generation - time_start

        self.metrics_total.n_rules_process[InteractionType.GENERATED.name] = len(rules_to_evaluate)
        self.metrics_total.n_pairs_category[PairsType.NEGATIVE.name] = n_negative_pairs
        self.metrics_total.n_pairs_category[PairsType.POSITIVE.name] = n_positive_pairs
        self.metrics_total.time_spent_process[RuleExtractionStage.GENERATION.name] = (time_spent_generation).seconds
        self.log_info(
            "Generated in total {n_rules} valid rules based on {n_negative_pairs} negative pairs, computation took "
            "{time_spent}",
            LogId.rule_generation_total,
            n_rules=len(rules_to_evaluate),
            n_negative_pairs=n_negative_pairs,
            time_spent=time_spent_generation,
        )

        self.evaluate_rules_and_cache_results(rules_to_evaluate)

        time_after_evaluation = datetime_now()
        time_spent_evaluation = time_after_evaluation - time_after_generation

        self.metrics_total.n_rules_process[InteractionType.EVALUATED.name] = len(rules_to_evaluate)
        self.metrics_total.time_spent_process[RuleExtractionStage.EVALUATION.name] = (time_spent_evaluation).seconds
        self.log_info(
            "Evaluated {n_rules} rules, each on {n_positive_pairs} positive pairs, computation took {time_spent}",
            LogId.rule_evaluation,
            n_rules=len(rules_to_evaluate),
            n_positive_pairs=n_positive_pairs,
            time_spent=time_spent_evaluation,
        )

        selected_rules, remaining_pairs = self.select_best_rules(rules_to_evaluate)

        covered_pairs_in_total = n_positive_pairs - len(remaining_pairs)
        overall_coverage = covered_pairs_in_total / n_positive_pairs if n_positive_pairs > 0 else 1.0
        time_after_selection = datetime_now()
        time_spent_selection = time_after_selection - time_after_evaluation

        self.metrics_total.n_rules_process[InteractionType.EXTRACTED.name] = len(selected_rules)
        self.metrics_total.n_pairs_category[PairsType.COVERED.name] = covered_pairs_in_total
        self.metrics_total.time_spent_process[RuleExtractionStage.EXTRACTION.name] = (time_spent_selection).seconds
        self.log_info(
            "Extracted {n_rules} rules covering together {overall_coverage:0.2f}% ({n_covered_pairs} from "
            "{n_positive_pairs}) positive pairs and 0% (0 from {n_negative_pairs}) negative pairs: {rules}, "
            "computation took {time_spent}",
            LogId.rule_extraction,
            n_rules=len(selected_rules),
            overall_coverage=overall_coverage * 100,
            n_covered_pairs=covered_pairs_in_total,
            n_positive_pairs=n_positive_pairs,
            n_negative_pairs=n_negative_pairs,
            rules=selected_rules,
            time_spent=time_spent_selection,
        )

        return RulesWithCoverage(selected_rules, overall_coverage)

    def generate_rules(self) -> Iterator[Sequence[RuleBase]]:
        """
        Generate rules applicable to the columns which do not cover any negative pairs, separately by number of columns.

        Do not generate rules which cannot be better than already existing rules (i.e. has to be REDUNDANT).
        """
        always_match = AlwaysMatchRule()
        always_match.validate(self.records, self.negative_pairs)
        yield [always_match]

        # Otherwise no need to generate further rules, they would be REDUNDANT
        if always_match.validity != RuleValidity.VALID and self.max_columns > 0:
            nonparametric_rules = self.generate_single_column_nonparametric_rules()
            parametric_rules = self.generate_single_column_parametric_rules()
            one_column_rules = nonparametric_rules + parametric_rules  # type: ignore
            yield one_column_rules

            if self.max_columns > 1:
                two_column_non_parametric_rules = self.generate_two_column_nonparametric_rules(nonparametric_rules)
                two_column_parametric_rules = self.generate_two_column_parametric_rules(
                    parametric_rules, nonparametric_rules
                )
                two_column_rules = two_column_non_parametric_rules + two_column_parametric_rules
                yield two_column_rules

                n_column_rules = two_column_rules
                for _ in range(2, self.max_columns):
                    n_column_rules = self.generate_n_plus_one_column_rules(n_column_rules, nonparametric_rules)
                    yield n_column_rules

    def generate_single_column_nonparametric_rules(self) -> list[NonparametricRuleBase]:
        """Generate all possible single column nonparametric rules and validate them."""
        rules: list[NonparametricRuleBase] = []
        for column_name in self.columns:
            for template in SINGLE_COLUMN_NONPARAMETRIC_RULES:
                rule = template(column_name)
                rule.validate(self.records, self.negative_pairs)
                rules.append(rule)

        return rules

    def generate_single_column_parametric_rules(self) -> list[ParametricRuleBase]:
        """Generate all possible single column parametric rules with optimal parameters and validate them."""
        rules: list[ParametricRuleBase] = []
        for column_name in self.columns:
            for template in SINGLE_COLUMN_PARAMETRIC_RULES:
                rule = template(column_name)
                rule.set_best_params_and_validate(self.records, self.negative_pairs)
                rules.append(rule)

        return rules

    def generate_two_column_nonparametric_rules(
        self, nonparametric_rules: list[NonparametricRuleBase]
    ) -> list[CompositionRule]:
        """Generate all combinations of nonparametric multi column rules from single column rules.

        Generate only rules where each sub-rule is using different column and are not guaranteed to be redundant.
        """
        rules: list[CompositionRule] = []
        rule_pairs = itertools.combinations(nonparametric_rules, 2)  # Unique rule pairs without symmetries
        for rule1, rule2 in rule_pairs:
            if rule1.validity == RuleValidity.REDUNDANT or rule2.validity == RuleValidity.REDUNDANT:
                continue  # Both VALID and INVALID need to be considered

            if rule1.columns == rule2.columns:
                continue  # Composition rules with rules covering the same column are disallowed

            for template in MULTI_COLUMN_RULES:
                multi_column_rule = template([rule1.clone(), rule2.clone()], None)
                multi_column_rule.set_best_params_and_validate(self.records, self.negative_pairs)
                rules.append(multi_column_rule)

        return rules

    def generate_two_column_parametric_rules(
        self, parametric_rules: list[ParametricRuleBase], nonparametric_rules: list[NonparametricRuleBase]
    ) -> list[CompositionRule]:
        """Generate all combinations of parametric multi column rules from single column rules.

        Generate only rules where each sub-rule is using different column and are not guaranteed to be redundant.
        """
        rules: list[CompositionRule] = []
        for parametric_rule in parametric_rules:
            if parametric_rule.validity == RuleValidity.REDUNDANT:
                continue  # Both VALID and INVALID need to be considered
            for nonparametric_rule in nonparametric_rules:
                if nonparametric_rule.validity == RuleValidity.REDUNDANT:
                    continue  # Both VALID and INVALID need to be considered

                if parametric_rule.columns == nonparametric_rule.columns:
                    continue  # Composition rules with rules covering the same column are disallowed

                for template in MULTI_COLUMN_RULES:
                    multi_column_rule = template([nonparametric_rule.clone()], parametric_rule.clone())
                    multi_column_rule.set_best_params_and_validate(self.records, self.negative_pairs)
                    rules.append(multi_column_rule)

        return rules

    def generate_n_plus_one_column_rules(
        self, n_column_rules: list[CompositionRule], single_column_nonparametric_rules: list[NonparametricRuleBase]
    ) -> list[CompositionRule]:
        """Generate composition rules using n+1 columns based on a list of composition rules using n columns."""
        nonredundant_single_column_rules = [
            rule for rule in single_column_nonparametric_rules if rule.validity != RuleValidity.REDUNDANT
        ]

        rules: list[CompositionRule] = []
        for n_rule in n_column_rules:
            if n_rule.validity == RuleValidity.REDUNDANT:
                continue  # Any more complex rule would be also redundant

            used_columns_n_rule = n_rule.subrules_columns

            for single_rule in nonredundant_single_column_rules:
                used_column = more_itertools.one(single_rule.columns)
                if any(used_column <= column for column in used_columns_n_rule):
                    continue  # Column is identical or the resulting rule was/will be generated from another rule

                new_rule = n_rule.clone()
                single_rule_clone = single_rule.clone()
                new_rule.non_parametric_rules.append(single_rule_clone)

                new_rule.set_best_params_and_validate(self.records, self.negative_pairs)
                rules.append(new_rule)

        return rules

    def evaluate_rules_and_cache_results(self, rules: Iterable[RuleBase]):
        """Evaluate all rules on all positive pairs and store those which the rules match."""
        for rule in rules:
            rule_evaluation: RecordIdsPairSet = {
                (id1, id2) for id1, id2 in self.positive_pairs if rule.match(self.records[id1], self.records[id2])
            }
            self.evaluation[rule] = rule_evaluation

    def select_best_rules(self, all_rules: list[RuleBase]) -> tuple[list[RuleWithStatistics], RecordIdsPairSet]:
        """Return a list of best rules (covering most positive pairs, in a greedy way) and remaining uncovered pairs."""
        n_positive_pairs = len(self.positive_pairs)
        remaining_pairs = self.positive_pairs.copy()

        selected_rules = []
        while remaining_pairs:
            best_rule, rules_to_evaluate = self.pick_best_rule(all_rules, remaining_pairs)
            if best_rule is None:
                break
            covered_pairs = self.evaluation[best_rule].intersection(remaining_pairs)
            remaining_pairs -= covered_pairs
            covered_positive_pairs = len(covered_pairs) / n_positive_pairs
            result = RuleWithStatistics(best_rule, covered_positive_pairs)
            selected_rules.append(result)

        return selected_rules, remaining_pairs

    def pick_best_rule(
        self, candidate_rules: Iterable[RuleBase], positive_pairs: RecordIdsPairSet
    ) -> tuple[Optional[RuleBase], list[RuleBase]]:
        """Select the rule covering the most number of positive pairs."""
        scores: dict[RuleBase, int] = {}

        for rule in candidate_rules:
            score = len(self.evaluation[rule].intersection(positive_pairs))
            # Score is based on len which means always >= 0
            if score > 0:
                scores[rule] = score

        remaining_candidates = list(scores.keys())

        # Select rule with highest number of matches
        best_rule: Optional[RuleBase] = max(scores, key=scores.__getitem__, default=None)  # type: ignore
        if best_rule is not None:
            remaining_candidates.remove(best_rule)

        return best_rule, remaining_candidates


def apply_rules(
    records: Records,
    pairs: set[RecordIdsPair],
    rules: list[RuleBase],
    sequential: bool,
) -> tuple[list[float], list[RecordIdsPairSet]]:
    """Apply the given rules on given records after optional blocking process and calculate coverage."""
    matched_pairs: list[RecordIdsPairSet] = []
    coverage: list[float] = []

    n_all_pairs = len(pairs)

    for rule in rules:
        matched_pairs_per_rule = {(id1, id2) for id1, id2 in pairs if rule.match(records[id1], records[id2])}

        if sequential:
            pairs -= matched_pairs_per_rule

        matched_pairs.append(matched_pairs_per_rule)

        n_matched_rules = len(matched_pairs_per_rule)
        rule_coverage = n_matched_rules / n_all_pairs if n_matched_rules > 0 else 0  # To avoid division by zero
        coverage.append(rule_coverage)

    return coverage, matched_pairs
