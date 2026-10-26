# ============================================================
# DERA — Database Engineering & Reverse Analysis
# Unit Tests: Conventional Commit & PR Title Validation
# ============================================================

from __future__ import annotations

import unittest

from scripts.ci.validate_pr_title import is_bot_title, validate_title


class TestValidatePrTitle(unittest.TestCase):
    """Test suite for Conventional Commits PR title validation logic."""

    def test_valid_standard_types(self) -> None:
        valid_titles = [
            "feat(connectors): add SQLite metadata support",
            "fix(graph): correct circular foreign-key resolution",
            "docs(architecture): document monorepo module boundaries",
            "refactor(core): simplify schema model definitions",
            "perf(erd): optimize foreign key lookup performance",
            "test(api): add health endpoint verification tests",
            "build(python): configure packaging metadata",
            "ci(github): add PR title validation check",
            "chore(repo): update development tooling configuration",
            "revert(core): revert previous snapshot hashing change",
            "security(api): enforce loopback address default",
            "deps(npm): update typescript compiler dependency",
        ]
        for title in valid_titles:
            with self.subTest(title=title):
                self.assertTrue(validate_title(title), f"Expected '{title}' to be valid.")

    def test_valid_without_scope(self) -> None:
        valid_titles = [
            "feat: introduce canonical database schemas",
            "fix: correct composite index parsing bug",
            "docs: update installation instructions",
            "chore: clean up temporary build artifacts",
        ]
        for title in valid_titles:
            with self.subTest(title=title):
                self.assertTrue(validate_title(title), f"Expected '{title}' to be valid.")

    def test_breaking_change_indicators(self) -> None:
        valid_titles = [
            "feat(api)!: revise schema response data contract",
            "feat!: redesign connector interface hierarchy",
            "refactor(core)!: drop deprecated snapshot format",
        ]
        for title in valid_titles:
            with self.subTest(title=title):
                self.assertTrue(validate_title(title), f"Expected '{title}' to be valid.")

    def test_multi_scope_and_characters(self) -> None:
        valid_titles = [
            "ci(actions)(deps): bump github actions to latest",
            "chore(deps,npm): update packages and locks",
            "feat(connectors/postgres): add partition detection",
            "fix(core.models): handle None schema names",
        ]
        for title in valid_titles:
            with self.subTest(title=title):
                self.assertTrue(validate_title(title), f"Expected '{title}' to be valid.")

    def test_bot_titles_accepted(self) -> None:
        bot_titles = [
            "bump the actions group with 7 updates",
            "Dependabot: bump typescript from 5.9.3 to 7.0.2",
            "ci(deps): bump actions/setup-python from 4 to 5",
        ]
        for title in bot_titles:
            with self.subTest(title=title):
                self.assertTrue(validate_title(title), f"Expected bot title '{title}' to pass.")

    def test_invalid_titles_rejected(self) -> None:
        invalid_titles = [
            "",
            "   ",
            "Update readme",
            "Fixing bug in connector",
            "My great PR",
            "feat",
            "feat:",
            "feat: ",
            "feat:   ",
            "feat(core)",
            "feat(core):",
            "feat(core): ",
            "FEAT(core): uppercase type is not allowed",
            "unknown(core): invalid type name",
            "random: arbitrary prefix",
            "feat(core) missing colon space",
        ]
        for title in invalid_titles:
            with self.subTest(title=title):
                self.assertFalse(validate_title(title), f"Expected '{title}' to be rejected.")

    def test_is_bot_title_helper(self) -> None:
        self.assertTrue(is_bot_title("bump actions/checkout from 3 to 4"))
        self.assertTrue(is_bot_title("dependabot[bot]: update deps"))
        self.assertFalse(is_bot_title("feat(core): standard human commit"))


if __name__ == "__main__":
    unittest.main()
