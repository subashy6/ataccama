"""Abbreviations of types used in the management utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    GitHubRepoName = str  # GitHub repository name in format f"{repo_owner}/{repo_name}"
    PackageClassifiers = list[str]  # PIP package metadata -see https://pypi.org/classifiers/
    PackageLicense = str  # Name of the license - subject to normalization and white/blacklisting
    PackageDependencies = dict[str, set[str]]  # Keys: names of PIP packages, values: names of required PIP packages
