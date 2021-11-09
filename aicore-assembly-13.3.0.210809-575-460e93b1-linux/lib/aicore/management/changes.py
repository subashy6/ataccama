"""Tools for checking AI Core's CHANGELOG state."""

from __future__ import annotations

import re
import subprocess
import sys

from aicore.common.exceptions import AICoreException


CHANGELOG_FILE_LOCATION = "doc/CHANGELOG.md"


class InvalidBranchError(AICoreException):
    """Error raised when dealing with invalid branch."""


def get_current_branch() -> str:
    """Get currently checked-out branch."""
    args = ["git", "rev-parse", "--abbrev-ref", "HEAD"]

    return subprocess.run(args=args, capture_output=True, text=True, encoding=sys.stdout.encoding).stdout.strip()


def get_previous_release_branch(current_branch: str) -> str:
    """Find previous release branch name from remote based on current branch."""
    args = ["git", "branch", "-r", "-l", "origin/release-*"]

    branches = (
        subprocess.run(args=args, capture_output=True, text=True, encoding=sys.stdout.encoding)
        .stdout.strip()
        .split("\n")
    )
    # Normalize - " origin/release-13.3.X" -> "release-13.3.X"
    branches = [branch.replace("origin/", "").strip(" ") for branch in branches]
    # Ascending order - we are interested in the last one (or the one before if the last one is the current one)
    branches.sort(reverse=True)

    for branch in branches:
        if branch != current_branch:
            return branch

    raise InvalidBranchError("Cannot find previous release branch")


def get_common_ancestor(old_branch: str, new_branch: str) -> str:
    """Get commit hash of common ancestor for two branches."""
    args = ["git", "merge-base", old_branch, new_branch]

    return subprocess.run(args=args, capture_output=True, text=True, encoding=sys.stdout.encoding).stdout.strip()


def get_commits_in_range(start: str, end: str) -> list[str]:
    """Get all commits between two commits/branches."""
    args = ["git", "log", "--format=oneline", f"{start}..{end}"]

    return (
        subprocess.run(args=args, capture_output=True, text=True, encoding=sys.stdout.encoding)
        .stdout.strip()
        .split("\n")
    )


def parse_issue_numbers(commits: list[str]) -> set[str]:
    """Parse all issue numbers from supplied commit messages."""
    issue_numbers = set()

    for commit in commits:
        parsed_issue_numbers = re.findall("ONE-[0-9]+", commit)
        issue_numbers.update(parsed_issue_numbers)

    return issue_numbers


def load_changelog_issue_numbers() -> set[str]:
    """Load all issue numbers from changelog."""
    issue_numbers = set()

    with open(CHANGELOG_FILE_LOCATION) as changelog:
        for line in changelog.readlines():
            parsed_issue_numbers = re.findall("ONE-[0-9]+", line)
            issue_numbers.update(parsed_issue_numbers)

    return issue_numbers


def parse_dependencies_versions(commits: list[str]) -> dict[str, str]:
    """Parse all dependency updates from supplied commit messages."""
    dependencies = {}

    for commit in commits:
        parsed_dependencies = re.findall("Update dependency ([^ ]+) to (.+)", commit)
        if parsed_dependencies:
            dependency, version = parsed_dependencies[0]
            dependencies[dependency] = version

    return dependencies


def load_changelog_dependencies() -> dict[str, str]:
    """Load all dependency updates from changelog."""
    dependencies = {}

    with open(CHANGELOG_FILE_LOCATION) as changelog:
        for line in changelog.readlines():
            parsed_dependencies = re.findall("\\s{2}\\* ([^ ]+) to ([^\\s]+)", line)
            if parsed_dependencies:
                dependency, version = parsed_dependencies[0]
                dependencies[dependency] = version

    return dependencies
