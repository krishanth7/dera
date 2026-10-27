"""Regression tests for GitHub Actions security workflows and container hardening.

Validates that CodeQL, dependency security, and Docker configurations
comply strictly with DERA's DevSecOps security invariants.

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from scripts.ci.validate_security_config import (
    validate_codeql_workflow,
    validate_container_hardening,
    validate_dependency_security_workflow,
)


class TestSecurityWorkflows(unittest.TestCase):
    """Verify security workflow structures and least-privilege configurations."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[2]
        cls.workflows_dir = cls.repo_root / ".github" / "workflows"

    def test_codeql_workflow_validity(self) -> None:
        """Verify CodeQL workflow configuration passes all deterministic checks."""
        errors = validate_codeql_workflow(self.repo_root)
        self.assertEqual(errors, [], f"CodeQL workflow validation failed: {errors}")

    def test_dependency_security_workflow_validity(self) -> None:
        """Verify dependency security workflow configuration passes all checks."""
        errors = validate_dependency_security_workflow(self.repo_root)
        self.assertEqual(errors, [], f"Dependency security workflow validation failed: {errors}")

    def test_container_hardening_validity(self) -> None:
        """Verify Dockerfile and .dockerignore adhere to container security rules."""
        errors = validate_container_hardening(self.repo_root)
        self.assertEqual(errors, [], f"Container hardening validation failed: {errors}")

    def test_no_pull_request_target_in_any_workflow(self) -> None:
        """Verify pull_request_target is never used across any repository workflow."""
        for yml_path in self.workflows_dir.glob("*.yml"):
            content = yml_path.read_text(encoding="utf-8")
            with self.subTest(workflow=yml_path.name):
                self.assertNotIn(
                    "pull_request_target",
                    content,
                    f"Workflow '{yml_path.name}' must not use untrusted 'pull_request_target'.",
                )

    def test_all_workflows_enforce_explicit_permissions(self) -> None:
        """Verify all workflows declare explicit top-level permissions."""
        for yml_path in self.workflows_dir.glob("*.yml"):
            content = yml_path.read_text(encoding="utf-8")
            with self.subTest(workflow=yml_path.name):
                has_permissions = bool(re.search(r"^permissions:", content, re.MULTILINE))
                self.assertTrue(
                    has_permissions,
                    f"Workflow '{yml_path.name}' must declare explicit top-level 'permissions:'.",
                )

    def test_no_inline_untrusted_shell_interpolation(self) -> None:
        """Verify pull request title or body are never directly interpolated into bash run scripts."""
        untrusted_patterns = [
            r"\$\{\{\s*github\.event\.pull_request\.title\s*\}\}",
            r"\$\{\{\s*github\.event\.pull_request\.body\s*\}\}",
        ]
        for yml_path in self.workflows_dir.glob("*.yml"):
            content = yml_path.read_text(encoding="utf-8")
            # Look inside run: sections for unsafe direct expressions
            run_blocks = re.findall(
                r"run:\s*\|?\s*\n(.*?)(?=\n\s*(?:-|\w+:|$))", content, re.DOTALL
            )
            for block in run_blocks:
                for pat in untrusted_patterns:
                    with self.subTest(workflow=yml_path.name, pattern=pat):
                        self.assertFalse(
                            re.search(pat, block),
                            f"Workflow '{yml_path.name}' evaluates untrusted PR text directly in run: script.",
                        )


if __name__ == "__main__":
    unittest.main()
