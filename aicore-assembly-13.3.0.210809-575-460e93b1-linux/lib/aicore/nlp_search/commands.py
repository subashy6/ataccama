"""De-/serialization and server-side handling of gRPC commands for NLP Search."""

from __future__ import annotations

from typing import TYPE_CHECKING

import aicore.nlp_search.proto.nlp_search_pb2 as search_proto

from aicore.common.command import Command
from aicore.nlp_search.translator import translate_to_aql


if TYPE_CHECKING:
    from typing import Optional

    from aicore.common.auth import Identity
    from aicore.common.types import CorrelationId
    from aicore.nlp_search.types import HistoricalQuery, QueryPart


class SearchCommand:
    """Class with common fields for search commands."""

    __slots__ = ("query_parts", "aql_filters", "search_type", "listing_node", "user_id", "query_id")

    def __init__(
        self,
        query_parts: list[QueryPart],
        aql_filters: list[str],
        search_type: search_proto.SearchType,
        listing_node: str,
        user_id: str,
        query_id: str,
    ):
        self.query_parts = query_parts  # Query defined as filter-like query parts consisting of query type and value
        self.aql_filters = aql_filters  # Optional AQL filters to limit the results
        self.search_type = search_type  # Global or entityListing search type
        self.listing_node = listing_node  # Searched node for entityListing or 'null' for global search
        self.user_id = user_id
        self.query_id = query_id

    def populate_search_request(self, search_request):
        """Fill SearchRequest proto message from commands fields."""
        for part_type, part_value in self.query_parts:
            request_part = search_request.query_parts.add()
            request_part.type = part_type
            request_part.value.value = part_value

        search_request.aql_filters.extend(self.aql_filters)

        search_request.search_type = self.search_type
        search_request.listing_node = self.listing_node
        search_request.user_id = self.user_id
        search_request.query_id = self.query_id


class TranslateQueryCommand(Command):
    """Translate query parts to AQL."""

    service = "ataccama.aicore.nlp_search.QueryTranslator"
    method = "TranslateQuery"
    request_class = search_proto.TranslateQueryRequest
    response_class = search_proto.TranslateQueryResponse
    __slots__ = ("search_command", "translated_query")

    def __init__(
        self,
        query_parts: list[QueryPart],
        aql_filters: list[str],
        search_type: search_proto.SearchType,
        listing_node: str,
        user_id: str,
        query_id: str,
    ):
        self.search_command = SearchCommand(query_parts, aql_filters, search_type, listing_node, user_id, query_id)
        # `null` is a valid empty AQL
        self.translated_query = None

    def __repr__(self):
        return (
            f"TranslateQueryCommand({self.search_command.user_id}:{self.search_command.listing_node}: "
            f"{self.search_command.query_parts})"
        )

    def serialize_for_server(self) -> search_proto.TranslateQueryRequest:
        """Create a gRPC request based on the command's state."""
        request = self.request_class()
        self.search_command.populate_search_request(request.search_request)
        return request

    def deserialize_from_server(self, response: search_proto.TranslateQueryResponse) -> None:
        """Set command's state based on protobuf response message."""
        self.translated_query = response.aql_query

    @classmethod
    def deserialize_from_client(cls, request: search_proto.TranslateQueryRequest) -> TranslateQueryCommand:
        """Create the command from given protobuf message."""
        query_parts = [(query_part.type, query_part.value.value) for query_part in request.search_request.query_parts]

        return cls(
            query_parts=query_parts,
            aql_filters=list(request.search_request.aql_filters),
            search_type=request.search_request.search_type,
            listing_node=request.search_request.listing_node,
            user_id=request.search_request.user_id,
            query_id=request.search_request.query_id,
        )

    def process(self, microservice, _correlation_id: CorrelationId, _identity: Optional[Identity] = None) -> None:
        """Set command's state based on results provided by given microservice."""
        self.translated_query = translate_to_aql(
            self.search_command.query_parts,
            self.search_command.listing_node,
            microservice.query_parts_config.query_parts_details,
        )

        # TODO: Save the query details into persistent storage  # noqa T101 ONE-5287

    def serialize_for_client(self) -> search_proto.TranslateQueryResponse:
        """Create a gRPC response based on the command's results (suggestions for each attribute)."""
        return self.response_class(aql_query=self.translated_query)


