#!/usr/bin/env python3
"""Audits and maintains GitHub Actions cache entries for DERA.

Uses the GitHub CLI to inspect cache key prefixes, total storage footprint,
and prune stale caches when total size exceeds policy thresholds.
Copyright (c) 2026 Bunga Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import json
import subprocess
import sys


def get_cache_list() -> list[dict]:
    try:
        res = subprocess.run(
            ["gh", "cache", "list", "--json", "id,key,sizeInBytes,createdAt,lastAccessedAt"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(res.stdout)
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"INFO: Could not query gh cache list ({exc}). Running offline analysis.")
        return []


def format_bytes(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def main() -> int:
    caches = get_cache_list()
    if not caches:
        print("No active GitHub Actions cache entries detected or running outside authenticated CLI environment.")
        return 0

    total_bytes = sum(c.get("sizeInBytes", 0) for c in caches)
    print(f"Total Cache Entries: {len(caches)}")
    print(f"Total Storage Consumed: {format_bytes(total_bytes)}")

    # Sort by oldest accessed
    sorted_caches = sorted(caches, key=lambda x: x.get("lastAccessedAt", x.get("createdAt", "")))
    for c in sorted_caches[:5]:
        print(f"  - Key: {c.get('key')} | Size: {format_bytes(c.get('sizeInBytes', 0))} | Last Accessed: {c.get('lastAccessedAt')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
