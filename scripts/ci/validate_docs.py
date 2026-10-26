#!/usr/bin/env python3
"""Validates internal markdown links, heading hierarchy, and UTF-8 encoding in DERA docs.

Copyright (c) 2026 Bunga Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import sys

# Matches standard markdown links [text](target) excluding external http/https/mailto
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def slugify_heading(heading: str) -> set[str]:
    """Generates possible GitHub markdown anchor slugs for a heading."""
    # Strip non-alphanumeric/non-space/non-dash
    clean = re.sub(r"[^\w\s-]", "", heading.lower())
    base_slug = re.sub(r"[-\s]+", "-", clean).strip("-")
    slugs = {base_slug, f"-{base_slug}"}
    
    # Also handle non-ASCII/unicode headings (e.g. CJK, Cyrillic, Arabic)
    words = re.findall(r"[\w-]+", heading.lower())
    if words:
        unicode_slug = "-".join(words)
        slugs.add(unicode_slug)
        slugs.add(f"-{unicode_slug}")
    return slugs


def validate_file(file_path: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [f"{file_path}: Invalid UTF-8 encoding ({exc})"]

    # 1. Heading Check: Top-level documents must have an H1
    headings = HEADING_PATTERN.findall(content)
    if not headings:
        errors.append(f"{file_path}: No markdown headings found.")
    elif headings[0][0] != "#":
        errors.append(f"{file_path}: First heading must be a level-1 heading (#). Found: {headings[0][0]}")

    local_slugs: set[str] = set()
    for h in headings:
        local_slugs.update(slugify_heading(h[1]))

    # 2. Internal Link Validation
    for match in LINK_PATTERN.finditer(content):
        link_target = match.group(2).strip()

        # Skip external web URLs and email addresses
        if link_target.startswith(("http://", "https://", "mailto:", "#")):
            if link_target.startswith("#"):
                anchor = link_target.lstrip("#")
                if anchor and anchor not in local_slugs:
                    errors.append(f"{file_path}: Local anchor #{anchor} not found in headings.")
            continue

        # Split path and optional anchor
        target_parts = link_target.split("#", 1)
        rel_path = target_parts[0]
        anchor = target_parts[1] if len(target_parts) > 1 else None

        if rel_path:
            # Resolve relative to current file's directory
            resolved_target = (file_path.parent / rel_path).resolve()
            if not resolved_target.exists():
                errors.append(f"{file_path}: Broken link to nonexistent file: '{link_target}'")
            elif anchor and resolved_target.suffix.lower() == ".md":
                try:
                    target_content = resolved_target.read_text(encoding="utf-8")
                    target_slugs: set[str] = set()
                    for h in target_headings:
                        target_slugs.update(slugify_heading(h[1]))
                    if anchor not in target_slugs:
                        errors.append(f"{file_path}: Anchor #{anchor} not found in {resolved_target.name}")
                except Exception:
                    pass

    return errors


def main() -> int:
    repo_root = Path(__file__).parent.parent.parent.resolve()
    doc_paths: list[Path] = []

    # Check root docs
    for root_file in ["README.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md"]:
        p = repo_root / root_file
        if p.exists():
            doc_paths.append(p)

    # Check docs/ directory
    docs_dir = repo_root / "docs"
    if docs_dir.exists():
        doc_paths.extend(docs_dir.rglob("*.md"))

    all_errors: list[str] = []
    print(f"Validating {len(doc_paths)} markdown documentation files...")

    for path in sorted(doc_paths):
        errs = validate_file(path, repo_root)
        if errs:
            all_errors.extend(errs)

    if all_errors:
        print(f"\nFound {len(all_errors)} documentation validation issues:", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"SUCCESS: All {len(doc_paths)} markdown documentation files are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