class AutocompleteQueryPartsCommand(Command):
    """Find most relevant autocomplete suggestions for query parts."""

    service = "ataccama.aicore.nlp_search.QueryAutocomplete"
    method = "AutocompleteQueryParts"
    request_class = search_proto.AutocompleteQueryPartsRequest
    response_class = search_proto.AutocompleteQueryPartsResponse
    __slots__ = (
        "search_command",
        "value",
        "caret_position",
        "suggestions",
        "num_suggestions",
        "num_history",
        "history_suggestions",
    )

    def __init__(
        self,
        query_parts: list[QueryPart],
        aql_filters: list[str],
        search_type: search_proto.SearchType,
        listing_node: str,
        user_id: str,
        query_id: str,
        value: str,
        caret_position: int,
        num_suggestions: int,
        num_history: int,
    ):
        self.search_command = SearchCommand(query_parts, aql_filters, search_type, listing_node, user_id, query_id)

        self.value = value  # String for query part auto-complete inserted by user up to now
        self.caret_position = caret_position  # Position of a cursor within a value to be auto-completed
        self.num_suggestions = num_suggestions  # Maximal number of query parts suggestions
        self.num_history = num_history  # Maximal number of historical queries suggestions

        self.suggestions: list[QueryPart] = []
        self.history_suggestions: list[HistoricalQuery] = []

    def __repr__(self):
        return (
            f"AutocompleteQueryPartsCommand({self.search_command.user_id}:{self.search_command.listing_node}:"
            f"{self.search_command.query_parts}: {self.value}/{self.caret_position})"
        )

    def serialize_for_server(self) -> search_proto.AutocompleteQueryPartsRequest:
        """Create a gRPC request based on the command's state."""
        request = self.request_class()
        self.search_command.populate_search_request(request.search_request)
        request.value = self.value
        request.caret_position = self.caret_position
        request.num_suggestions = self.num_suggestions
        request.num_history = self.num_history
        return request

    def deserialize_from_server(self, response: search_proto.AutocompleteQueryPartsResponse) -> None:
        """Set command's state based on protobuf response message."""
        self.suggestions = [
            (part_suggestion.type, part_suggestion.value.value) for part_suggestion in response.suggestions
        ]

        self.history_suggestions = []
        for history in response.history_suggestions:
            self.history_suggestions.append(
                tuple((history_query.type, history_query.value.value) for history_query in history.query_parts)
            )

    @classmethod
    def deserialize_from_client(
        cls, request: search_proto.AutocompleteQueryPartsRequest
    ) -> AutocompleteQueryPartsCommand:
        """Create the command from given protobuf message."""
        query_parts = [(query_part.type, query_part.value.value) for query_part in request.search_request.query_parts]

        return cls(
            query_parts=query_parts,
            aql_filters=list(request.search_request.aql_filters),
            search_type=request.search_request.search_type,
            listing_node=request.search_request.listing_node,
            user_id=request.search_request.user_id,
            query_id=request.search_request.query_id,
            value=request.value,
            caret_position=request.caret_position,
            num_suggestions=request.num_suggestions,
            num_history=request.num_history,
        )

    def process(self, microservice, _correlation_id: CorrelationId, _identity: Optional[Identity] = None) -> None:
        """Set command's state based on results provided by given microservice."""
        self.suggestions = microservice.autocomplete.suggest_part_types(
            self.search_command.listing_node,
            self.value,
            self.num_suggestions,
        )
        self.history_suggestions = microservice.autocomplete_history.suggest_history(
            self.search_command.query_parts,
            self.search_command.search_type,
            self.search_command.listing_node,
            self.search_command.user_id,
            self.search_command.query_id,
            self.value,
            self.caret_position,
            self.num_history,
        )

    def serialize_for_client(self) -> search_proto.AutocompleteQueryPartsResponse:
        """Create a gRPC response based on the command's results (suggestions for each attribute)."""
        response = self.response_class()
        for suggested_filter_type, suggested_filter_value in self.suggestions:
            proto_suggestion = response.suggestions.add()
            proto_suggestion.type = suggested_filter_type
            proto_suggestion.value.value = suggested_filter_value

        for history in self.history_suggestions:
            proto_history = response.history_suggestions.add()
            for suggested_part_type, suggested_part_value in history:
                suggested_part = proto_history.query_parts.add()
                suggested_part.type = suggested_part_type
                suggested_part.value.value = suggested_part_value

        return response


