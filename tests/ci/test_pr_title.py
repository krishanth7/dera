# ============================================================
# DERA — Database Engineering & Reverse Analysis
# Regression Tests: Conventional Commit PR Title Validation
# ============================================================

from __future__ import annotations

import unittest

from scripts.ci.validate_pr_title import (
    ALLOWED_TYPES,
    CANONICAL_SCOPES,
    is_bot_title,
    parse_title,
    validate_title,
)


class TestPrTitleRegression(unittest.TestCase):
    """Exhaustive regression test suite for Conventional Commit title parsing."""

    def test_all_canonical_types(self) -> None:
        """Verify each approved Conventional Commit type is valid."""
        for c_type in ALLOWED_TYPES:
            title = f"{c_type}(core): implement deterministic feature"
            with self.subTest(c_type=c_type):
                self.assertTrue(validate_title(title), f"Type '{c_type}' should be valid.")

    def test_all_canonical_scopes(self) -> None:
        """Verify each canonical scope is recognized and approved."""
        for scope in CANONICAL_SCOPES:
            title = f"feat({scope}): valid scope test"
            with self.subTest(scope=scope):
                self.assertTrue(validate_title(title), f"Scope '{scope}' should be valid.")

    def test_optional_scope_omission(self) -> None:
        """Verify titles without a scope are completely valid."""
        titles = [
            "feat: add database schema parser",
            "fix: correct circular dependency in graph resolution",
            "docs: update architecture guidelines",
            "chore: clean temporary test artifacts",
        ]
        for title in titles:
            with self.subTest(title=title):
                self.assertTrue(validate_title(title))

    def test_breaking_change_markers(self) -> None:
        """Verify breaking change marker '!' works with and without scope."""
        breaking_titles = [
            "feat(api)!: alter schema snapshot response payload",
            "fix(core)!: change exception hierarchy for cycle errors",
            "feat!: redesign top-level CLI interface",
            "refactor(connectors)!: require explicit read-only transactions",
        ]
        for title in breaking_titles:
            with self.subTest(title=title):
                is_valid, parsed, errors = parse_title(title)
                self.assertTrue(is_valid, f"Expected breaking title '{title}' to be valid.")
                assert parsed is not None
                self.assertTrue(parsed.is_breaking)

    def test_compound_and_subscopes(self) -> None:
        """Verify hierarchical and compound scopes."""
        compound_titles = [
            "feat(connectors/postgres): add partition table inspection",
            "feat(connectors/sqlite): support in-memory URI",
            "chore(deps,npm): bump frontend dev dependencies",
            "ci(actions)(deps): bump workflow actions",
            "fix(core.models): prevent mutable column default",
        ]
        for title in compound_titles:
            with self.subTest(title=title):
                self.assertTrue(validate_title(title))

    def test_unicode_and_multilingual_descriptions(self) -> None:
        """Verify Unicode, accents, and non-ASCII character handling."""
        unicode_titles = [
            "docs(i18n): synchronize documentation in 日本語 and 한국어",
            "docs(i18n): update README in Español and Français",
            "fix(core): preserve UTF-8 identifiers in «table_log»",
            "feat(connectors): support German umlauts (München_schema)",
        ]
        for title in unicode_titles:
            with self.subTest(title=title):
                self.assertTrue(validate_title(title))

    def test_very_long_technical_title(self) -> None:
        """Verify long informative titles are not rejected by an arbitrary low limit."""
        long_title = (
            "feat(connectors): implement comprehensive foreign key constraint extraction "
            "with composite primary key resolution and reverse dependency graph construction"
        )
        self.assertGreater(len(long_title), 120)
        self.assertTrue(validate_title(long_title))

    def test_shell_metacharacters_safety(self) -> None:
        """Verify titles containing shell metacharacters parse deterministically without error."""
        shell_titles = [
            "fix(api): escape '$' in environment variable resolution",
            "feat(core): support identifiers with quotes \"users_table\" and 'orders'",
            "fix(cli): handle pipe '|' and semicolon ';' in raw query strings",
            "docs: document `<DatabaseTable>` and `SchemaSnapshot` generic types",
        ]
        for title in shell_titles:
            with self.subTest(title=title):
                self.assertTrue(validate_title(title))

    def test_markdown_and_html_injection_like_titles(self) -> None:
        """Verify Markdown/HTML syntax in title is parsed safely."""
        injection_titles = [
            "docs: link to [PEP 8](https://peps.python.org/pep-0008/) style guide",
            "fix(web): render `<code>` tags inside component canvas",
            "chore: remove <!-- old comments --> from template",
        ]
        for title in injection_titles:
            with self.subTest(title=title):
                self.assertTrue(validate_title(title))

    def test_bot_pr_titles(self) -> None:
        """Verify automated bot PR titles pass seamlessly."""
        bot_titles = [
            "bump actions/setup-python from 4 to 5",
            "Dependabot: bump typescript from 5.9.3 to 7.0.2 in /apps/web",
            "chore(deps): bump the npm-dependencies group across 1 directory",
        ]
        for title in bot_titles:
            with self.subTest(title=title):
                self.assertTrue(validate_title(title))
                self.assertTrue(is_bot_title(title) or validate_title(title))

    def test_invalid_titles_rejected(self) -> None:
        """Verify invalid, malformed, or untyped titles are rejected with clear diagnostics."""
        invalid_cases = [
            ("", "empty"),
            ("   ", "whitespace"),
            ("Update README.md", "no type"),
            ("Fixing bug in connector", "gerund no type"),
            ("feat", "no colon"),
            ("feat:", "no space or description"),
            ("feat: ", "no description"),
            ("feat: a", "description too short"),
            ("feat(core):", "empty description"),
            ("FEAT(core): uppercase type", "uppercase type"),
            ("unknown(core): invalid type", "unknown type"),
            ("feat(randomxyz): unrecognized scope", "unrecognized scope"),
            ("feat(core) missing colon: description", "malformed syntax"),
        ]
        for title, reason in invalid_cases:
            with self.subTest(reason=reason, title=title):
                is_valid, _, errors = parse_title(title)
                self.assertFalse(is_valid, f"Expected '{title}' to fail for reason: {reason}")
                self.assertGreater(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
