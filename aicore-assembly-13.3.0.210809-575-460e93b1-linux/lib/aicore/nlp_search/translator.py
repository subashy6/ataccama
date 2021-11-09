"""Translating query parts to their AQL representation."""

from __future__ import annotations

import itertools
import operator
import string

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from aicore.nlp_search.query_parts_config import QueryPartsDetails
    from aicore.nlp_search.types import AQLString, QueryPart


def translate_to_aql(
    query_parts: list[QueryPart], entity_type: str, query_parts_details: dict[str, QueryPartsDetails]
) -> AQLString:
    """Translate search query into AQL string for given entity type."""
    sorted_parts = sorted(query_parts, key=operator.itemgetter(0))  # Parts arrive not sorted from MMM
    aql_query = []

    part_types_groups = itertools.groupby(sorted_parts, operator.itemgetter(0))  # Group by query part type

    for part_type, group in part_types_groups:
        or_values = " or like ".join([f"{value!r}" for _, value in group])  # Combine same type values by OR

        part_details = query_parts_details.get(part_type.lower())
        if not part_details:
            continue  # skip unknown part types

        aql_template = part_details.get_AQL(entity_type)
        if aql_template:
            substitution = {part_details.value: or_values}
            aql_query.append(string.Template(aql_template).safe_substitute(substitution))  # Fill template

    filled_aql = ") and (".join(aql_query)  # Combine groups with AND relation

    # () is not a valid AQL - `null` or whitespace is
    return f"({filled_aql})" if filled_aql else None
