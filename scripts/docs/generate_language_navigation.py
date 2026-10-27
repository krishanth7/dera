#!/usr/bin/env python3
"""Unified Ten-Language Documentation Navigation Generator for DERA.

Reads docs/i18n/languages.json, calculates relative links for target README
documents, and updates or validates the managed navigation regions demarcated by:
<!-- DERA:I18N_NAV:START --> ... <!-- DERA:I18N_NAV:END -->

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

START_MARKER = "<!-- DERA:I18N_NAV:START -->"
END_MARKER = "<!-- DERA:I18N_NAV:END -->"
MARKER_PATTERN = re.compile(
    re.escape(START_MARKER) + r"(.*?)" + re.escape(END_MARKER),
    re.DOTALL,
)

OFFICIAL_LANGUAGE_CODES = (
    "en",
    "es",
    "fr",
    "de",
    "pt",
    "it",
    "ja",
    "ko",
    "zh-CN",
    "ru",
)

TARGET_DOCUMENTS = [
    "README.md",
    "docs/README.md",
    "docs/i18n/README.en.md",
    "docs/i18n/README.es.md",
    "docs/i18n/README.fr.md",
    "docs/i18n/README.de.md",
    "docs/i18n/README.pt.md",
    "docs/i18n/README.it.md",
    "docs/i18n/README.ja.md",
    "docs/i18n/README.ko.md",
    "docs/i18n/README.zh-CN.md",
    "docs/i18n/README.ru.md",
]


class NavigationError(Exception):
    """Raised when navigation generation or validation fails."""


def validate_manifest_data(data: dict[str, Any], repo_root: Path) -> list[dict[str, str]]:
    """Validates the structure, codes, uniqueness, and file paths of languages.json."""
    if not isinstance(data, dict):
        raise NavigationError("Manifest root must be a JSON object.")

    if data.get("version") != 1:
        raise NavigationError(f"Unsupported manifest version: {data.get('version')} (expected 1).")

    if data.get("default_language") != "en":
        raise NavigationError(
            f"Default language must be 'en', found: {data.get('default_language')}"
        )

    languages = data.get("languages")
    if not isinstance(languages, list):
        raise NavigationError("Manifest 'languages' field must be a list.")

    if len(languages) != len(OFFICIAL_LANGUAGE_CODES):
        raise NavigationError(
            f"Expected exactly {len(OFFICIAL_LANGUAGE_CODES)} languages, found {len(languages)}."
        )

    seen_codes: set[str] = set()
    seen_paths: set[str] = set()
    validated_languages: list[dict[str, str]] = []

    for index, lang in enumerate(languages):
        if not isinstance(lang, dict):
            raise NavigationError(f"Language item #{index} must be an object.")

        code = lang.get("code")
        name = lang.get("name")
        native_name = lang.get("native_name")
        rel_path = lang.get("path")

        if not code or not name or not native_name or not rel_path:
            raise NavigationError(
                f"Language item #{index} missing required fields (code, name, native_name, path)."
            )

        expected_code = OFFICIAL_LANGUAGE_CODES[index]
        if code != expected_code:
            raise NavigationError(
                f"Language #{index + 1} code mismatch: expected '{expected_code}', found '{code}'."
            )

        if code in seen_codes:
            raise NavigationError(f"Duplicate language code: '{code}'.")
        seen_codes.add(code)

        if rel_path in seen_paths:
            raise NavigationError(f"Duplicate language path: '{rel_path}'.")
        seen_paths.add(rel_path)

        # Path traversal guard
        target_path = (repo_root / rel_path).resolve()
        try:
            target_path.relative_to(repo_root.resolve())
        except ValueError as exc:
            raise NavigationError(f"Language path '{rel_path}' escapes repository root.") from exc

        if not target_path.is_file():
            raise NavigationError(
                f"Language file not found: '{rel_path}' (resolved: {target_path})"
            )

        validated_languages.append(
            {
                "code": code,
                "name": name,
                "native_name": native_name,
                "path": rel_path.replace("\\", "/"),
            }
        )

    return validated_languages


def load_manifest(manifest_path: Path, repo_root: Path) -> list[dict[str, str]]:
    """Loads and validates the canonical language manifest."""
    if not manifest_path.is_file():
        raise NavigationError(f"Language manifest not found at: {manifest_path}")

    try:
        content = manifest_path.read_text(encoding="utf-8")
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise NavigationError(f"Malformed JSON in language manifest: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise NavigationError(f"Manifest is not valid UTF-8: {exc}") from exc

    return validate_manifest_data(data, repo_root)


def determine_active_language(doc_rel_path: str, languages: list[dict[str, str]]) -> str | None:
    """Determines which language code is active for a given documentation file."""
    doc_norm = doc_rel_path.replace("\\", "/")

    # Special case: docs/README.md is an index hub, no language is active (all 10 are links)
    if doc_norm == "docs/README.md":
        return None

    # Check direct manifest mapping
    for lang in languages:
        if lang["path"] == doc_norm:
            return lang["code"]

    # Check docs/i18n/README.<code_or_suffix>.md
    filename = Path(doc_norm).name
    if filename == "README.en.md":
        return "en"

    match = re.match(r"^README\.([a-zA-Z0-9-]+)\.md$", filename)
    if match:
        code = match.group(1)
        for lang in languages:
            if lang["code"] == code:
                return code

    return None


def generate_navigation_line(
    doc_rel_path: str,
    languages: list[dict[str, str]],
    repo_root: Path,
) -> str:
    """Generates the pipe-separated navigation line for a target documentation file."""
    source_file = (repo_root / doc_rel_path).resolve()
    source_dir = source_file.parent
    active_code = determine_active_language(doc_rel_path, languages)

    items: list[str] = []
    for lang in languages:
        native_name = lang["native_name"]
        code = lang["code"]

        if code == active_code:
            # Render bold active language without self-link
            items.append(f"**{native_name}**")
        else:
            target_path = (repo_root / lang["path"]).resolve()
            rel_link = os.path.relpath(target_path, source_dir).replace("\\", "/")
            items.append(f"[{native_name}]({rel_link})")

    return " | ".join(items)


def update_managed_region(content: str, new_nav_line: str, doc_name: str) -> str:
    """Replaces content between managed markers. Rejects malformed or duplicate markers."""
    start_count = content.count(START_MARKER)
    end_count = content.count(END_MARKER)

    if start_count == 0 or end_count == 0:
        raise NavigationError(
            f"{doc_name}: Missing navigation markers ({START_MARKER} ... {END_MARKER})."
        )

    if start_count > 1 or end_count > 1:
        raise NavigationError(
            f"{doc_name}: Duplicate navigation markers detected (found {start_count} START, {end_count} END)."
        )

    start_pos = content.find(START_MARKER)
    end_pos = content.find(END_MARKER)

    if end_pos < start_pos:
        raise NavigationError(
            f"{doc_name}: Malformed markers (END marker appears before START marker)."
        )

    managed_block = f"{START_MARKER}\n{new_nav_line}\n{END_MARKER}"
    return MARKER_PATTERN.sub(managed_block, content, count=1)


def process_documents(
    repo_root: Path,
    manifest_path: Path,
    write: bool = False,
) -> tuple[int, list[str]]:
    """Checks or writes navigation for all target documentation files.

    Returns:
        tuple of (error_count, diagnostics_messages)
    """
    diagnostics: list[str] = []

    try:
        languages = load_manifest(manifest_path, repo_root)
    except NavigationError as exc:
        return 1, [f"Manifest error: {exc}"]

    diff_count = 0

    for doc_rel in TARGET_DOCUMENTS:
        doc_path = (repo_root / doc_rel).resolve()

        # Path safety check
        try:
            doc_path.relative_to(repo_root.resolve())
        except ValueError:
            diagnostics.append(f"ERROR: Document path escapes repository: {doc_rel}")
            diff_count += 1
            continue

        if not doc_path.is_file():
            diagnostics.append(f"ERROR: Target document not found: {doc_rel}")
            diff_count += 1
            continue

        try:
            content = doc_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            diagnostics.append(f"ERROR: {doc_rel} is not valid UTF-8 ({exc})")
            diff_count += 1
            continue

        try:
            expected_nav = generate_navigation_line(doc_rel, languages, repo_root)
            updated_content = update_managed_region(content, expected_nav, doc_rel)
        except NavigationError as exc:
            diagnostics.append(f"ERROR: {exc}")
            diff_count += 1
            continue

        if content != updated_content:
            diff_count += 1
            if write:
                doc_path.write_text(updated_content, encoding="utf-8", newline="\n")
                diagnostics.append(f"UPDATED: {doc_rel}")
            else:
                diagnostics.append(f"OUT_OF_SYNC: {doc_rel}")
        else:
            diagnostics.append(f"OK: {doc_rel}")

    return diff_count, diagnostics


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate or validate unified 10-language navigation in DERA Markdown documents."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--check",
        action="store_true",
        help="Check that all documentation navigation blocks are up-to-date (non-mutating).",
    )
    group.add_argument(
        "--write",
        action="store_true",
        help="Update all documentation navigation blocks in place (idempotent).",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Optional path to languages.json manifest.",
    )

    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent.parent.resolve()
    manifest_path = args.manifest or (repo_root / "docs" / "i18n" / "languages.json")

    mode_label = "Checking" if args.check else "Writing"
    print(f"[{mode_label}] DERA 10-language documentation navigation...")

    diff_count, diagnostics = process_documents(
        repo_root=repo_root,
        manifest_path=manifest_path,
        write=args.write,
    )

    for diag in diagnostics:
        print(f"  {diag}")

    if args.check:
        if diff_count > 0:
            print(
                f"\nFAILED: {diff_count} document(s) out of sync or contain navigation errors.",
                file=sys.stderr,
            )
            return 1
        print(
            f"\nSUCCESS: All {len(TARGET_DOCUMENTS)} documents have verified, synchronized navigation."
        )
        return 0
    else:
        print(f"\nSUCCESS: Navigation processing complete ({diff_count} files modified).")
        return 0


if __name__ == "__main__":
    sys.exit(main())
