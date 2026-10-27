"""Unit tests for DERA's unified ten-language documentation navigation system.

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.docs.generate_language_navigation import (
    END_MARKER,
    OFFICIAL_LANGUAGE_CODES,
    START_MARKER,
    TARGET_DOCUMENTS,
    NavigationError,
    determine_active_language,
    generate_navigation_line,
    load_manifest,
    process_documents,
    update_managed_region,
    validate_manifest_data,
)


class TestLanguageNavigation(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).parent.parent.parent.resolve()
        self.manifest_path = self.repo_root / "docs" / "i18n" / "languages.json"
        self.languages = load_manifest(self.manifest_path, self.repo_root)

    def test_canonical_manifest_structure_and_count(self) -> None:
        """Verifies canonical manifest loads cleanly and contains exactly 10 official languages."""
        self.assertEqual(len(self.languages), 10)
        loaded_codes = tuple(lang["code"] for lang in self.languages)
        self.assertEqual(loaded_codes, OFFICIAL_LANGUAGE_CODES)

    def test_unsupported_languages_rejected(self) -> None:
        """Verifies that Arabic and Indian languages are rejected if present in manifest."""
        unsupported = ["ar", "hi", "te", "ta", "kn", "ml", "mr", "bn", "gu", "pa", "ur"]
        for code in unsupported:
            fake_data = {
                "version": 1,
                "default_language": "en",
                "languages": [
                    {"code": code, "name": "Unsupported", "native_name": "Bad", "path": "README.md"}
                ],
            }
            with self.assertRaises(NavigationError):
                validate_manifest_data(fake_data, self.repo_root)

    def test_duplicate_codes_rejected(self) -> None:
        """Verifies duplicate language codes raise NavigationError."""
        fake_data = {
            "version": 1,
            "default_language": "en",
            "languages": [
                {"code": "en", "name": "English", "native_name": "English", "path": "README.md"},
                {
                    "code": "en",
                    "name": "English2",
                    "native_name": "English2",
                    "path": "docs/README.md",
                },
            ],
        }
        with self.assertRaises(NavigationError):
            validate_manifest_data(fake_data, self.repo_root)

    def test_duplicate_paths_rejected(self) -> None:
        """Verifies duplicate file paths raise NavigationError."""
        fake_data = {
            "version": 1,
            "default_language": "en",
            "languages": [
                {"code": "en", "name": "English", "native_name": "English", "path": "README.md"},
                {"code": "es", "name": "Spanish", "native_name": "Español", "path": "README.md"},
            ],
        }
        with self.assertRaises(NavigationError):
            validate_manifest_data(fake_data, self.repo_root)

    def test_missing_language_file_rejected(self) -> None:
        """Verifies nonexistent language paths raise NavigationError."""
        fake_data = {
            "version": 1,
            "default_language": "en",
            "languages": [
                {
                    "code": "en",
                    "name": "English",
                    "native_name": "English",
                    "path": "nonexistent/file.md",
                }
            ]
            * 10,
        }
        with self.assertRaises(NavigationError):
            validate_manifest_data(fake_data, self.repo_root)

    def test_path_traversal_rejected(self) -> None:
        """Verifies paths escaping the repository root raise NavigationError."""
        fake_data = {
            "version": 1,
            "default_language": "en",
            "languages": [
                {
                    "code": "en",
                    "name": "English",
                    "native_name": "English",
                    "path": "../../outside.md",
                }
            ]
            * 10,
        }
        with self.assertRaises(NavigationError):
            validate_manifest_data(fake_data, self.repo_root)

    def test_root_readme_link_generation(self) -> None:
        """Verifies root README has English active (bold) and relative links to docs/i18n."""
        nav = generate_navigation_line("README.md", self.languages, self.repo_root)
        self.assertIn("**English**", nav)
        self.assertNotIn("[English]", nav)
        self.assertIn("[Español](docs/i18n/README.es.md)", nav)
        self.assertIn("[Italiano](docs/i18n/README.it.md)", nav)
        self.assertIn("[Русский](docs/i18n/README.ru.md)", nav)

    def test_nested_i18n_readme_link_generation(self) -> None:
        """Verifies docs/i18n/ READMEs link to English at ../../README.md and siblings at README.<lang>.md."""
        # Italian README
        it_nav = generate_navigation_line("docs/i18n/README.it.md", self.languages, self.repo_root)
        self.assertIn("[English](../../README.md)", it_nav)
        self.assertIn("[Español](README.es.md)", it_nav)
        self.assertIn("**Italiano**", it_nav)
        self.assertNotIn("[Italiano]", it_nav)
        self.assertIn("[日本語](README.ja.md)", it_nav)

        # Spanish README
        es_nav = generate_navigation_line("docs/i18n/README.es.md", self.languages, self.repo_root)
        self.assertIn("[English](../../README.md)", es_nav)
        self.assertIn("**Español**", es_nav)
        self.assertNotIn("[Español]", es_nav)
        self.assertIn("[Italiano](README.it.md)", es_nav)

    def test_docs_index_link_generation(self) -> None:
        """Verifies docs/README.md links to ../README.md for English and i18n/README.<lang>.md for others."""
        docs_nav = generate_navigation_line("docs/README.md", self.languages, self.repo_root)
        self.assertIn("[English](../README.md)", docs_nav)
        self.assertIn("[Español](i18n/README.es.md)", docs_nav)
        self.assertIn("[Italiano](i18n/README.it.md)", docs_nav)
        self.assertIn("[日本語](i18n/README.ja.md)", docs_nav)
        # None should be bold since docs/README.md is not a language README
        self.assertNotIn("**", docs_nav)

    def test_active_language_determination(self) -> None:
        """Tests active language code detection across various file paths."""
        self.assertEqual(determine_active_language("README.md", self.languages), "en")
        self.assertEqual(determine_active_language("docs/i18n/README.en.md", self.languages), "en")
        self.assertEqual(determine_active_language("docs/i18n/README.it.md", self.languages), "it")
        self.assertEqual(determine_active_language("docs/i18n/README.ja.md", self.languages), "ja")
        self.assertIsNone(determine_active_language("docs/README.md", self.languages))

    def test_unicode_native_labels_preserved(self) -> None:
        """Verifies that non-ASCII native language labels (CJK, Cyrillic, accented) are preserved."""
        nav = generate_navigation_line("README.md", self.languages, self.repo_root)
        self.assertIn("Español", nav)
        self.assertIn("Français", nav)
        self.assertIn("Português", nav)
        self.assertIn("日本語", nav)
        self.assertIn("한국어", nav)
        self.assertIn("简体中文", nav)
        self.assertIn("Русский", nav)

    def test_update_managed_region_success(self) -> None:
        """Verifies replacing content between markers leaves surrounding text untouched."""
        content = f"Header before\n\n{START_MARKER}\nOld Navigation\n{END_MARKER}\n\nFooter after"
        updated = update_managed_region(content, "New Navigation", "test.md")
        self.assertEqual(
            updated,
            f"Header before\n\n{START_MARKER}\nNew Navigation\n{END_MARKER}\n\nFooter after",
        )

    def test_malformed_markers_rejected(self) -> None:
        """Verifies that missing, inverted, or duplicate markers are rejected."""
        # Missing markers
        with self.assertRaises(NavigationError):
            update_managed_region("No markers here", "Nav", "test.md")

        # Inverted markers (END before START)
        with self.assertRaises(NavigationError):
            update_managed_region(f"{END_MARKER}\nNav\n{START_MARKER}", "Nav", "test.md")

        # Duplicate markers
        with self.assertRaises(NavigationError):
            update_managed_region(
                f"{START_MARKER}\nNav\n{END_MARKER}\n{START_MARKER}\nNav2\n{END_MARKER}",
                "Nav",
                "test.md",
            )

    def test_idempotent_and_deterministic_output(self) -> None:
        """Verifies that running generate_navigation_line multiple times yields identical strings."""
        for target in TARGET_DOCUMENTS:
            run1 = generate_navigation_line(target, self.languages, self.repo_root)
            run2 = generate_navigation_line(target, self.languages, self.repo_root)
            self.assertEqual(run1, run2)

    def test_check_mode_non_mutating(self) -> None:
        """Verifies that check mode detects sync status without modifying any files."""
        diff_count, diagnostics = process_documents(
            repo_root=self.repo_root,
            manifest_path=self.manifest_path,
            write=False,
        )
        self.assertEqual(diff_count, 0)
        for diag in diagnostics:
            self.assertTrue(diag.startswith("OK: "), f"Expected OK diagnostic, found: {diag}")


if __name__ == "__main__":
    unittest.main()
