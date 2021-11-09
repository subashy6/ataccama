"""Provide suggestions for query autocomplete."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aicore.nlp_search.registry import LogId
from aicore.nlp_search.vocabularies import MetaDataVocabulary


if TYPE_CHECKING:
    from aicore.common.config import Config
    from aicore.common.logging import Logger
    from aicore.common.types import CorrelationId
    from aicore.nlp_search.types import HistoricalQuery, QueryPart


class Autocomplete:
    """Provide suggestions of query continuation."""

    def __init__(self, config: Config, metadata_vocabulary: MetaDataVocabulary, logger: Logger):
        self.config = config
        self.metadata_vocabulary = metadata_vocabulary  # Vocabulary and directed word graphs for autocomplete
        self.logger = logger

    def suggest_part_types(
        self,
        listing_node: str,
        value_to_complete: str,
        num_suggestions: int,
    ) -> list[QueryPart]:
        """Provide suggestions of filter-like query parts given inputted string value."""
        graph_specifier = self.metadata_vocabulary.applicable_for_entity_key(listing_node, insert=False)
        autocomplete_graph = self.metadata_vocabulary.autocomplete_word_graphs[graph_specifier]

        autocomplete_suggestions = autocomplete_graph.search(value_to_complete, max_cost=0, size=num_suggestions)

        query_part_suggestions = [(part_type, "") for part_type in autocomplete_suggestions]

        # If num_suggestions not exceeded, also check DWGs of query part values autocomplete
        # TODO: implement the actual logic  # noqa T101 ONE-16161

        return query_part_suggestions

    def suggest_part_values(
        self,
        query_parts: list[QueryPart],
        part_index: int,
        caret_position: int,
        num_suggestions: int,
        correlation_id: CorrelationId,
    ) -> list[str]:
        """Provide suggestions of query part values given already provided query part type and initial letters."""
        valid_index = min(part_index, len(query_parts) - 1)
        query_part_type, query_part_value = query_parts[valid_index]
        value_to_complete = query_part_value[:caret_position]

        try:
            query_part_details = self.metadata_vocabulary.query_parts_config.query_parts_details[query_part_type]
            autocomplete_graph = self.metadata_vocabulary.autocomplete_word_graphs[query_part_details.value]
        except KeyError:
            self.logger.warning(
                "Requested value suggestions for unknown query part type {part_type!r}",
                part_type=query_part_type,
                correlation_id=correlation_id,
                message_id=LogId.autocomplete_value_unknown,
            )
            return []  # Return no suggestions for unknown entity types, e.g. 'anything'

        autocomplete_suggestions = autocomplete_graph.search(value_to_complete, max_cost=0, size=num_suggestions)
        return autocomplete_suggestions


class AutocompleteHistory:
    """Provide suggestions based on query history."""

    def __init__(self, config):
        self.config = config

    def suggest_history(
        self,
        _query_parts: list[QueryPart],
        _search_type: str,
        _listing_node: str,
        _user_id: str,
        _query_id: str,
        _value: str,
        _caret_position: int,
        _num_history: int,
    ) -> list[HistoricalQuery]:
        """Provide suggestions of whole filter sets from history given already inputted filters."""
        # TODO: implement the actual logic - not now  # noqa T101 ONE-5287
        return []
