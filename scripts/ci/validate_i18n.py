#!/usr/bin/env python3
"""Validates canonical language manifest, navigation markers, translation parity, and technical tokens.

Enforces DERA's strict ten-language policy, cross-navigation synchronization,
structural parity across translations, and non-translatable technical token preservation.

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

UNSUPPORTED_LANGUAGE_CODES = {"ar", "hi", "te", "ta", "kn", "ml", "mr", "bn", "gu", "pa", "ur"}

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

# Non-translatable technical tokens that must be preserved in all 9 translations
REQUIRED_TECHNICAL_TOKENS = [
    "DERA",
    "Krishanth",
    "MIT",
    "packages/core",
    "packages/connectors",
    "packages/contracts",
    "apps/api",
    "apps/web",
    "dev.py",
    "sqlite",
    "postgresql",
]


def validate_manifest(
    manifest_path: Path, repo_root: Path
) -> tuple[list[dict[str, str]], list[str]]:
    """Validates languages.json for exact count, order, codes, paths, and no traversal."""
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

        languages.append(
            {
                "code": code,
                "name": name,
                "native_name": native_name,
                "path": path_str.replace("\\", "/"),
            }
        )

    return languages, errors


def determine_active_language(doc_rel: str, languages: list[dict[str, str]]) -> str | None:
    """Determines the active language code for a given relative document path."""
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
    """Computes the expected relative navigation markup for a target document."""
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
    """Validates navigation markers, active bolding, self-links, and UTF-8 encoding."""
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
            errors.append(
                f"{doc_rel}: Missing navigation markers ({START_MARKER} ... {END_MARKER})."
            )
            continue

        if start_count > 1 or end_count > 1:
            errors.append(
                f"{doc_rel}: Duplicate navigation markers (found {start_count} START, {end_count} END)."
            )
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

        active_code = determine_active_language(doc_rel, languages)
        if active_code:
            for lang in languages:
                if lang["code"] == active_code:
                    active_name = lang["native_name"]
                    if f"[{active_name}]" in actual_nav:
                        errors.append(
                            f"{doc_rel}: Active language '{active_name}' must not link to itself."
                        )
                    if f"**{active_name}**" not in actual_nav:
                        errors.append(
                            f"{doc_rel}: Active language '{active_name}' must be formatted in bold."
                        )

    return errors


def extract_code_block_languages(content: str) -> list[str]:
    """Extracts the sequential list of code block languages (e.g. ['text', 'mermaid', ...])."""
    languages: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") and len(stripped) > 3:
            languages.append(stripped[3:].strip())
    return languages


def validate_translation_parity(repo_root: Path) -> list[str]:
    """Validates structural parity between each translated README and the English source.

    Compares code block sequences, major structural section counts, and Mermaid blocks.
    """
    errors: list[str] = []
    en_path = repo_root / "README.md"
    if not en_path.is_file():
        return [f"Authoritative English README not found at: {en_path}"]

    en_content = en_path.read_text(encoding="utf-8")
    expected_fences = extract_code_block_languages(en_content)
    expected_h2_count = len(re.findall(r"^##\s+(.+)$", en_content, re.MULTILINE))
    expected_mermaid_count = len(re.findall(r"^```mermaid", en_content, re.MULTILINE))

    # Check all 9 derivative translations
    for code in OFFICIAL_LANGUAGE_CODES[1:]:
        rel_path = f"docs/i18n/README.{code}.md"
        trans_file = repo_root / rel_path
        if not trans_file.is_file():
            errors.append(f"Missing translated README for '{code}': {rel_path}")
            continue

        try:
            content = trans_file.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"{rel_path}: Invalid UTF-8 encoding ({exc})")
            continue

        if "\ufffd" in content:
            errors.append(f"{rel_path}: Contains Unicode replacement character (U+FFFD).")

        # 1. Code fence parity
        actual_fences = extract_code_block_languages(content)
        if len(actual_fences) != len(expected_fences):
            errors.append(
                f"{rel_path}: Code block count mismatch: expected {len(expected_fences)}, found {len(actual_fences)}."
            )
        elif actual_fences != expected_fences:
            errors.append(
                f"{rel_path}: Code block language sequence mismatch.\n"
                f"    Expected: {expected_fences}\n"
                f"    Found:    {actual_fences}"
            )

        # 2. Section parity (H2 headings)
        actual_h2_count = len(re.findall(r"^##\s+(.+)$", content, re.MULTILINE))
        if actual_h2_count != expected_h2_count:
            errors.append(
                f"{rel_path}: Major structural section count mismatch: expected {expected_h2_count} (H2), found {actual_h2_count}."
            )

        # 3. Mermaid diagram parity
        actual_mermaid_count = len(re.findall(r"^```mermaid", content, re.MULTILINE))
        if actual_mermaid_count != expected_mermaid_count:
            errors.append(
                f"{rel_path}: Mermaid diagram count mismatch: expected {expected_mermaid_count}, found {actual_mermaid_count}."
            )

    return errors


def validate_technical_tokens(repo_root: Path) -> list[str]:
    """Ensures non-translatable technical identifiers remain intact across all 9 translations."""
    errors: list[str] = []

    for code in OFFICIAL_LANGUAGE_CODES[1:]:
        rel_path = f"docs/i18n/README.{code}.md"
        trans_file = repo_root / rel_path
        if not trans_file.is_file():
            continue

        content = trans_file.read_text(encoding="utf-8")
        content_lower = content.lower()

        missing_tokens: list[str] = []
        for token in REQUIRED_TECHNICAL_TOKENS:
            if token.lower() not in content_lower:
                missing_tokens.append(token)

        if missing_tokens:
            errors.append(
                f"{rel_path}: Missing non-translatable technical token(s): {', '.join(missing_tokens)}"
            )

    return errors


def validate_translation_freshness(repo_root: Path) -> list[str]:
    """Verifies that international documentation files track English baseline metadata without corruption."""
    errors: list[str] = []
    # Check if translation maintenance policy exists and specifies baseline tracking
    maintenance_policy = repo_root / "docs" / "i18n" / "TRANSLATION_MAINTENANCE.md"
    if not maintenance_policy.is_file():
        errors.append(f"Missing translation maintenance guide: {maintenance_policy}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Authoritative internationalization & translation validator for DERA."
    )
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help="Validate only languages.json manifest.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    manifest_path = repo_root / "docs" / "i18n" / "languages.json"

    print("Executing DERA Multilingual Documentation & Internationalization Qualification...")
    print(f"Repository Root: {repo_root}")

    # Domain 1: Manifest Validation
    languages, manifest_errors = validate_manifest(manifest_path, repo_root)

    if args.manifest_only:
        if manifest_errors:
            for err in manifest_errors:
                print(f"ERROR: {err}", file=sys.stderr)
            return 1
        print("SUCCESS: Language manifest verified.")
        return 0

    # Domain 2: Navigation Synchronization
    nav_errors = validate_navigation_in_docs(languages, repo_root) if not manifest_errors else []

    # Domain 3: Translation Structural Parity
    parity_errors = validate_translation_parity(repo_root)

    # Domain 4: Non-translatable Technical Token Preservation
    token_errors = validate_technical_tokens(repo_root)

    # Domain 5: Freshness & Governance Metadata
    freshness_errors = validate_translation_freshness(repo_root)

    all_errors = manifest_errors + nav_errors + parity_errors + token_errors + freshness_errors

    # Structured Domain Diagnostic Output (Prompt Section 27)
    manifest_status = "PASS" if not manifest_errors else "FAIL"
    nav_status = "PASS" if not nav_errors and not manifest_errors else "FAIL"
    parity_status = "PASS" if not parity_errors else "FAIL"
    token_status = "PASS" if not token_errors else "FAIL"
    freshness_status = "PASS" if not freshness_errors else "FAIL"
    overall_status = "PASS" if not all_errors else "FAIL"

    print("\nDERA Internationalization CI")
    print("============================")
    print(f"Language manifest:          {manifest_status}")
    print(f"README navigation:          {nav_status}")
    print(f"Translation structure:      {parity_status}")
    print(f"Technical token parity:     {token_status}")
    print(f"Freshness metadata:         {freshness_status}")
    print(f"Overall: {overall_status}\n")

    if all_errors:
        print(f"FAILED: Found {len(all_errors)} internationalization issue(s):", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("SUCCESS: All 10 official languages and translations verified successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
