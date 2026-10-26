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

CONVENTIONAL_PATTERN = re.compile(
    r"^(?:feat|fix|docs|refactor|perf|test|build|ci|chore|revert|security)"
    r"(?:\([a-z0-9._/-]+\))?!?: .+$"
)


def validate_title(title: str) -> bool:
    clean_title = title.strip()
    return bool(CONVENTIONAL_PATTERN.match(clean_title))


def main() -> int:
    title = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PR_TITLE", "")
    if not title:
        print("ERROR: No pull request title provided via argument or PR_TITLE env.", file=sys.stderr)
        return 1

    if not validate_title(title):
        print(f"ERROR: Pull request title '{title}' violates Conventional Commits format.", file=sys.stderr)
        print("Expected format: <type>(<optional-scope>): <summary>", file=sys.stderr)
        print("Allowed types: feat, fix, docs, refactor, perf, test, build, ci, chore, revert, security", file=sys.stderr)
        print("Example: feat(connector): add PostgreSQL catalog inspection", file=sys.stderr)
        return 1

    print(f"SUCCESS: Valid Conventional Commit title: '{title}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
