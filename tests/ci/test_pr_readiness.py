# ============================================================
# DERA — Database Engineering & Reverse Analysis
# Regression Tests: Pull Request Readiness Validation
# ============================================================

from __future__ import annotations

import unittest

from scripts.ci.validate_pr_readiness import (
    check_readiness,
    strip_template_boilerplate,
)


class TestPrReadinessRegression(unittest.TestCase):
    """Exhaustive regression test suite for PR readiness and author declaration checks."""

    def test_strip_template_boilerplate(self) -> None:
        """Verify HTML comments and standard headers are stripped to reveal real content."""
        template_text = """
## Summary
<!-- Describe change here -->
This is an actual user typed description explaining the schema migration.

## Testing
<!-- Provide test evidence -->
- [x] Relevant tests passed
"""
        stripped = strip_template_boilerplate(template_text)
        self.assertIn("This is an actual user typed description", stripped)
        self.assertNotIn("<!-- Describe change here -->", stripped)
        self.assertNotIn("## Summary", stripped)

    def test_draft_pr_is_non_blocking(self) -> None:
        """Verify draft PRs receive advisory messages but do not fail CI."""
        is_ready, errors = check_readiness(
            title="feat(core): work in progress schema parser",
            body="",
            is_draft=True,
            author="contributor",
        )
        self.assertTrue(is_ready, "Draft PR should not be blocked.")
        self.assertEqual(errors, [])

    def test_ready_pr_with_empty_body_fails(self) -> None:
        """Verify ready-for-review PR with empty body fails."""
        is_ready, errors = check_readiness(
            title="feat(core): add schema models",
            body="",
            is_draft=False,
            author="contributor",
        )
        self.assertFalse(is_ready)
        self.assertTrue(any("empty" in e.lower() for e in errors))

    def test_ready_pr_with_untouched_template_fails(self) -> None:
        """Verify PR body containing only untouched template comments fails."""
        untouched_body = """
## Summary
<!-- Briefly describe the purpose, motivation, and context of this pull request. -->

## Change Type
- [ ] Feature (`feat`)

## Testing
<!-- Describe the verification steps taken. -->
- [ ] Relevant tests passed
"""
        is_ready, errors = check_readiness(
            title="feat(core): add schema models",
            body=untouched_body,
            is_draft=False,
            author="contributor",
        )
        self.assertFalse(is_ready)
        self.assertTrue(any("too short" in e.lower() for e in errors))

    def test_valid_standard_pr_body_passes(self) -> None:
        """Verify standard complete PR body passes."""
        body = """
## Summary
Implements deterministic SQLite catalog inspection for column types, nullability,
and foreign key constraints within the DERA core connector framework.

## Testing
- [x] Relevant tests passed (`python scripts/development/dev.py all`)
**Test evidence:** Ran unittest discover tests/, all 64 tests passed cleanly.

## Documentation Impact
- [x] Documentation in `docs/` updated or verified where required
- [x] Documentation validation passed (`npm run docs:check`)

## Security Impact & Deterministic Engineering
- [x] **Strict Non-AI Policy:** Verified zero generative AI, LLM, or external inference APIs are introduced.
- [x] **Database Safety:** Verified all database connector operations enforce read-only introspection without data modification.
"""
        is_ready, errors = check_readiness(
            title="feat(connectors): add SQLite metadata inspection",
            body=body,
            is_draft=False,
            author="contributor",
        )
        self.assertTrue(is_ready, f"Expected standard PR to pass, got: {errors}")
        self.assertEqual(errors, [])

    def test_alternative_testing_state_not_applicable_passes(self) -> None:
        """Verify 'Tests not applicable' with explanation passes for non-code PRs."""
        doc_body = """
## Summary
Updated documentation for internationalization guides and added technical notes on
canonical schemas across all ten supported languages.

## Testing
- [x] Tests not applicable — explanation below
**Test evidence:** This pull request modifies only markdown documentation files in `docs/`. Executable code tests are not applicable. Verified doc integrity via `npm run docs:check`.

## Documentation Impact
- [x] Documentation in `docs/` updated or verified where required
"""
        is_ready, errors = check_readiness(
            title="docs(i18n): update internationalization guides",
            body=doc_body,
            is_draft=False,
            author="contributor",
        )
        self.assertTrue(is_ready, f"Expected 'tests not applicable' to pass, got: {errors}")
        self.assertEqual(errors, [])

    def test_alternative_testing_state_not_run_with_explanation_passes(self) -> None:
        """Verify 'Tests not run / blocked' with explanation passes."""
        blocked_body = """
## Summary
Refactored Docker container configuration to prepare for non-root execution.

## Testing
- [x] Tests not run — explanation below
**Test evidence & notes:** Local docker daemon was not accessible on development machine; relying on GitHub Actions container build workflow.

## Documentation Impact
- [x] No documentation updates required for this change
"""
        is_ready, errors = check_readiness(
            title="build(docker): update container build arguments",
            body=blocked_body,
            is_draft=False,
            author="contributor",
        )
        self.assertTrue(is_ready, f"Expected 'tests not run' to pass, got: {errors}")
        self.assertEqual(errors, [])

    def test_security_labeled_pr_without_assessment_fails(self) -> None:
        """Verify PR modifying security components or labeled 'security' requires assessment."""
        body = """
## Summary
Changed API host address binding and updated configuration tokens for the server.

## Testing
- [x] Relevant tests passed
"""
        is_ready, errors = check_readiness(
            title="security(api): restrict unauthorized host interface binding",
            body=body,
            is_draft=False,
            author="contributor",
            labels="security",
        )
        self.assertFalse(is_ready)
        self.assertTrue(any("Security Assessment" in e for e in errors))

    def test_security_labeled_pr_with_assessment_passes(self) -> None:
        """Verify security PR with assessment note passes."""
        body = """
## Summary
Changed API host address binding to ensure default binds to loopback only.

## Testing
- [x] Relevant tests passed

## Security Impact
Security Assessment: Confirmed API binds strictly to 127.0.0.1, preventing network eavesdropping.
"""
        is_ready, errors = check_readiness(
            title="security(api): enforce loopback binding default",
            body=body,
            is_draft=False,
            author="contributor",
            labels="security",
        )
        self.assertTrue(is_ready, f"Expected security assessment to pass, got: {errors}")
        self.assertEqual(errors, [])

    def test_breaking_change_without_details_fails(self) -> None:
        """Verify PR with '!' in title requires breaking change explanation in body."""
        body = """
## Summary
Changed return type and payload structure of schema models in API gateway.

## Testing
- [x] Relevant tests passed

## Breaking Changes
- [x] No breaking changes.
"""
        is_ready, errors = check_readiness(
            title="feat(api)!: alter schema snapshot response payload",
            body=body,
            is_draft=False,
            author="contributor",
        )
        self.assertFalse(is_ready)
        self.assertTrue(any("breaking change" in e.lower() for e in errors))

    def test_breaking_change_with_migration_passes(self) -> None:
        """Verify breaking change PR with proper declaration passes."""
        body = """
## Summary
Altered the schema snapshot JSON representation to use snake_case properties consistently.

## Testing
- [x] Relevant tests passed

## Breaking Changes
- [x] Breaking change introduced
**Migration path:** Clients must update JSON key references from `tableName` to `table_name`.
"""
        is_ready, errors = check_readiness(
            title="feat(api)!: alter schema snapshot response payload",
            body=body,
            is_draft=False,
            author="contributor",
        )
        self.assertTrue(is_ready, f"Expected breaking change declaration to pass, got: {errors}")
        self.assertEqual(errors, [])

    def test_bot_pr_automatic_bypass(self) -> None:
        """Verify automated bot PRs bypass blocking checks."""
        is_ready, errors = check_readiness(
            title="bump actions/setup-python from 4 to 5",
            body="Bumps actions/setup-python from 4 to 5.",
            is_draft=False,
            author="dependabot[bot]",
        )
        self.assertTrue(is_ready)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
