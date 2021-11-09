"""Specific constants and hardcoded data."""


from __future__ import annotations


MMD_KEYWORDS = ("type", "dataType", "subEntities", "entityName")

# Soon it should be possible to whitelist "fmt: off" and "fmt: on" as eridicate (which flake8-eridicate is based on)
# already supports whitelisting and there is a PR in flake8-eridicate adding this feature
# See: https://github.com/sobolevn/flake8-eradicate/pull/157

# fmt: off  # noqa E800
AQL_KEYWORDS = (
    "all",
    "none",
    "any",
    "count",
    "some",
    "and",
    "or",
    "in",
    "ALL",
    "NONE",
    "ANY",
    "COUNT",
    "SOME",
    "AND",
    "OR",
    "IN",
    "like",
    "match",
    "is",
    "not",
    "eq",
    "gt",
    "lt",
    "gte",
    "lte",
    "ne",
    "neq",
    "LIKE",
    "MATCH",
    "IS",
    "NOT",
    "EQ",
    "GT",
    "LT",
    "GTE",
    "LTE",
    "NE",
    "NEQ",
    "true",
    "false",
    "null",
    "TRUE",
    "FALSE",
    "NULL",
    "Infinity",
    "NaN",
    "$parent",
    "$path",
    "$draft",
    "$fulltext",
    "$id",
    "$type",
    "$recursive",
    "$recursiveDepth",
    "$left",
    "$right",
)
# fmt: on  # noqa E800
