#!/usr/bin/env python3
"""Validates pull request readiness, description completeness, and security disclosures.

Reads PR metadata from environment variables passed securely from GitHub Actions:
- PR_TITLE
- PR_BODY
- PR_AUTHOR
- PR_DRAFT
- PR_LABELS

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import os
import sys

REQUIRED_HEADINGS = [
    "summary",
    "testing",
]

def check_readiness() -> tuple[bool, list[str]]:
    title = os.environ.get("PR_TITLE", "").strip()
    body = os.environ.get("PR_BODY", "").strip()
    is_draft = os.environ.get("PR_DRAFT", "false").lower() == "true"
    labels_raw = os.environ.get("PR_LABELS", "")

    errors: list[str] = []

    if is_draft:
        print("INFO: PR is marked as draft; skipping blocking readiness checks.")
        return True, []

    # Exclude automated Dependabot PRs
    if "dependabot" in title.lower() or "bump " in title.lower():
        print("INFO: Automated bot PR detected; passing readiness automatically.")
        return True, []

    if not body:
        errors.append("PR body is empty. Please provide a description of your changes.")
        return False, errors

    body_lower = body.lower()

    # Check for meaningful content length
    if len(body) < 30:
        errors.append("PR description is too short (less than 30 characters). Please explain your changes.")

    # Check for checklist completion or key sections
    has_checklist = "- [x]" in body or "- [X]" in body
    has_summary = any(h in body_lower for h in ["summary", "description", "motivation", "overview"])
    has_testing = any(t in body_lower for t in ["test", "testing", "verification", "verified"])

    if not (has_checklist or (has_summary and has_testing)):
        errors.append(
            "PR description should include a change Summary and a Testing/verification explanation or completed checklist items."
        )

    # Check for security disclosures on security-labeled or API-touching PRs
    if "security" in title.lower() or "security" in labels_raw.lower():
        if "security" not in body_lower:
            errors.append("PR modifying security-sensitive components must include a Security Assessment note.")

    return len(errors) == 0, errors


def main() -> int:
    is_ready, errors = check_readiness()
    if not is_ready:
        print("PR Readiness Validation FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("PR Readiness Validation PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
