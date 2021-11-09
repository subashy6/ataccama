"""Spellchecking AQL queries and enhancing them with similar values."""

from __future__ import annotations

import re
import string

from typing import TYPE_CHECKING

from symspellpy import Verbosity

from aicore.nlp_search.vocabularies import AQLKeywordsVocabulary


if TYPE_CHECKING:
    from aicore.nlp_search.types import AQLString

    TemplateVariable = str


class Spellchecker:
    """Check AQL query for typos in keywords or template values."""

    AQL_SPLIT_VALUES = r"[{})(.\s\[\]@=]"
    AQL_TEMPLATE_VAR_PREFIX = "var"
    NUM_FIX_SUGGESTIONS = 3

    def __init__(self, config, aql_vocabulary: AQLKeywordsVocabulary):
        self.config = config
        self.aql_vocabulary = aql_vocabulary
        self.spellcheck_languages = [
            lang for lang in aql_vocabulary.lang_vocabularies if lang != AQLKeywordsVocabulary.MMD_LANGUAGE
        ]
        self.quoted_string_re: re.Pattern = re.compile(  # Find strings in quotes
            r"""(["'])              # any initial quote
            ((?:\\["']|(?!\1).)*)   # anything except the same quote if not escaped
            (\1)                    # the same quote""",
            re.VERBOSE,
        )
        self.template_var_re: re.Pattern = re.compile(r"\${" + self.AQL_TEMPLATE_VAR_PREFIX + r"[0-9]{0,4}\}")

        self.in_vars_re = re.compile(
            r"""\s(?:in)  # starting with ' in'
            \s*\([^)]+\)  # take everything between two following braces""",
            flags=re.IGNORECASE | re.VERBOSE,
        )

    def fix_typos(self, aql_query: AQLString, _user_id: str, _query_id: str) -> str:
        """Perform spellchecking of the AQL query."""
        aql_template, value_mapping = self.extract_template(aql_query)
        fixed_template = self.typo_check_template(aql_template)
        value_synonyms = self.get_synonyms(value_mapping)
        fixed_aql = self.combine_template_values(fixed_template, value_mapping, value_synonyms)

        if self.check_alq_filled(fixed_aql):
            return fixed_aql

        return aql_query  # if AQL cannot be correctly filled, fallback and return original query

    def extract_template(self, aql_query: AQLString) -> tuple[AQLString, dict[TemplateVariable, str]]:
        """Extract values from AQL and replace them with placeholder identifiers $var1, ..., $varN."""
        aql_template = aql_query
        value_mapping = {}
        found_values = self.quoted_string_re.findall(aql_query)

        for idx, found_parts in enumerate(found_values):
            _, value, _ = found_parts
            quoted_value = "".join(found_parts)
            placeholder_name = f"{self.AQL_TEMPLATE_VAR_PREFIX}{idx+1}"
            placeholder_value = "${" + placeholder_name + "}"

            value_mapping[placeholder_name] = value
            aql_template = aql_template.replace(quoted_value, placeholder_value, 1)

        return aql_template, value_mapping

    def typo_check_template(self, aql_template: AQLString) -> AQLString:
        """Spellcheck the template words by applying AQLKeywordsVocabulary."""
        words = self.get_template_words_to_fix(aql_template)
        type_checked_words = self.augment_words(words, AQLKeywordsVocabulary.MMD_LANGUAGE, Verbosity.CLOSEST)
        fixed_template = self.apply_fixes(aql_template, type_checked_words)
        return fixed_template

    def get_synonyms(self, value_mapping: dict[TemplateVariable, str]) -> dict[TemplateVariable, list[str]]:
        """Augment the AQL constraints values by synonyms and words close from the dictionary."""
        similar_words = {}
        for placeholder, value in value_mapping.items():
            similar = set()
            for language in self.spellcheck_languages:
                similar.update(list(self.augment_words([value], language, Verbosity.ALL).values())[0])

            similar_words[placeholder] = list(similar)
        return similar_words

    def combine_template_values(
        self,
        fixed_template: AQLString,
        value_mapping: dict[TemplateVariable, str],
        synonyms: dict[TemplateVariable, list[str]],
    ) -> AQLString:
        """Combine AQL template and augmented values into a single AQL string."""
        if not value_mapping:
            return fixed_template

        # in ("...", "...") -> in ("...", "...", "...")
        new_template = self.combine_in_vars(fixed_template, value_mapping, synonyms)

        for variable_name in value_mapping:
            #  [=, ==, is, eq] -> in (...)
            new_template = self.combine_eq_vars(new_template, variable_name, value_mapping, synonyms)
            #  [is not, ne, neq, <>] -> neq ... (no synonyms)
            new_template = self.combine_neq_vars(new_template, variable_name, value_mapping)
            # [like, match, ~] -> (like ... or like ...)
            new_template = self.combine_like_vars(new_template, variable_name, value_mapping, synonyms)

        return new_template

    def get_template_words_to_fix(self, aql_template: AQLString) -> list[str]:
        """From AQL template extract words that should to be checked for typos."""
        words = set()
        aql_template = re.sub(self.template_var_re, "", aql_template)  # Remove placeholders
        for part in re.split(self.AQL_SPLIT_VALUES, aql_template):
            # Do not spellcheck empty strings, variables, numbers
            if len(part) > 1 and not is_number(part) and not is_hex_number(part):
                words.add(part)

        return list(words)

    def apply_fixes(self, aql_template: AQLString, fixes: dict[str, list[str]]) -> AQLString:
        """Apply template typo fixes."""
        fixed_template = aql_template
        for orig_word, suggested_fixes in fixes.items():
            if not suggested_fixes:
                continue

            pattern = f"(^|{self.AQL_SPLIT_VALUES}){re.escape(orig_word)}({self.AQL_SPLIT_VALUES}|$)"
            substitution_fix = r"\1" + suggested_fixes[0] + r"\2"
            fixed_template = re.sub(pattern, substitution_fix, fixed_template)

        return fixed_template

    def augment_words(self, words: list[str], language: str, verbosity: Verbosity) -> dict[str, list[str]]:
        """Augment by closest words from vocabulary. Verbosity defines how many results to return."""
        augmented = {}
        vocabulary = self.aql_vocabulary.lang_vocabularies.get(language)
        if not vocabulary:
            return augmented

        for word in words:
            if word:
                suggestions = vocabulary.lookup(word, verbosity)
                augmented[word] = [suggestion.term for suggestion in suggestions[: self.NUM_FIX_SUGGESTIONS]]

        return augmented

    def combine_in_vars(self, template: AQLString, value_mapping, synonyms) -> AQLString:
        """Fill template values that are within 'in' block: in ("...", "...") -> in ("...", "...", "...")."""
        new_str = template

        found_in_parts = re.findall(self.in_vars_re, template)  # Find all in-parts, e.g. in (??var1??, ??var2??)

        for in_part in found_in_parts:
            for var_placeholder in re.findall(self.template_var_re, in_part):  # Find variables within in-part
                var = variable_name(var_placeholder)
                all_value_versions = self.prepare_values(var, value_mapping, synonyms)

                replacement_str = ", ".join(all_value_versions)
                new_str = string.Template(new_str).safe_substitute({var: replacement_str})

        return new_str

    def combine_eq_vars(self, template, variable_name, value_mapping, synonyms):
        """Try substituting values that are used in equals cases: [=, ==, is, eq] -> in (...)."""
        values = self.prepare_values(variable_name, value_mapping, synonyms)
        replacement = " in(" + ",".join(values) + ")"
        pattern_prefix = r"((?<!\!)=+(\s)*|(?<!n)is(\s)+|(?<!n)eq(\s)+)"
        eq_pattern = pattern_prefix + var_name_to_placeholder(variable_name)

        return re.sub(eq_pattern, replacement, template, flags=re.IGNORECASE)  # Replace eq occurrences with 'in(...)

    def combine_neq_vars(self, template, variable_name, value_mapping):
        """Try substituting values that are used in non equals cases: [is not, neq, <>] -> neq ..."""
        values = self.prepare_values(variable_name, value_mapping, {})  # Do not add synonyms for neq case
        replacement = " neq " + values[0]  # Values will always be list with one item
        pattern_prefix = r"(\!=\s*|\sis not\s+|\sneq\s+|<>\s*)"
        pattern = pattern_prefix + var_name_to_placeholder(variable_name)

        return re.sub(pattern, replacement, template, flags=re.IGNORECASE)

    def combine_like_vars(self, template, variable_name, value_mapping, synonyms):
        """Try substituting values that are used in like cases: [like, match, ~] -> (like ... or like ...)."""
        # find replacements:
        values = self.prepare_values(variable_name, value_mapping, synonyms)
        in_repl = " or like ".join(values)
        replacement = "(like " + in_repl + ")"
        pattern_like = re.compile(
            r"""((?<=(\s|\())  # starts with white chart or left brace (or nothing for ~ character)
            (like|match)|~)    # AQL key word
            \s*"""
            + var_name_to_placeholder(variable_name),  # variable string
            flags=re.VERBOSE | re.IGNORECASE,
        )
        return re.sub(pattern_like, replacement, template)

    def prepare_values(self, variable_name: str, value_mapping, synonyms) -> list[str]:
        """Prepare template values as a combination of the original value and synonyms."""
        all_vals = ["'" + escape_quotes(synonym) + "'" for synonym in synonyms.get(variable_name, [])]
        return all_vals + ["'" + escape_quotes(value_mapping[variable_name]) + "'"]

    def check_alq_filled(self, fixed_aql) -> bool:
        """Check whether the fixed AQL is constructed correctly and does not contain unfilled template."""
        return not re.findall(self.template_var_re, fixed_aql)


def is_number(s: str) -> bool:
    """Return True is string is a number."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def is_hex_number(s_value: str) -> bool:
    """Return True if string is a hexadecimal number starting with 0x."""
    value = s_value.lower()
    return value.startswith("0x") and all(c in string.hexdigits for c in s_value[2:])


def variable_name(placeholder: str) -> str:
    """Extract variable name from template placeholder string - ${var1} -> var1."""
    return placeholder[2:-1]


def var_name_to_placeholder(var_name: str):
    """Convert variable name to string template placeholder representation."""
    return r"\$\{" + var_name + r"\}"


def escape_quotes(string_to_escape: str) -> str:
    r"""Escape quotes of a string: '"' -> '\"', and ''' -> '\''."""
    return string_to_escape.replace(r'"', r"\"").replace(r"'", r"\'")