class AutocompleteValuesCommand(Command):
    """Find most relevant autocomplete suggestions for filter values."""

    service = "ataccama.aicore.nlp_search.QueryAutocomplete"
    method = "AutocompleteValues"
    request_class = search_proto.AutocompleteValuesRequest
    response_class = search_proto.AutocompleteValuesResponse
    __slots__ = ("search_command", "part_index", "caret_position", "num_suggestions", "suggestions")

    def __init__(
        self,
        query_parts: list[QueryPart],
        aql_filters: list[str],
        search_type: search_proto.SearchType,
        listing_node: str,
        user_id: str,
        query_id: str,
        part_index: int,
        caret_position: int,
        num_suggestions: int,
    ):
        self.search_command = SearchCommand(query_parts, aql_filters, search_type, listing_node, user_id, query_id)
        self.part_index = part_index
        self.caret_position = caret_position  # Position of a cursor within a value to be auto-completed
        self.num_suggestions = num_suggestions  # Maximal number of value suggestions

        self.suggestions: list[str] = []

    def __repr__(self):
        return (
            f"AutocompleteValuesCommand({self.search_command.user_id}:{self.search_command.listing_node}: "
            f"{self.search_command.query_parts}: {self.part_index}/{self.caret_position})"
        )

    def serialize_for_server(self) -> search_proto.AutocompleteValuesRequest:
        """Create a gRPC request based on the command's state."""
        request = self.request_class()
        self.search_command.populate_search_request(request.search_request)
        request.part_index = self.part_index
        request.caret_position = self.caret_position
        request.num_suggestions = self.num_suggestions
        return request

    def deserialize_from_server(self, response: search_proto.AutocompleteValuesResponse) -> None:
        """Set command's state based on protobuf response message."""
        self.suggestions = [value_suggestion.value for value_suggestion in response.suggestions]

    @classmethod
    def deserialize_from_client(cls, request: search_proto.AutocompleteValuesRequest) -> AutocompleteValuesCommand:
        """Create the command from given protobuf message."""
        query_parts = [(query_part.type, query_part.value.value) for query_part in request.search_request.query_parts]

        return cls(
            query_parts=query_parts,
            aql_filters=list(request.search_request.aql_filters),
            search_type=request.search_request.search_type,
            listing_node=request.search_request.listing_node,
            user_id=request.search_request.user_id,
            query_id=request.search_request.query_id,
            part_index=request.part_index,
            caret_position=request.caret_position,
            num_suggestions=request.num_suggestions,
        )

    def process(self, microservice, correlation_id: CorrelationId, _identity: Optional[Identity] = None) -> None:
        """Set command's state based on results provided by given microservice."""
        self.suggestions = microservice.autocomplete.suggest_part_values(
            self.search_command.query_parts, self.part_index, self.caret_position, self.num_suggestions, correlation_id
        )

    def serialize_for_client(self) -> search_proto.AutocompleteValuesResponse:
        """Create a gRPC response based on the command's results (suggestions for each attribute)."""
        response = self.response_class()
        for suggested_value in self.suggestions:
            proto_suggestion = response.suggestions.add()
            proto_suggestion.value = suggested_value

        return response


class SpellcheckCommand(Command):
    """Check and correct spelling of AQL keywords, entity names and searched values."""

    service = "ataccama.aicore.nlp_search.AqlQuerySpellchecker"
    method = "SpellcheckAqlQuery"
    request_class = search_proto.SpellcheckAqlQueryRequest
    response_class = search_proto.SpellcheckAqlQueryResponse
    __slots__ = ("aql_query", "search_type", "listing_node", "user_id", "query_id", "spellchecked_query")

    def __init__(
        self, aql_query: str, search_type: search_proto.SearchType, listing_node: str, user_id: str, query_id: str
    ):
        self.aql_query = aql_query  # AQL query string to be spell-checked
        self.search_type = search_type  # Global or entityListing search type
        self.listing_node = listing_node  # Searched node for entityListing or 'null' for global search
        self.user_id = user_id
        self.query_id = query_id
        self.spellchecked_query = ""

    def __repr__(self):
        return f"SpellcheckCommand({self.user_id}:{self.listing_node}:{self.aql_query})"

    def serialize_for_server(self) -> search_proto.SpellcheckAqlQueryRequest:
        """Create a gRPC request based on the command's state."""
        request = self.request_class()
        request.aql_query = self.aql_query
        request.search_type = self.search_type
        request.listing_node = self.listing_node
        request.user_id = self.user_id
        request.query_id = self.query_id
        return request

    def deserialize_from_server(self, response: search_proto.SpellcheckAqlQueryResponse) -> None:
        """Set command's state based on protobuf response message."""
        self.spellchecked_query = response.aql_query

    @classmethod
    def deserialize_from_client(cls, request: search_proto.SpellcheckAqlQueryRequest) -> SpellcheckCommand:
        """Create the command from given protobuf message."""
        return cls(
            aql_query=request.aql_query,
            search_type=request.search_type,
            listing_node=request.listing_node,
            user_id=request.user_id,
            query_id=request.query_id,
        )

    def process(self, microservice, _correlation_id: CorrelationId, _identity: Optional[Identity] = None) -> None:
        """Set command's state based on results provided by given microservice."""
        self.spellchecked_query = microservice.spellchecker.fix_typos(self.aql_query, self.user_id, self.query_id)

    def serialize_for_client(self) -> search_proto.SpellcheckAqlQueryResponse:
        """Create a gRPC response based on the command's results (suggestions for each attribute)."""
        return self.response_class(aql_query=self.spellchecked_query)
