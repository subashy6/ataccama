"""Modifications of a fast-autocomplete module to adjust it for search and query autocomplete use-cases."""
from __future__ import annotations

import itertools
import unicodedata

from typing import TYPE_CHECKING

from fast_autocomplete import AutoComplete
from fast_autocomplete.lfucache import LFUCache


if TYPE_CHECKING:
    from collections.abc import Iterable

NORMALIZED_CACHE_SIZE = 2048
MAX_WORD_LENGTH = 40
ORIGINAL_CASE_KEY = "original_case"  # Metadata context keeping original case of suggested words

_normalized_lfu_cache = LFUCache(NORMALIZED_CACHE_SIZE)


class FixedAutocompleteModule(AutoComplete):
    """
    Modified version of fast-autocomplete solving some of our problems.

    Original AutoComplete has problem with normalization of strings, replaces '-' with ' ',
    but does not do that during indexing -> this should fix this.
    Also, unlike in the original AutoComplete, in FixedAutocomplete the search() method
    returns flattened list of suggestions.
    """

    def __init__(self, words: Iterable[str], synonyms=None, full_stop_words=None, logger=None):
        words_with_context: dict[str, dict] = {}
        for word in words:
            normalized_word = self.normalize_node_name(word)
            context = words_with_context.get(normalized_word, {ORIGINAL_CASE_KEY: set()})
            context[ORIGINAL_CASE_KEY].add(word)
            words_with_context[normalized_word] = context

        super().__init__(words_with_context, synonyms, full_stop_words, logger)

    def _search(self, word, max_cost=2, size=5):
        word = self.normalize_node_name(word)
        key = f"{word}-{max_cost}-{size}"
        result = self._lfu_cache.get(key)
        if result == -1:
            result = list(self._find_and_sort(word, max_cost, size))
            self._lfu_cache.set(key, result)
        return result

    def search(self, word: str, max_cost: int = 2, size: int = 5) -> list[str]:
        """
        Search for suggestions, filter out multi-term suggestions and flatten the suggestions.

         E.g.
          'email with' provides suggestions [['email'], ['email', 'sin'], ['email', 'ssn'], ...],
          instead return just ['email']
        parameters:
        - word: the word to return autocomplete results for
        - max_cost: Maximum Levenshtein edit distance to be considered when calculating results
        - size: The max number of results to return
        """
        suggestions_results = self._search(word, max_cost, size)
        suggestions = (suggestion_result[0] for suggestion_result in suggestions_results if len(suggestion_result) == 1)
        result = itertools.chain.from_iterable(
            self.get_original_words(suggested_word) for suggested_word in suggestions
        )
        return list(result)

    def get_original_words(self, normalized_word: str) -> list[str]:
        """Get original words to a normalized word."""
        context = self.words.get(normalized_word)
        return context.get(ORIGINAL_CASE_KEY, [normalized_word])

    @classmethod
    def normalize_node_name(cls, name: str) -> str:
        """
        Normalize a search node's name, remove unsupported characters.

        In the fast-autocomplete module dashes ('-') were replaced with spaces (' ') which is not usable for us.
        """
        if name is None:
            return ""
        name = name[:MAX_WORD_LENGTH]
        result = _normalized_lfu_cache.get(name)
        if result == -1:
            result = cls.get_normalized_node_name(name)
            _normalized_lfu_cache.set(name, result)
        return result

    @staticmethod
    def get_normalized_node_name(name: str) -> str:
        """Normalize the name - shave special characters, remove multiple spaces, make lower-case."""
        name = unicodedata.normalize("NFD", name)
        name = "".join(c for c in name if not unicodedata.combining(c))
        name = unicodedata.normalize("NFC", name.lower())
        return " ".join(name.split())  # unify whitespaces, simpler than using regex
