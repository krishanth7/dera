"""Regression tests for Dependabot automated update configuration.

Verifies that .github/dependabot.yml covers all active ecosystems,
enforces manageable PR limits, and maintains Conventional Commit prefixes.

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.ci.validate_security_config import (
    REQUIRED_DEPENDABOT_ECOSYSTEMS,
    validate_dependabot_config,
)


class TestDependabotConfig(unittest.TestCase):
    """Test suite for Dependabot configuration integrity."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[2]
        cls.dependabot_path = cls.repo_root / ".github" / "dependabot.yml"

    def test_dependabot_file_exists(self) -> None:
        """Verify .github/dependabot.yml exists."""
        self.assertTrue(self.dependabot_path.is_file(), "Missing .github/dependabot.yml")

    def test_dependabot_validation_passes(self) -> None:
        """Verify complete Dependabot validation passes with zero errors."""
        errors = validate_dependabot_config(self.repo_root)
        self.assertEqual(errors, [], f"Dependabot configuration errors: {errors}")

    def test_all_required_ecosystems_present(self) -> None:
        """Verify github-actions, pip, npm, and docker ecosystems are all defined."""
        content = self.dependabot_path.read_text(encoding="utf-8")
        for eco in REQUIRED_DEPENDABOT_ECOSYSTEMS:
            with self.subTest(ecosystem=eco):
                self.assertIn(
                    f'package-ecosystem: "{eco}"',
                    content,
                    f"Required ecosystem '{eco}' not found in dependabot.yml",
                )


if __name__ == "__main__":
    unittest.main()
