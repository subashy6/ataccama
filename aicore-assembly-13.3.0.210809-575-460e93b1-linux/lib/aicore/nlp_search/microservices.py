"""Microservices (processes or Docker containers) provided by NLP Search."""

from __future__ import annotations

import string

from aicore.common.microservice import Microservice
from aicore.common.utils import random_correlation_id
from aicore.nlp_search import AUTOCOMPLETE, SPELLCHECKER, TRANSLATOR, commands
from aicore.nlp_search.autocomplete import Autocomplete, AutocompleteHistory
from aicore.nlp_search.query_parts_config import QueryPartsConfig
from aicore.nlp_search.spellchecker import Spellchecker
from aicore.nlp_search.vocabularies import AQLKeywordsVocabulary, MetaDataVocabulary


METAMETADATA_QUERY = """
    {
        _modelMetadata {
            entities(entityName: "metadata") {
                entityName
                properties {
                    name
                }
            }
        }
    }
"""


NAMES_QUERY_TEMPLATE = string.Template(
    """
    {
        $entity_name(versionSelector: {
            draftVersion: true
        }) {
            edges {
                node {
                    draftVersion {
                        $fields
                    }
                }
            }
        }
    }
"""
)


ENTITY_NAME_TO_FIELDS = {"terms": "name,abbreviation,synonym", "persons": "firstName,lastName,username"}


class TranslatorService(Microservice):
    """Translates query parts into AQL."""

    def __init__(self, config):
        super().__init__("translator", config)

        self.query_parts_config = QueryPartsConfig(self.config)
        self.grpc_server(commands=[commands.TranslateQueryCommand])
        self.wsgi = self.wsgi_server()

    def process_config_reload(self, new_config):
        """Process template's configuration updates."""
        super().process_config_reload(new_config)

        self.query_parts_config.process_config_reload(new_config)


class AutocompleteService(Microservice):
    """Suggests possible query parts that can be used for query autocomplete."""

    def __init__(self, config):
        super().__init__("autocomplete", config, period=config.request_metadata_period_s)

        self.query_parts_config = QueryPartsConfig(self.config)
        self.metadata_vocabulary = MetaDataVocabulary(self.query_parts_config)
        self.autocomplete = Autocomplete(self.config, self.metadata_vocabulary, self.logger)
        self.autocomplete_history = AutocompleteHistory(self.config)

        self.mmm_client = self.graphql_client("mmm")
        self.grpc_server(commands=[commands.AutocompleteQueryPartsCommand, commands.AutocompleteValuesCommand])
        self.wsgi = self.wsgi_server()
        self.add_external_dependency("mmm")

    def on_start(self):
        """Request metadata entity names from MMM."""
        self.metadata_vocabulary.update_query_parts(self.query_parts_config)

        entity_names_by_type = {}
        for entity_type, cmd_name in self.query_parts_config.nodes_to_request.items():
            entity_names = self.get_entity_names(cmd_name)
            entity_names_by_type[entity_type] = set(entity_names)

        self.metadata_vocabulary.update_entities(entity_names_by_type)

    def process_config_reload(self, new_config):
        """Process template's configuration updates."""
        super().process_config_reload(new_config)

        if self.query_parts_config.process_config_reload(new_config):
            self.metadata_vocabulary.update_query_parts(self.query_parts_config)

    def process_once_per_period(self) -> None:
        """Periodically ask for the metadata entity names updates."""
        # TODO temporary fix, request when Metadata changed messages from MMM  # noqa T100,T101 AI-698
        entity_names_by_type = {}
        for entity_type, cmd_name in self.query_parts_config.nodes_to_request.items():
            entity_names = self.get_entity_names(cmd_name)
            entity_names_by_type[entity_type] = set(entity_names)

        self.metadata_vocabulary.update_entities(entity_names_by_type)

    def get_entity_names(self, entity_name):
        """Get names of entities from MMM."""
        fields = ENTITY_NAME_TO_FIELDS.get(entity_name, "name")
        entity_names_string = NAMES_QUERY_TEMPLATE.substitute(entity_name=entity_name, fields=fields)
        response = self.mmm_client.send(entity_names_string, random_correlation_id())

        entity_names = []
        for entity in response[entity_name]["edges"]:
            for field_value in fields.split(","):
                name = entity["node"]["draftVersion"][field_value]
                if name:
                    entity_names.append(name)

        return entity_names


class SpellcheckerService(Microservice):
    """Checks for typos in AQL query string and provides keyword fixes and value enhancements."""

    def __init__(self, config):
        super().__init__("spellchecker", config, period=config.request_metadata_period_s)

        self.aql_vocabulary = AQLKeywordsVocabulary(self.config.vocabularies_folder, self.config.languages, self.logger)
        self.spellchecker = Spellchecker(self.config, self.aql_vocabulary)

        self.mmm_client = self.graphql_client("mmm")
        self.grpc_server(commands=[commands.SpellcheckCommand])
        self.wsgi = self.wsgi_server()
        self.add_external_dependency("mmm")

    def on_start(self):
        """Request MMD nodes from MMM."""
        mmd_node_names = self.get_metametadata_names()
        self.aql_vocabulary.update_aql_vocabulary(mmd_node_names)

    def process_once_per_period(self) -> None:
        """Periodically ask for MMD nodes updates."""
        # TODO temporary fix, request when Metametadata or mmd version changed messages from MMM  # noqa T100,T101 AI-698
        mmd_node_names = self.get_metametadata_names()
        self.aql_vocabulary.update_aql_vocabulary(mmd_node_names)

    def get_metametadata_names(self) -> set[str]:
        """Get names of meta-metadata entities from MMM."""
        mmd_names = set()
        mmd_json = self.mmm_client.send(METAMETADATA_QUERY, random_correlation_id())
        mmd_entities = mmd_json["_modelMetadata"]["entities"]

        for entity in mmd_entities:
            mmd_names.add(entity["entityName"])
            for mmd_property in entity["properties"]:
                mmd_names.add(mmd_property["name"])

        return mmd_names


MICROSERVICES = {
    TRANSLATOR: TranslatorService,
    AUTOCOMPLETE: AutocompleteService,
    SPELLCHECKER: SpellcheckerService,
}
