#!/usr/bin/env python3
"""Validates completeness, navigation links, and RTL support across DERA's 10 documentation languages.

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from pathlib import Path
import sys

REQUIRED_LANGUAGES = {
    "en": "README.en.md",
    "es": "README.es.md",
    "fr": "README.fr.md",
    "de": "README.de.md",
    "pt": "README.pt.md",
    "ja": "README.ja.md",
    "ko": "README.ko.md",
    "zh-CN": "README.zh-CN.md",
    "ar": "README.ar.md",
    "ru": "README.ru.md",
}


def validate_i18n_docs(i18n_dir: Path) -> list[str]:
    errors: list[str] = []

    # 1. File existence
    for code, filename in REQUIRED_LANGUAGES.items():
        doc_file = i18n_dir / filename
        if not doc_file.exists():
            errors.append(f"Missing required language documentation file: {filename} ({code})")

    if errors:
        return errors

    # 2. Inspect each document
    for code, filename in REQUIRED_LANGUAGES.items():
        doc_file = i18n_dir / filename
        content = doc_file.read_text(encoding="utf-8")

        # Check for non-corrupted UTF-8 replacement character
        if "\ufffd" in content:
            errors.append(f"{filename}: Contains Unicode replacement character (U+FFFD). Encoding corrupted.")

        # Check for navigation link presence to other languages
        for other_code, other_file in REQUIRED_LANGUAGES.items():
            if other_code == code:
                continue
            if other_file not in content and f"/{other_file}" not in content:
                errors.append(f"{filename}: Missing navigation link to {other_file} ({other_code})")

        # Arabic RTL validation
        if code == "ar":
            if 'dir="rtl"' not in content and "direction: rtl" not in content:
                errors.append(f"{filename}: Arabic documentation must specify RTL direction (dir=\"rtl\").")

    return errors


def main() -> int:
    repo_root = Path(__file__).parent.parent.parent.resolve()
    i18n_dir = repo_root / "docs" / "i18n"

    if not i18n_dir.exists():
        print(f"ERROR: docs/i18n directory not found at {i18n_dir}", file=sys.stderr)
        return 1

    print(f"Validating 10 multilingual documentation files in {i18n_dir.name}...")
    errors = validate_i18n_docs(i18n_dir)

    if errors:
        print(f"\nFound {len(errors)} i18n documentation issues:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"SUCCESS: All 10 language documentation files verified with valid navigation and parity.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
