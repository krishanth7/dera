# ============================================================
# DERA — Database Engineering & Reverse Analysis
# Unit Tests: PR Readiness Validation
# ============================================================

from __future__ import annotations

import os
import unittest
from unittest import mock

from scripts.ci.validate_pr_readiness import check_readiness


class TestValidatePrReadiness(unittest.TestCase):
    """Test suite for PR readiness and author declaration verification."""

    def test_draft_pr_bypasses_readiness(self) -> None:
        env = {
            "PR_TITLE": "feat(core): work in progress",
            "PR_BODY": "",
            "PR_DRAFT": "true",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            is_ready, errors = check_readiness()
            self.assertTrue(is_ready)
            self.assertEqual(errors, [])

    def test_bot_pr_bypasses_readiness(self) -> None:
        env = {
            "PR_TITLE": "bump actions/setup-python from 4 to 5",
            "PR_BODY": "Bumps actions/setup-python.",
            "PR_DRAFT": "false",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            is_ready, errors = check_readiness()
            self.assertTrue(is_ready)
            self.assertEqual(errors, [])

    def test_empty_pr_body_rejected(self) -> None:
        env = {
            "PR_TITLE": "feat(core): introduce schema models",
            "PR_BODY": "",
            "PR_DRAFT": "false",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            is_ready, errors = check_readiness()
            self.assertFalse(is_ready)
            self.assertIn("PR body is empty. Please provide a description of your changes.", errors)

    def test_short_pr_body_rejected(self) -> None:
        env = {
            "PR_TITLE": "feat(core): introduce schema models",
            "PR_BODY": "Too short.",
            "PR_DRAFT": "false",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            is_ready, errors = check_readiness()
            self.assertFalse(is_ready)
            self.assertTrue(any("too short" in err for err in errors))

    def test_pr_body_missing_summary_or_testing_rejected(self) -> None:
        env = {
            "PR_TITLE": "feat(core): introduce schema models",
            "PR_BODY": "I implemented some cool changes to improve performance across the system, please review and merge.",
            "PR_DRAFT": "false",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            is_ready, errors = check_readiness()
            self.assertFalse(is_ready)
            self.assertTrue(any("Summary" in err for err in errors))

    def test_valid_pr_body_with_checklist(self) -> None:
        body = """
## Summary
Introduced canonical schema models and exceptions for DERA core engine.

## Testing
- [x] Ran unit tests via python scripts/development/dev.py test
- [x] Ran static type checks
"""
        env = {
            "PR_TITLE": "feat(core): introduce schema models",
            "PR_BODY": body,
            "PR_DRAFT": "false",
            "PR_LABELS": "",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            is_ready, errors = check_readiness()
            self.assertTrue(is_ready, f"Expected valid body to pass, but got: {errors}")
            self.assertEqual(errors, [])

    def test_security_labeled_pr_requires_security_disclosure(self) -> None:
        body_without_sec = """
## Summary
Changed API host configuration and token handling.

## Testing
- [x] Tested locally with pytest
"""
        env = {
            "PR_TITLE": "security(api): restrict unauthorized metadata access",
            "PR_BODY": body_without_sec,
            "PR_DRAFT": "false",
            "PR_LABELS": "security",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            is_ready, errors = check_readiness()
            self.assertFalse(is_ready)
            self.assertTrue(any("Security Assessment" in err for err in errors))

    def test_security_labeled_pr_with_disclosure_passes(self) -> None:
        body_with_sec = """
## Summary
Enforced loopback host address default in API configuration.

## Testing
- [x] Tested locally with dev.py all

## Security Assessment
Confirmed that API binds only to 127.0.0.1 by default, preventing unintended network exposure.
"""
        env = {
            "PR_TITLE": "security(api): enforce loopback address default",
            "PR_BODY": body_with_sec,
            "PR_DRAFT": "false",
            "PR_LABELS": "security",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            is_ready, errors = check_readiness()
            self.assertTrue(is_ready, f"Expected security disclosure to pass, but got: {errors}")
            self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
