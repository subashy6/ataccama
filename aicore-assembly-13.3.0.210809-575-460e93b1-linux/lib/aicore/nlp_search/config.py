"""Microservice configuration."""

from __future__ import annotations

import json

from aicore.common.config import ConfigOptionsBuilder, connection_options, server_options


def one_line(line):
    """Convert string having multiple lines to one having only one line."""
    return line.replace("  ", "").replace("\n", "")


CONFIG_OPTIONS = (
    ConfigOptionsBuilder()
    .common_options("microservice_commons", "mmm")
    .start_section("NLP search", 120)
    .option(
        "vocabularies_folder",
        "ataccama.one.aicore.nlp-search.spellchecker.vocabularies-folder",
        str,
        "Points to the location of vocabularies used for AQL error checking.",
        default_value="${ataccama.path.etc}/data/nlp_search",
    )
    .option(
        "languages",
        "ataccama.one.aicore.nlp-search.spellchecker.languages",
        list,
        """A list of languages used for AQL error checking. For every stated language, a file named
        `<language_name>_word_frequencies.txt` is searched for in the vocabularies folder.""",
        default_value=json.dumps(["english"]),
    )
    .option(
        "request_metadata_period_s",
        "ataccama.one.aicore.nlp-search.request-metadata-period-s",
        int,
        """Defines how often requests are sent to MMM to retrieve metadata entity names, such as names of terms and
        sources, which are used for autocomplete.""",
        default_value=60,
    )
    .option(
        "nodes_to_request",
        "ataccama.one.aicore.nlp-search.nodes-to-request",
        list,
        "A JSON definition of the relation between search template placeholders and entity types.",
        default_value=json.dumps(
            [
                {"placeholder_value": "source", "entity_request": "sources"},
                {"placeholder_value": "term", "entity_request": "terms"},
            ],
            indent=4,
        ),
        refreshable=True,
    )
    .option(
        "query_parts_config",
        "ataccama.one.aicore.nlp-search.query-parts-config",
        dict,
        "A JSON definition of search suggestions templates.",
        default_value=json.dumps(
            {
                "with term": {
                    "value": "term",
                    "AQL": {
                        "catalogItem": one_line(
                            """(
                                termInstances.some(
                                    target{name like ${term} OR synonym like ${term} OR abbreviation like ${term}}
                                )
                                 OR attributes.some(
                                    termInstances.some(
                                        target{name like ${term} OR synonym like ${term} OR abbreviation like ${term}}
                                    )
                                )
                            )"""
                        ),
                        "source": one_line(
                            """
                                locations.some(
                                    catalogItems.some(
                                        termInstances.some(
                                            target{name like ${term}}
                                        )
                                    )
                                )
                                 OR locations.some(
                                    locations.some(
                                        catalogItems.some(
                                            termInstances.some(
                                                target{name like ${term}}
                                            )
                                        )
                                    )
                                )
                            """
                        ),
                    },
                    "allow_negations": True,
                },
                "from source": {
                    "value": "source",
                    "AQL": {
                        "catalogItem": one_line(
                            """(
                                $parent.$parent.name like ${source}
                                 OR $parent.$parent.$parent.name like ${source}
                                 OR $parent.$parent.$parent.$parent.name like ${source}
                            )"""
                        )
                    },
                    "allow_negations": True,
                },
                "with attribute": {
                    "value": "attribute",
                    "AQL": {"catalogItem": "attributes.some(name like ${attribute})"},
                    "allow_negations": True,
                },
                "fulltext": {"value": "anything", "AQL": {"all": "$fulltext like ${anything}"}},
            },
            indent=4,
        ),
        refreshable=True,
    )
    .create_options(
        lambda builder: server_options(
            builder, module_name="NLP Search", microservice_name="Translator", grpc_port=8546, http_port=8046
        )
    )
    # gRPC connection used only in tests
    .create_options(
        lambda builder: connection_options(
            builder, server_name="Translator microservice", grpc_port=8546, http_port=8046
        )
    )
    .create_options(
        lambda builder: server_options(
            builder, module_name="NLP Search", microservice_name="Autocomplete", grpc_port=8545, http_port=8045
        )
    )
    # gRPC connection used only in tests
    .create_options(
        lambda builder: connection_options(
            builder, server_name="Autocomplete microservice", grpc_port=8545, http_port=8045
        )
    )
    .create_options(
        lambda builder: server_options(
            builder, module_name="NLP Search", microservice_name="Spellchecker", grpc_port=8544, http_port=8044
        )
    )
    # gRPC connection used only in tests
    .create_options(
        lambda builder: connection_options(
            builder, server_name="Spellchecker microservice", grpc_port=8544, http_port=8044
        )
    )
    .end_section()
    .options
)
