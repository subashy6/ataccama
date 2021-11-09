"""Serialization/ deserialization of data from/ to proto messages."""
from __future__ import annotations

from typing import TYPE_CHECKING

import dedupe.predicates as dedupe_predicates
import google.protobuf.timestamp_pb2
import pandas

from aicore.ai_matching.enums import MdcColumnType, ParsingError, Proposal, Status
from aicore.ai_matching.proto import ai_matching_pb2 as matching_proto
from aicore.ai_matching.rules_extraction import CompositionRule, RuleBase
from aicore.common.exceptions import AICoreException
from aicore.common.utils import datetime_fromtimestamp


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator
    from typing import Any

    from aicore.ai_matching.types import BlockingRule, MdcColumn, MdcColumns, RecordData

LONG_BYTE: int = 254  # b'0xfe'
NULL_BYTE: int = 255  # b'0xff'
INVERSE_BYTE: int = 128  # b'0x80'
EMPTY_STRING_BYTE: int = 0  # b'0x00'


def _handle_long(byte_array: Iterator[int], lead_byte: int) -> int:
    id_ = lead_byte & 15
    size = 8 if lead_byte == 128 else (lead_byte & 112) >> 4

    while size > 0:
        id_ = (id_ << 8) | next(byte_array)
        size -= 1

    return id_ if size <= INVERSE_BYTE else id_ * (-1)


def _handle_big_int(byte_array: Iterator[int], lead_byte: int) -> int:
    if lead_byte == LONG_BYTE:
        return _handle_long(byte_array, next(byte_array))

    return int.from_bytes([next(byte_array) for _ in range(lead_byte)], "big")


def _handle_bool(_byte_array: Iterator[int], lead_byte: int) -> bool:
    return True if lead_byte != 0 else False


def _handle_string(byte_array: Iterator[int], lead_byte: int) -> str:
    if lead_byte == LONG_BYTE:
        lead_byte = _handle_big_int(byte_array, lead_byte)

    return _parse_string(byte_array, lead_byte)


def _parse_string(byte_array: Iterator[int], lead_byte: int) -> str:
    return "".join([chr(next(byte_array)) for _ in range(lead_byte)])


# Mapping of types to the methods used for their processing
type_processing_map: dict[MdcColumnType, Callable[[Iterator, int], Any]] = {
    MdcColumnType.STRING: _handle_string,
    MdcColumnType.INTEGER: _handle_long,
    MdcColumnType.DAY: _handle_long,
    MdcColumnType.BOOLEAN: _handle_bool,
    MdcColumnType.LONG: _handle_big_int,  # Due to MDC types
    MdcColumnType.DATETIME: _handle_long,
    MdcColumnType.ID_LONG_TYPE: _handle_long,  # Because ID is still proper LONG in MDC
    # FLOAT (de)serialization is not implemented on MDC side
}

# Python types the MDC types are converted to during deserialization
convert_types = {
    MdcColumnType.STRING: str,
    MdcColumnType.INTEGER: str,
    MdcColumnType.BOOLEAN: str,
    MdcColumnType.LONG: str,
    MdcColumnType.DAY: str,
    MdcColumnType.DATETIME: str,
    MdcColumnType.FLOAT: str,
    MdcColumnType.ID_LONG_TYPE: int,
}


class ByteArrayTooShortError(AICoreException):
    """Internal error caused by received array being smaller than expected."""

    def __init__(self, required_size: int):
        super().__init__(f"Size of provided byte array was smaller than the expected {required_size}")


def deserialize(
    columns: MdcColumns,
    response_stream: Iterable[matching_proto.ProvideDataResponse],
    date_to_str: bool = True,
) -> Iterator[RecordData]:
    """Deserialize MDC response."""
    columns_with_id: MdcColumns = [(MdcColumnType.ID_LONG_TYPE, "id")] + list(columns)

    for data in response_stream:
        for row in data.data:
            byte_stream = iter(row.data)
            parsed_row = parse_values(columns_with_id, byte_stream)

            converted_values = {
                column_name: convert_type(parsed_row[column_name], column_type, date_to_str)
                for (column_type, column_name) in columns_with_id
            }
            yield converted_values


def convert_type(column_value: Any, column_type: MdcColumnType, date_to_str: bool) -> Any:
    """Convert parsed values to required column types, so far only timestamps are needed."""
    if column_value == "" or column_value is None:  # Both empty and NULL values are handled the same
        return None

    if date_to_str and column_type in [MdcColumnType.DAY, MdcColumnType.DATETIME]:
        date = datetime_fromtimestamp(column_value / 1e3)  # The timestamp is in milliseconds
        return date.strftime("%Y-%m-%d %H:%M")

    return convert_types[column_type](column_value)


def parse_values(columns: MdcColumns, byte_stream: Iterator[int]) -> dict[str, Callable[[Iterator, int], Any]]:
    """Parse and deserialize values from the gRPC response bytes."""
    value_dict: dict[str, Any] = {}
    try:
        for (column_type, column_name) in columns:
            size = next(byte_stream)
            if size in [NULL_BYTE, EMPTY_STRING_BYTE]:
                value_dict[column_name] = None
            else:
                value_dict[column_name] = type_processing_map[column_type](byte_stream, size)
    except StopIteration:
        raise ParsingError(f"Size of provided byte array was smaller than the expected, required size: {len(columns)}")

    return value_dict


