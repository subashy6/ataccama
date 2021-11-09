"""Vocabularies for autocomplete, spell-checking and storing metadata entity names and mmd node names."""

from __future__ import annotations

import collections
import pathlib
import time

from typing import TYPE_CHECKING

from symspellpy import SymSpell

from aicore.nlp_search import constants
from aicore.nlp_search.fixed_autocomplete_module import FixedAutocompleteModule
from aicore.nlp_search.query_parts_config import QueryPartsConfig
from aicore.nlp_search.registry import LogId


if TYPE_CHECKING:
    from typing import Optional

    from aicore.nlp_search.types import EntityInstances


class MetaDataVocabulary:
    """Store MetaData entity names and allow querying them for autocomplete."""

    QUERY_PARTS_SUGGESTIONS = "QUERY_PARTS"

    def __init__(self, query_parts_config: QueryPartsConfig):
        # Query parts new_config loader to get configurations from
        self.query_parts_config: QueryPartsConfig = query_parts_config
        # Mapping of MetaData entity types to their Directed Word Graphs for autocomplete
        self.autocomplete_word_graphs: dict[str, FixedAutocompleteModule] = {}
        # received metadata entity names
        self.entity_names: EntityInstances = {}

        self.update_query_parts(query_parts_config)

    def update_entities(self, received_entity_instances: EntityInstances):
        """Update all entity metadata structures for autocomplete given entity names from MMM."""
        new_entity_names_graphs = {}
        # Re-init the autocomplete word graphs from scratch for two reasons:
        # 1. it is not easy to add/remove single nodes from the word graphs
        # 2. building the graphs happens only 1/min and is quite efficient for reasonable number of entities:
        # 10k nodes ~ 120ms, 100k nodes ~ 1.6s, 500k nodes ~ 9s, 1M nodes ~ 17s
        for entity_type, entity_names in received_entity_instances.items():

            if self.check_names_updated(entity_names, self.entity_names.get(entity_type)):
                autocomplete = FixedAutocompleteModule(words=entity_names)
                new_entity_names_graphs[entity_type] = autocomplete
                self.entity_names[entity_type] = entity_names

            else:
                new_entity_names_graphs[entity_type] = self.autocomplete_word_graphs[entity_type]

        # Assign all dict at once to prevent need for thread locking, short-time un-sync is ok
        self.autocomplete_word_graphs.update(new_entity_names_graphs)

    def update_query_parts(self, new_config: QueryPartsConfig):
        """Update query parts autocomplete based on new query parts config."""
        new_query_parts_graphs = {}
        applicable_types, applicable_everywhere = new_config.applicable_query_part_types()

        for entity, applicable_query_types in applicable_types.items():
            autocomplete_words = (applicable_query_types | applicable_everywhere) - {"fulltext"}  # FE suggests fulltext
            autocomplete = FixedAutocompleteModule(words=autocomplete_words)
            new_query_parts_graphs[self.applicable_for_entity_key(entity)] = autocomplete

        # Assign all dict at once to prevent need for thread locking, short-time un-sync is ok
        self.autocomplete_word_graphs.update(new_query_parts_graphs)

    def applicable_for_entity_key(self, entity_name: str, insert: bool = True) -> str:
        """Prepare key for retraction of autocomplete graph of query part types applicable on given entity."""
        entity_key = f"{MetaDataVocabulary.QUERY_PARTS_SUGGESTIONS}_{entity_name}"
        if not insert and entity_key not in self.autocomplete_word_graphs:
            entity_key = f"{MetaDataVocabulary.QUERY_PARTS_SUGGESTIONS}_{QueryPartsConfig.APPLICABLE_EVERYWHERE}"

        return entity_key

    @staticmethod
    def check_names_updated(new_entities: set[str], current_entities: Optional[set[str]]):
        """Check whether newly received entity names differ from the current ones."""
        return not current_entities or new_entities != current_entities


class AQLKeywordsVocabulary:
    """Store MMD node names and AQL keywords and allow querying them for typo fixing."""

    SPELLCHECK_MAX_EDIT_DISTANCE = 3
    SPELLCHECK_PREFIX_LEN = 7
    MMD_LANGUAGE = "mmd"  # MMD structure tokens

    def __init__(self, vocabularies_folder: str, languages: list[str], logger):
        self.logger = logger
        # Map of languages and corresponding spelling lang_dictionaries
        self.lang_vocabularies: dict[str, SymSpell] = {}

        # Load dictionary, prepare spell checker
        for lang in languages:
            self.lang_vocabularies[lang] = self.load_language(lang, vocabularies_folder)

    def load_language(self, language_to_load: str, vocabularies_folder: str) -> SymSpell:
        """Load spellchecking dictionary from file containing words and their number of occurences."""
        time_start = time.time()
        file_name = f"{language_to_load}_word_frequencies.txt"
        path = pathlib.Path(vocabularies_folder) / file_name
        symspell = SymSpell(self.SPELLCHECK_MAX_EDIT_DISTANCE, self.SPELLCHECK_PREFIX_LEN)

        with self.logger.action(LogId.spellchecker_prepare_vocabulary) as action:
            action.start("Loading dictionary from {path!r}", path=path)
            if symspell.load_dictionary(str(path), term_index=0, count_index=1):
                time_spent = time.time() - time_start
                action.finish("Spellchecking vocabulary prepared in {time:0.2f} sec", time=time_spent)
                return symspell
            else:
                action.error("Vocabulary file not found:{path!r}", path=path)
                raise FileNotFoundError(f"Vocabulary file not found: {path}")

    def update_aql_vocabulary(self, mmd_node_names: set[str]):
        """Update vocabulary with AQL keywords."""
        words_nums = collections.Counter()

        words_nums.update(constants.MMD_KEYWORDS)
        words_nums.update(constants.AQL_KEYWORDS)
        words_nums.update(mmd_node_names)

        symspell = SymSpell(self.SPELLCHECK_MAX_EDIT_DISTANCE, self.SPELLCHECK_PREFIX_LEN)
        for word, count in words_nums.items():
            symspell.create_dictionary_entry(word, count)

        self.lang_vocabularies[self.MMD_LANGUAGE] = symspell
