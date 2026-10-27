#!/usr/bin/env python3
"""Automated regression test suite for DERA translation structural parity and i18n governance.

Tests canonical manifest integrity, language exclusions, navigation synchronization,
code fence parity, heading section counts, technical token preservation, and drift detection.

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.ci.validate_i18n import (
    OFFICIAL_LANGUAGE_CODES,
    extract_code_block_languages,
    validate_manifest,
    validate_technical_tokens,
    validate_translation_parity,
)


class TestI18nParity(unittest.TestCase):
    """Regression test suite for DERA internationalization and translation parity."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parent.parent.parent
        cls.manifest_path = cls.repo_root / "docs" / "i18n" / "languages.json"

    # -------------------------------------------------------------
    # 1. Canonical Language Manifest Tests
    # -------------------------------------------------------------

    def test_canonical_manifest_official_ten_languages(self) -> None:
        """Verifies canonical manifest loads cleanly and contains exactly the 10 official languages in order."""
        languages, errors = validate_manifest(self.manifest_path, self.repo_root)
        self.assertEqual(len(errors), 0, f"Manifest validation errors: {errors}")
        self.assertEqual(len(languages), 10)
        codes = tuple(lang["code"] for lang in languages)
        self.assertEqual(codes, OFFICIAL_LANGUAGE_CODES)

    def test_manifest_rejection_of_unsupported_languages(self) -> None:
        """Verifies that Arabic, Hindi, Telugu, and other excluded regional languages are rejected."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / "languages.json"
            for code in ["ar", "hi", "te", "ta", "kn", "ml", "mr", "bn", "gu", "pa", "ur"]:
                fake_manifest = {
                    "version": 1,
                    "default_language": "en",
                    "languages": [
                        {
                            "code": "en",
                            "name": "English",
                            "native_name": "English",
                            "path": "README.md",
                        },
                        {
                            "code": code,
                            "name": "Excluded",
                            "native_name": "Excluded",
                            "path": "README.md",
                        },
                    ],
                }
                import json

                tmp_path.write_text(json.dumps(fake_manifest), encoding="utf-8")
                _, errors = validate_manifest(tmp_path, self.repo_root)
                self.assertTrue(
                    any("unsupported language code" in err.lower() for err in errors),
                    f"Expected rejection for code '{code}'",
                )

    def test_manifest_duplicate_code_detection(self) -> None:
        """Verifies that duplicate language codes are rejected."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / "languages.json"
            fake_manifest = {
                "version": 1,
                "default_language": "en",
                "languages": [
                    {
                        "code": "en",
                        "name": "English 1",
                        "native_name": "English",
                        "path": "README.md",
                    },
                    {
                        "code": "en",
                        "name": "English 2",
                        "native_name": "English",
                        "path": "docs/README.md",
                    },
                ],
            }
            import json

            tmp_path.write_text(json.dumps(fake_manifest), encoding="utf-8")
            _, errors = validate_manifest(tmp_path, self.repo_root)
            self.assertTrue(any("duplicate language code" in err.lower() for err in errors))

    def test_manifest_path_traversal_detection(self) -> None:
        """Verifies that relative paths attempting directory traversal are caught."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / "languages.json"
            fake_manifest = {
                "version": 1,
                "default_language": "en",
                "languages": [
                    {
                        "code": "es",
                        "name": "Spanish",
                        "native_name": "Español",
                        "path": "../../outside/README.es.md",
                    }
                ],
            }
            import json

            tmp_path.write_text(json.dumps(fake_manifest), encoding="utf-8")
            _, errors = validate_manifest(tmp_path, self.repo_root)
            self.assertTrue(any("path traversal detected" in err.lower() for err in errors))

    # -------------------------------------------------------------
    # 2. Translation Structural Parity Tests
    # -------------------------------------------------------------

    def test_all_ten_readmes_exist_and_valid_utf8(self) -> None:
        """Verifies that all 10 READMEs exist, are valid UTF-8, and contain no replacement chars."""
        en_readme = self.repo_root / "README.md"
        self.assertTrue(en_readme.is_file())
        self.assertNotIn("\ufffd", en_readme.read_text(encoding="utf-8"))

        for code in OFFICIAL_LANGUAGE_CODES[1:]:
            trans_file = self.repo_root / "docs" / "i18n" / f"README.{code}.md"
            self.assertTrue(trans_file.is_file(), f"Missing translation: {trans_file}")
            content = trans_file.read_text(encoding="utf-8")
            self.assertNotIn(
                "\ufffd",
                content,
                f"Translation '{code}' contains Unicode replacement character (U+FFFD)",
            )

    def test_full_repository_translation_parity(self) -> None:
        """Verifies that validate_translation_parity passes with zero errors on repository baseline."""
        errors = validate_translation_parity(self.repo_root)
        self.assertEqual(
            len(errors),
            0,
            "Expected zero parity errors, found:\n" + "\n".join(errors),
        )

    def test_code_block_sequence_parity(self) -> None:
        """Verifies that code block sequence across all 9 translations strictly matches English source."""
        en_content = (self.repo_root / "README.md").read_text(encoding="utf-8")
        expected_fences = extract_code_block_languages(en_content)

        for code in OFFICIAL_LANGUAGE_CODES[1:]:
            trans_path = self.repo_root / "docs" / "i18n" / f"README.{code}.md"
            content = trans_path.read_text(encoding="utf-8")
            actual_fences = extract_code_block_languages(content)
            self.assertEqual(
                actual_fences,
                expected_fences,
                f"Code block sequence mismatch in {trans_path.name}",
            )

    def test_major_section_heading_parity(self) -> None:
        """Verifies that all 10 READMEs contain exactly 15 major H2 structural sections."""
        import re

        en_content = (self.repo_root / "README.md").read_text(encoding="utf-8")
        expected_h2 = len(re.findall(r"^##\s+(.+)$", en_content, re.MULTILINE))
        self.assertEqual(expected_h2, 15)

        for code in OFFICIAL_LANGUAGE_CODES[1:]:
            trans_path = self.repo_root / "docs" / "i18n" / f"README.{code}.md"
            content = trans_path.read_text(encoding="utf-8")
            actual_h2 = len(re.findall(r"^##\s+(.+)$", content, re.MULTILINE))
            self.assertEqual(
                actual_h2,
                expected_h2,
                f"H2 section count mismatch in {trans_path.name}: expected {expected_h2}, got {actual_h2}",
            )

    # -------------------------------------------------------------
    # 3. Technical Token Preservation Tests
    # -------------------------------------------------------------

    def test_technical_tokens_preserved_across_all_translations(self) -> None:
        """Verifies that core non-translatable tokens (packages, commands, dialects) are preserved."""
        errors = validate_technical_tokens(self.repo_root)
        self.assertEqual(
            len(errors),
            0,
            "Expected zero token errors, found:\n" + "\n".join(errors),
        )

    def test_token_drift_detection(self) -> None:
        """Verifies that removing a mandatory technical token triggers a diagnostic error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            fake_root = Path(tmp_dir)
            fake_docs = fake_root / "docs" / "i18n"
            fake_docs.mkdir(parents=True)

            # Create an English README and an invalid translation missing 'packages/core'
            (fake_root / "README.md").write_text("# DERA\npackages/core", encoding="utf-8")
            (fake_docs / "README.es.md").write_text("# DERA\nsin-paquetes", encoding="utf-8")

            errors = validate_technical_tokens(fake_root)
            self.assertTrue(
                any("packages/core" in err for err in errors),
                f"Expected error for missing packages/core, got: {errors}",
            )


if __name__ == "__main__":
    unittest.main()