def convert_dates_to_str(data_frame: pandas.DataFrame, columns: MdcColumns) -> pandas.DataFrame:
    """Convert datetime columns to string."""
    date_columns = [
        column_name
        for (column_type, column_name) in columns
        if column_type in [MdcColumnType.DAY, MdcColumnType.DATETIME]
    ]
    for col in date_columns:
        data_frame[col] = data_frame[col].dt.strftime("%Y-%m-%d %H:%M")
        data_frame[col] = data_frame[col].where(pandas.notnull(data_frame[col]), None)

    return data_frame


def status_to_proto(status: Status) -> matching_proto.StatusMessage:
    """Convert status to proto message."""
    matching_id = matching_proto.MatchingId(
        entity_name=status.matching_id.entity_name, layer_name=status.matching_id.layer_name
    )
    timestamp = google.protobuf.timestamp_pb2.Timestamp()
    timestamp.FromDatetime(status.model_update_time)
    error_message = matching_proto.ErrorMessage()
    if status.error is not None:
        error_message.message = status.error.message
        error_message.phase = status.error.phase.value  # type: ignore

    return matching_proto.StatusMessage(
        matching_id=matching_id,
        phase=status.phase.value,  # type: ignore
        progress=status.progress,
        model_update_time=timestamp,
        match_training_pairs_count=status.match_training_pairs_count,
        distinct_training_pairs_count=status.distinct_training_pairs_count,
        used_columns_count=status.used_columns_count,
        clustering_state=status.clustering_state.value,  # type: ignore
        records_matching_status=matching_proto.RecordsMatchingStatus(
            state=status.records_matching_status.state.value,  # type: ignore
            merge_proposals_count=status.records_matching_status.merge_proposals_count,
            split_proposals_count=status.records_matching_status.split_proposals_count,
            cached_proposals_count=status.records_matching_status.cached_proposals_count,
            confidence_threshold=status.records_matching_status.confidence_threshold,
        ),
        rules_extraction_status=matching_proto.RulesExtractionStatus(
            state=status.rules_extraction_status.state.value,  # type: ignore
            rules_extracted_count=status.rules_extraction_status.rules_extracted_count,
            min_match_confidence=status.rules_extraction_status.min_match_confidence,
            min_distinct_confidence=status.rules_extraction_status.min_distinct_confidence,
        ),
        error=error_message,
        model_quality=status.model_quality,
    )


def proposal_to_proto(proposal: Proposal) -> matching_proto.MatchingProposal:
    """Create proposal proto message from proposal."""
    proto_proposal = matching_proto.MatchingProposal()
    proto_proposal.pair.id1 = proposal.id1
    proto_proposal.pair.id2 = proposal.id2
    proto_proposal.decision = proposal.decision.value  # type: ignore
    proto_proposal.confidence = proposal.confidence
    proto_proposal.key_columns.extend(proposal.key_columns)
    for column_name, score in proposal.column_scores.items():
        proto_column_score = proto_proposal.column_scores.add()
        proto_column_score.column_name = column_name
        proto_column_score.score = score

    return proto_proposal


def rule_to_proto(rule: RuleBase, all_columns: list[MdcColumn]) -> matching_proto.Rule:
    """Create rule suggestion proto message from a single rule. Do not fill the statistics (coverage)."""
    proto_rule = matching_proto.Rule()
    proto_rule.function = rule.get_rule_name()

    for column_type, column_name in all_columns:
        if column_name in rule.columns:
            serialize_single_column_rule(column_type.value, column_name, proto_rule)

    for name, value in rule.get_params().items():
        serialize_single_rule_param(name, str(value), proto_rule)

    if isinstance(rule, CompositionRule):
        sub_rules_proto = [rule_to_proto(sub_rule, all_columns) for sub_rule in rule.all_rules]
        proto_rule.sub_rules.extend(sub_rules_proto)

    return proto_rule


def serialize_single_rule_param(param_name: str, param_value: str, proto_rule: matching_proto.Rule):
    """Convert a single rule param into a proto message and add it to a rule proto message."""
    proto_rule_param = proto_rule.params.add()
    proto_rule_param.name = param_name
    proto_rule_param.value = param_value


def blocking_rule_to_proto(blocking_rule: BlockingRule) -> matching_proto.BlockingRule:
    """Create blocking rule proto message from a single blocking rule (predicate)."""
    proto_blocking_rule = matching_proto.BlockingRule()

    if isinstance(blocking_rule, dedupe_predicates.StringPredicate):
        serialize_simple_predicate(blocking_rule, proto_blocking_rule.rule)
    else:  # It is a dedupe.predicates.CompoundPredicate
        proto_blocking_rule.rule.function = "CompoundPredicate"
        for predicate in blocking_rule:
            simple_rule = proto_blocking_rule.rule.sub_rules.add()
            serialize_simple_predicate(predicate, simple_rule)

    return proto_blocking_rule


def serialize_simple_predicate(blocking_rule: dedupe_predicates.StringPredicate, proto_rule: matching_proto.Rule):
    """Convert a single predicate type blocking rule into a proto message and add it to the rule proto message."""
    proto_rule.function = blocking_rule.func.__name__

    # All columns are treated as strings at the moment.
    serialize_single_column_rule(MdcColumnType.STRING.value, blocking_rule.field, proto_rule)


def serialize_single_column_rule(column_type: int, column_name: str, proto_rule: matching_proto.Rule):
    """Convert a single column into its corresponding proto message equivalent and add it to the rule proto message."""
    proto_rule_column = proto_rule.columns.add()
    proto_rule_column.type = column_type  # type: ignore
    proto_rule_column.name = column_name
