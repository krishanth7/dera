#!/usr/bin/env python3
"""Validates pull request readiness, description completeness, and declarations.

Reads PR metadata from environment variables or CLI flags:
- PR_TITLE / --title
- PR_BODY / --body
- PR_AUTHOR / --author
- PR_DRAFT / --draft
- PR_LABELS / --labels

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

TEMPLATE_HEADER_PATTERN = re.compile(
    r"^##\s+(?:Summary|Change Type|Related Issues|Implementation Details|Testing(?: Performed)?|"
    r"Documentation Impact|Security Impact.*|Breaking Changes|Contributor Checklist)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

<<<<<<< HEAD
HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)


def strip_template_boilerplate(text: str) -> str:
    """Strip HTML comments, standard markdown template headers, and unchecked template lines."""
    no_comments = HTML_COMMENT_PATTERN.sub("", text)
    no_headers = TEMPLATE_HEADER_PATTERN.sub("", no_comments)
    # Strip untouched/unchecked checkbox lines from template
    no_unchecked = re.sub(r"^[ \t]*-[ \t]*\[ \].*$", "", no_headers, flags=re.MULTILINE)
    return no_unchecked.strip()


def is_bot_pr(title: str, author: str) -> bool:
    """Detect automated bot PRs (Dependabot, pre-commit-ci, etc.)."""
    t_clean = title.strip().lower()
    a_clean = author.strip().lower()
    return "dependabot" in t_clean or "bump " in t_clean or "dependabot" in a_clean


def check_readiness(
    title: str | None = None,
    body: str | None = None,
    is_draft: bool | None = None,
    author: str | None = None,
    labels: str | None = None,
) -> tuple[bool, list[str]]:
    """Evaluate PR readiness criteria."""
    if title is None:
        title = os.environ.get("PR_TITLE", "").strip()
    if body is None:
        body = os.environ.get("PR_BODY", "").strip()
    if is_draft is None:
        is_draft = os.environ.get("PR_DRAFT", "false").lower() == "true"
    if author is None:
        author = os.environ.get("PR_AUTHOR", "").strip()
    if labels is None:
        labels = os.environ.get("PR_LABELS", "").strip()
=======

def check_readiness() -> tuple[bool, list[str]]:
    title = os.environ.get("PR_TITLE", "").strip()
    body = os.environ.get("PR_BODY", "").strip()
    is_draft = os.environ.get("PR_DRAFT", "false").lower() == "true"
    labels_raw = os.environ.get("PR_LABELS", "")
>>>>>>> origin/main

    errors: list[str] = []

    # 1. Automated Bot PR Bypass
    if is_bot_pr(title, author):
        print("INFO: Automated bot PR detected; passing readiness automatically.")
        return True, []

    # 2. Draft PR Handling
    if is_draft:
        print("INFO: PR is marked as draft; non-blocking advisory evaluation.")

    # 3. Non-Empty Body Check
    raw_body = body.strip()
    if not raw_body:
        errors.append("PR body is empty. Please provide a description of your changes.")
        if is_draft:
            print("ADVISORY: PR body is currently empty. Populate before marking ready for review.")
            return True, []
        return False, errors

    # 4. User Substance Check (stripping comments and template headers)
    user_content = strip_template_boilerplate(raw_body)
    # Exclude markdown checkboxes like "- [ ] " or "- [x] " to ensure typed narrative
    stripped_checkboxes = re.sub(r"-\s*\[[ xX]\]", "", user_content).strip()

    if len(stripped_checkboxes) < 30:
        errors.append(
            "PR description is too short (less than 30 characters of typed explanation). "
            "Please describe the purpose and context of your change."
        )

    body_lower = raw_body.lower()

    # 5. Summary / Motivation Section
    has_summary = any(k in body_lower for k in ["summary", "description", "motivation", "overview"])
    if not has_summary:
        errors.append("PR description must include a '## Summary' or '## Motivation' section.")

    # 6. Testing Section & Status Declaration
    has_testing_section = any(
        k in body_lower for k in ["testing", "test evidence", "verification", "verified"]
    )
    has_test_checkbox = any(
        marker in raw_body
        for marker in [
            "- [x] Relevant tests passed",
            "- [X] Relevant tests passed",
            "- [x] Tests not applicable",
            "- [X] Tests not applicable",
            "- [x] Tests not run",
            "- [X] Tests not run",
            "- [x]",
            "- [X]",
        ]
    )

    if not (has_testing_section and (has_test_checkbox or "not applicable" in body_lower)):
        errors.append(
            "PR description must declare testing status (e.g. check a testing box or explain "
            "why tests are not applicable in '## Testing')."
        )

    # 7. Security Impact Declaration
    is_security_related = (
        "security" in title.lower()
        or "security" in labels.lower()
        or title.lower().startswith("security")
    )
    if is_security_related:
        has_security_note = "security" in body_lower and any(
            k in body_lower
            for k in ["assessment", "implication", "disclosure", "read-only", "non-ai", "safety"]
        )
        if not has_security_note:
            errors.append(
                "PR touching security-sensitive components or labeled 'security' must include a "
                "Security Assessment note in '## Security Impact'."
            )

    # 8. Breaking Change Alignment
    is_breaking_title = "!" in title.split(":")[0] if ":" in title else False
    if is_breaking_title:
        # Title declares breaking change, verify body acknowledges it
        has_breaking_decl = (
            "breaking change" in body_lower
            and "no breaking changes" not in stripped_checkboxes.lower()
            and any(
                marker in raw_body
                for marker in [
                    "- [x] Breaking change introduced",
                    "- [X] Breaking change introduced",
                    "migration",
                    "contract change",
                ]
            )
        )
        if not has_breaking_decl:
            errors.append(
                "PR title declares a breaking change ('!'), but the PR description does not "
                "detail the breaking change or migration path under '## Breaking Changes'."
            )

    if is_draft:
        if errors:
            print(f"ADVISORY: Found {len(errors)} item(s) to address before ready for review:")
            for err in errors:
                print(f"  - {err}")
        return True, []

    return len(errors) == 0, errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="DERA Pull Request Readiness & Author Declaration Validator"
    )
    parser.add_argument("--title", help="PR title string")
    parser.add_argument("--body", help="PR description body markdown")
    parser.add_argument("--draft", action="store_true", help="PR is a draft")
    parser.add_argument("--author", default="", help="PR author login")
    parser.add_argument("--labels", default="", help="Comma-separated PR labels")

    args = parser.parse_args()

    title = args.title if args.title is not None else os.environ.get("PR_TITLE", "")
    body = args.body if args.body is not None else os.environ.get("PR_BODY", "")
    is_draft = args.draft or (os.environ.get("PR_DRAFT", "false").lower() == "true")
    author = args.author or os.environ.get("PR_AUTHOR", "")
    labels = args.labels or os.environ.get("PR_LABELS", "")

    is_ready, errors = check_readiness(
        title=title,
        body=body,
        is_draft=is_draft,
        author=author,
        labels=labels,
    )

    if not is_ready:
        print("\nDERA PR Readiness Validation Status: FAILED", file=sys.stderr)
        print(
            "Please address the following items in your pull request description:", file=sys.stderr
        )
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        print(
            "\nTip: Refer to .github/PULL_REQUEST_TEMPLATE.md and docs/ci/PR_QUALIFICATION.md "
            "for recommended sections and checklist formats.",
            file=sys.stderr,
        )
        return 1

    print("SUCCESS: Pull Request Readiness Validation PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
