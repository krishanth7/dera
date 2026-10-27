#!/usr/bin/env python3
"""Validates Conventional Commit formatting on pull request titles.

Accepts PR title via CLI argument (--title or positional) or PR_TITLE environment variable.
Supports breaking change '!' indicator, optional single/compound scopes, and bot titles.
Example: feat(connectors): add SQLite metadata inspection

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import NamedTuple

ALLOWED_TYPES: tuple[str, ...] = (
    "feat",
    "fix",
    "docs",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
    "security",
    "deps",
)

CANONICAL_SCOPES: tuple[str, ...] = (
    "api",
    "web",
    "core",
    "connectors",
    "contracts",
    "cli",
    "graph",
    "erd",
    "diagnostics",
    "models",
    "database",
    "sqlite",
    "postgres",
    "postgresql",
    "mysql",
    "mariadb",
    "docs",
    "i18n",
    "security",
    "ci",
    "governance",
    "architecture",
    "release",
    "deps",
    "repo",
    "python",
    "npm",
    "github",
    "actions",
    "docker",
    "pr",
)

TITLE_REGEX = re.compile(
    r"^(?P<type>[a-z]+)"
    r"(?P<scope_block>(?:\([a-z0-9._/,-]+\))+)*"
    r"(?P<breaking>!)?"
    r": "
    r"(?P<description>.+)$",
    re.UNICODE,
)


class ParsedTitle(NamedTuple):
    commit_type: str
    scopes: list[str]
    is_breaking: bool
    description: str


def is_bot_title(title: str) -> bool:
    """Detect whether a title originates from automated bot integrations like Dependabot."""
    clean = title.strip().lower()
    return "dependabot" in clean or clean.startswith("bump ")


def parse_title(title: str) -> tuple[bool, ParsedTitle | None, list[str]]:
    """Parse and validate pull request title against Conventional Commits."""
    clean_title = title.strip()
    errors: list[str] = []

    if not clean_title:
        return False, None, ["Title is empty or whitespace."]

    if is_bot_title(clean_title):
        return True, ParsedTitle("deps", ["bot"], False, clean_title), []

    match = TITLE_REGEX.match(clean_title)
    if not match:
        return (
            False,
            None,
            [
                f"Title '{clean_title}' does not match Conventional Commit format: "
                "<type>(<optional-scope>)<!>: <description>"
            ],
        )

    commit_type = match.group("type")
    scope_block = match.group("scope_block") or ""
    is_breaking = match.group("breaking") is not None
    description = match.group("description").strip()

    if commit_type not in ALLOWED_TYPES:
        errors.append(
            f"Invalid commit type '{commit_type}'. Allowed types are: {', '.join(ALLOWED_TYPES)}"
        )

    scopes: list[str] = []
    if scope_block:
        raw_scopes = re.findall(r"\(([^)]+)\)", scope_block)
        for raw_scope in raw_scopes:
            scopes.append(raw_scope)
            tokens = re.split(r"[/,]", raw_scope)
            for token in tokens:
                base_token = token.split(".")[0].strip()
                if base_token and base_token not in CANONICAL_SCOPES:
                    errors.append(
                        f"Unrecognized scope token '{token}'. Canonical scopes: {', '.join(CANONICAL_SCOPES)}"
                    )
                    break

    if len(description) < 3:
        errors.append("Description is too short (minimum 3 characters).")

    if errors:
        return False, None, errors

    return True, ParsedTitle(commit_type, scopes, is_breaking, description), []


def validate_title(title: str) -> bool:
    """Convenience boolean helper for programmatic verification."""
    is_valid, _, _ = parse_title(title)
    return is_valid


def main() -> int:
    parser = argparse.ArgumentParser(
        description="DERA Conventional Commit Pull Request Title Validator"
    )
    parser.add_argument("positional_title", nargs="?", help="Pull request title string")
    parser.add_argument("--title", dest="flag_title", help="Explicit pull request title flag")

    args = parser.parse_args()
    raw_title = args.flag_title or args.positional_title or os.environ.get("PR_TITLE", "")

    if not raw_title:
        print(
            "ERROR: No pull request title provided via argument, --title, or PR_TITLE env.",
            file=sys.stderr,
        )
        return 1

    clean_title = raw_title.strip()
    if is_bot_title(clean_title):
        print(f"INFO: Automated bot PR title accepted: '{clean_title}'")
        return 0

    is_valid, parsed, errors = parse_title(clean_title)
    if not is_valid:
        print("\nDERA PR Title Validation Status: FAILED", file=sys.stderr)
        print(f'Received: "{clean_title}"', file=sys.stderr)
        for err in errors:
            print(f"  Error: {err}", file=sys.stderr)
        print(
            "\nExpected format: <type>(<optional-scope>)<!>: <meaningful description>",
            file=sys.stderr,
        )
        print(f"Allowed types: {', '.join(ALLOWED_TYPES)}", file=sys.stderr)
        print(f"Canonical scopes: {', '.join(CANONICAL_SCOPES)}", file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print("  feat(connectors): add SQLite metadata inspection", file=sys.stderr)
        print("  fix(api): handle missing metadata request", file=sys.stderr)
        print("  docs(i18n): synchronize Italian README translation", file=sys.stderr)
        print("  feat(api)!: revise schema response data contract", file=sys.stderr)
        return 1

    assert parsed is not None
    breaking_str = " [BREAKING CHANGE]" if parsed.is_breaking else ""
    scope_str = "".join(f"({s})" for s in parsed.scopes) if parsed.scopes else ""
    print(
        f"SUCCESS: Valid Conventional Commit title: '{parsed.commit_type}{scope_str}: {parsed.description}'{breaking_str}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
