#!/usr/bin/env python3
"""Validates canonical language manifest, navigation markers, and cross-navigation parity.

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys

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

UNSUPPORTED_LANGUAGE_CODES = {
    "ar", "hi", "te", "ta", "kn", "ml", "mr", "bn", "gu", "pa", "ur"
}

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


def validate_manifest(manifest_path: Path, repo_root: Path) -> tuple[list[dict[str, str]], list[str]]:
    errors: list[str] = []
    languages: list[dict[str, str]] = []

    if not manifest_path.is_file():
        return [], [f"Language manifest not found at: {manifest_path}"]

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [], [f"Failed to read/parse manifest {manifest_path}: {exc}"]

    if not isinstance(data, dict):
        return [], ["Manifest root must be a JSON object."]

    if data.get("version") != 1:
        errors.append(f"Unsupported manifest version: {data.get('version')} (expected 1)")

    if data.get("default_language") != "en":
        errors.append(f"Default language must be 'en', found: {data.get('default_language')}")

    raw_langs = data.get("languages")
    if not isinstance(raw_langs, list):
        return [], ["Manifest 'languages' must be a list."]

    if len(raw_langs) != len(OFFICIAL_LANGUAGE_CODES):
        errors.append(
            f"Expected exactly {len(OFFICIAL_LANGUAGE_CODES)} languages in manifest, found {len(raw_langs)}."
        )

    seen_codes: set[str] = set()
    seen_paths: set[str] = set()

    for idx, item in enumerate(raw_langs):
        if not isinstance(item, dict):
            errors.append(f"Language item #{idx} is not an object.")
            continue

        code = item.get("code")
        name = item.get("name")
        native_name = item.get("native_name")
        path_str = item.get("path")

        if not all([code, name, native_name, path_str]):
            errors.append(f"Language item #{idx} missing required fields.")
            continue

        if code in UNSUPPORTED_LANGUAGE_CODES:
            errors.append(f"Explicitly unsupported language code detected in manifest: '{code}'.")

        if idx < len(OFFICIAL_LANGUAGE_CODES) and code != OFFICIAL_LANGUAGE_CODES[idx]:
            errors.append(
                f"Language #{idx + 1} mismatch: expected '{OFFICIAL_LANGUAGE_CODES[idx]}', found '{code}'."
            )

        if code in seen_codes:
            errors.append(f"Duplicate language code in manifest: '{code}'.")
        seen_codes.add(code)

        if path_str in seen_paths:
            errors.append(f"Duplicate path in manifest: '{path_str}'.")
        seen_paths.add(path_str)

        resolved_file = (repo_root / path_str).resolve()
        try:
            resolved_file.relative_to(repo_root.resolve())
        except ValueError:
            errors.append(f"Path traversal detected in manifest path: '{path_str}'.")

        if not resolved_file.is_file():
            errors.append(f"Language file does not exist: '{path_str}' ({resolved_file})")

        languages.append({
            "code": code,
            "name": name,
            "native_name": native_name,
            "path": path_str.replace("\\", "/"),
        })

    return languages, errors


def determine_active_language(doc_rel: str, languages: list[dict[str, str]]) -> str | None:
    doc_norm = doc_rel.replace("\\", "/")
    if doc_norm == "docs/README.md":
        return None
    for lang in languages:
        if lang["path"] == doc_norm:
            return lang["code"]
    filename = Path(doc_norm).name
    if filename == "README.en.md":
        return "en"
    match = re.match(r"^README\.([a-zA-Z0-9-]+)\.md$", filename)
    if match:
        return match.group(1)
    return None


def generate_expected_navigation(
    doc_rel: str,
    languages: list[dict[str, str]],
    repo_root: Path,
) -> str:
    source_file = (repo_root / doc_rel).resolve()
    source_dir = source_file.parent
    active_code = determine_active_language(doc_rel, languages)

    items: list[str] = []
    for lang in languages:
        native_name = lang["native_name"]
        code = lang["code"]
        if code == active_code:
            items.append(f"**{native_name}**")
        else:
            target_path = (repo_root / lang["path"]).resolve()
            rel_link = os.path.relpath(target_path, source_dir).replace("\\", "/")
            items.append(f"[{native_name}]({rel_link})")

    return " | ".join(items)


def validate_navigation_in_docs(
    languages: list[dict[str, str]],
    repo_root: Path,
) -> list[str]:
    errors: list[str] = []

    for doc_rel in TARGET_DOCUMENTS:
        doc_path = (repo_root / doc_rel).resolve()
        if not doc_path.is_file():
            errors.append(f"Missing required documentation file: {doc_rel}")
            continue

        try:
            content = doc_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"{doc_rel}: Not valid UTF-8 ({exc})")
            continue

        if "\ufffd" in content:
            errors.append(f"{doc_rel}: Contains Unicode replacement character (U+FFFD).")

        start_count = content.count(START_MARKER)
        end_count = content.count(END_MARKER)

        if start_count == 0 or end_count == 0:
            errors.append(f"{doc_rel}: Missing navigation markers ({START_MARKER} ... {END_MARKER}).")
            continue

        if start_count > 1 or end_count > 1:
            errors.append(f"{doc_rel}: Duplicate navigation markers (found {start_count} START, {end_count} END).")
            continue

        start_pos = content.find(START_MARKER)
        end_pos = content.find(END_MARKER)
        if end_pos < start_pos:
            errors.append(f"{doc_rel}: Malformed markers (END before START).")
            continue

        match = MARKER_PATTERN.search(content)
        if not match:
            errors.append(f"{doc_rel}: Malformed managed navigation region.")
            continue

        actual_nav = match.group(1).strip()
        expected_nav = generate_expected_navigation(doc_rel, languages, repo_root)

        if actual_nav != expected_nav:
            errors.append(
                f"{doc_rel}: Navigation content out of sync with languages.json.\n"
                f"    Expected: {expected_nav}\n"
                f"    Actual:   {actual_nav}"
            )

        # Check that active language does not contain a link to itself
        active_code = determine_active_language(doc_rel, languages)
        if active_code:
            for lang in languages:
                if lang["code"] == active_code:
                    active_name = lang["native_name"]
                    if f"[{active_name}]" in actual_nav:
                        errors.append(f"{doc_rel}: Active language '{active_name}' must not link to itself.")
                    if f"**{active_name}**" not in actual_nav:
                        errors.append(f"{doc_rel}: Active language '{active_name}' must be formatted in bold.")

    return errors


def main() -> int:
    repo_root = Path(__file__).parent.parent.parent.resolve()
    manifest_path = repo_root / "docs" / "i18n" / "languages.json"

    print("Validating canonical language manifest and 10-language documentation navigation...")
    languages, manifest_errors = validate_manifest(manifest_path, repo_root)

    if manifest_errors:
        print(f"\nManifest validation failed with {len(manifest_errors)} error(s):", file=sys.stderr)
        for err in manifest_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    nav_errors = validate_navigation_in_docs(languages, repo_root)

    if nav_errors:
        print(f"\nNavigation validation failed with {len(nav_errors)} error(s):", file=sys.stderr)
        for err in nav_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("SUCCESS: Language manifest and 10-language navigation verified across all documentation targets.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
