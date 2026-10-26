#!/usr/bin/env python3
"""Validates Conventional Commit formatting on pull request titles.

Accepts PR title via command-line argument or PR_TITLE environment variable.
Supports breaking change '!' indicator and optional scope.
Example: feat(connector): add PostgreSQL catalog inspection

Copyright (c) 2026 Bunga Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import os
import re
import sys

ALLOWED_TYPES = (
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

CONVENTIONAL_PATTERN = re.compile(
    r"^(?:feat|fix|docs|refactor|perf|test|build|ci|chore|revert|security|deps)"
    r"(?:\([a-z0-9._/,-]+\))*(?:\([a-z0-9._/,-]+\))*!?: .+$"
)


def is_bot_title(title: str) -> bool:
    """Detect whether a title originates from automated bot integrations like Dependabot."""
    clean = title.strip().lower()
    return "dependabot" in clean or clean.startswith("bump ")


def validate_title(title: str) -> bool:
    """Validate that title complies with Conventional Commits 1.0.0 or is a recognized bot title."""
    clean_title = title.strip()
    if is_bot_title(clean_title):
        return True
    match = CONVENTIONAL_PATTERN.match(clean_title)
    if not match:
        return False
    # Ensure description after ': ' is not empty or pure whitespace
    parts = clean_title.split(": ", 1)
    if len(parts) < 2 or not parts[1].strip():
        return False
    return True


def main() -> int:
    title = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PR_TITLE", "")
    if not title:
        print("ERROR: No pull request title provided via argument or PR_TITLE env.", file=sys.stderr)
        return 1

    clean_title = title.strip()
    if is_bot_title(clean_title):
        print(f"INFO: Automated bot PR title accepted: '{clean_title}'")
        return 0

    if not validate_title(clean_title):
        print(f"ERROR: Pull request title '{clean_title}' violates Conventional Commits format.", file=sys.stderr)
        print("Expected format: <type>(<optional-scope>): <summary>", file=sys.stderr)
        print(f"Allowed types: {', '.join(ALLOWED_TYPES)}", file=sys.stderr)
        print("Example: feat(connectors): add PostgreSQL catalog inspection", file=sys.stderr)
        print("Example with breaking change: feat(api)!: revise schema response contract", file=sys.stderr)
        return 1

    print(f"SUCCESS: Valid Conventional Commit title: '{clean_title}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())

