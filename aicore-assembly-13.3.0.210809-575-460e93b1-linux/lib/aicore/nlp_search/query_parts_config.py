"""Loading, fetching and updating query parts configuration from file or from Configuration Service."""
from __future__ import annotations

import collections

from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from typing import Optional

    from aicore.common.config import Config
    from aicore.nlp_search.types import AQLString, EntityInstances


@dataclass
class QueryPartsDetails:
    """Class holding details of query parts configurations."""

    name: str
    value: str
    aqls: dict[str, AQLString]  # Mapping of entities to their AQLs

    __slots__ = ("name", "value", "aqls")

    @classmethod
    def negated_details(cls, part_name: str, part_value: str, aql_config: dict[str, AQLString]):
        """Create query parts details as a negation of a specific query part."""
        neg_part_name = "not " + part_name  # Negate query part name
        neg_aql_config = {entity_type: f"not ({aql})" for entity_type, aql in aql_config.items()}  # Negate AQLs
        return cls(neg_part_name, part_value, neg_aql_config)

    def get_AQL(self, entity_type: str) -> Optional[AQLString]:
        """Return AQL translation for particular entity name."""
        return self.aqls.get(entity_type) or self.aqls.get(QueryPartsConfig.APPLICABLE_EVERYWHERE)


class QueryPartsConfig:
    """Loader of query parts configuration from config service or file and informing subscribed listeners."""

    APPLICABLE_EVERYWHERE = "all"

    def __init__(self, config: Config):
        self.nodes_to_request: dict[str, str] = {}  # GraphQL metadata entities requested from MMM
        self.query_parts_details: dict[str, QueryPartsDetails] = {}

        self.process_config_reload(config)

    def process_config_reload(self, new_config: Config) -> bool:
        """Update query parts configuration parts from new configuration."""
        updated = False

        OPTION_UPDATERS = {
            "query_parts_config": self.update_query_part_data,
            "nodes_to_request": self.update_placeholder_request_values,
        }

        for option_name, update_function in OPTION_UPDATERS.items():
            if new_config.update_if_changed(option_name, update_function):
                updated = True

        return updated

    def update_query_part_data(self, query_parts_config: dict) -> None:
        """Parse query parts configuration."""
        query_parts_config = query_parts_config or {}
        query_part_data = {}

        for query_part_name, details_config in query_parts_config.items():
            args = [query_part_name.lower(), details_config["value"], details_config["AQL"]]
            query_part_data[query_part_name] = QueryPartsDetails(*args)

            if details_config.get("allow_negations"):
                negated_details = QueryPartsDetails.negated_details(*args)
                query_part_data[negated_details.name] = negated_details

        # Assign all dict at once to prevent need for thread locking, short-time un-sync is ok
        self.query_parts_details = query_part_data

    def update_placeholder_request_values(self, nodes_to_request_config: dict) -> None:
        """Parse placeholder configuration defining metadata entities to be queried by GraphQL from MMM."""
        nodes_to_request_config = nodes_to_request_config or {}

        placeholder_requests = {
            placeholder_def["placeholder_value"]: placeholder_def["entity_request"]
            for placeholder_def in nodes_to_request_config
        }

        # Assign all dict at once to prevent need for thread locking, short-time un-sync is ok
        self.nodes_to_request = placeholder_requests

    def applicable_query_part_types(self) -> tuple[EntityInstances, set[str]]:
        """Return mapping of entity names and query part types applicable for them."""
        applicable_on_entity = collections.defaultdict(set)
        for details in self.query_parts_details.values():
            name = details.name
            for entity in details.aqls.keys():
                applicable_on_entity[entity].add(name)

        applicable_everywhere = set(applicable_on_entity.get(self.APPLICABLE_EVERYWHERE, []))

        return applicable_on_entity, applicable_everywhere
