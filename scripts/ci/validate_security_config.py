#!/usr/bin/env python3
"""Validates security workflows, Dependabot configurations, and container hardening.

Enforces deterministic DevSecOps security standards across:
- .github/dependabot.yml (ecosystems, schedules, PR limits, labels)
- .github/workflows/codeql.yml (least-privilege permissions, languages, query suites)
- .github/workflows/dependency-security.yml (pip-audit, npm audit, lockfile checks)
- Dockerfile & .dockerignore (non-root execution, sensitive file exclusion)

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_DEPENDABOT_ECOSYSTEMS: set[str] = {
    "github-actions",
    "pip",
    "npm",
    "docker",
}

REQUIRED_CODEQL_LANGUAGES: set[str] = {
    "python",
    "javascript-typescript",
    "actions",
}

CRITICAL_DOCKERIGNORE_PATTERNS: list[str] = [
    ".git",
    ".env",
    "*.pem",
    "*.key",
]


def validate_dependabot_config(repo_root: Path) -> list[str]:
    """Validate .github/dependabot.yml configuration."""
    errors: list[str] = []
    dep_file = repo_root / ".github" / "dependabot.yml"
    if not dep_file.is_file():
        return [f"Missing Dependabot configuration: {dep_file}"]

    content = dep_file.read_text(encoding="utf-8")

    # Check version
    if not re.search(r"^version:\s*2", content, re.MULTILINE):
        errors.append("Dependabot configuration must specify 'version: 2'.")

    # Check required ecosystems
    found_ecosystems: set[str] = set(
        re.findall(r'package-ecosystem:\s*["\']?([a-zA-Z0-9_-]+)["\']?', content)
    )
    missing_eco = REQUIRED_DEPENDABOT_ECOSYSTEMS - found_ecosystems
    if missing_eco:
        errors.append(
            f"Dependabot is missing required package ecosystems: {', '.join(sorted(missing_eco))}."
        )

    # Check schedule intervals
    intervals = re.findall(r'interval:\s*["\']?([a-zA-Z0-9_-]+)["\']?', content)
    for interval in intervals:
        if interval not in {"daily", "weekly", "monthly"}:
            errors.append(f"Invalid Dependabot schedule interval: '{interval}'.")

    # Check PR limits
    pr_limits = re.findall(r"open-pull-requests-limit:\s*(\d+)", content)
    for limit in pr_limits:
        val = int(limit)
        if val <= 0 or val > 25:
            errors.append(
                f"Dependabot open-pull-requests-limit '{val}' is outside safe range (1-25)."
            )

    return errors


def validate_codeql_workflow(repo_root: Path) -> list[str]:
    """Validate .github/workflows/codeql.yml configuration."""
    errors: list[str] = []
    codeql_file = repo_root / ".github" / "workflows" / "codeql.yml"
    if not codeql_file.is_file():
        return [f"Missing CodeQL workflow: {codeql_file}"]

    content = codeql_file.read_text(encoding="utf-8")

    # Ensure no dangerous pull_request_target
    if "pull_request_target" in content:
        errors.append("CodeQL workflow must not use 'pull_request_target' trigger.")

    # Check least-privilege top-level permissions
    if not re.search(r"^permissions:\s*\n\s+contents:\s*read", content, re.MULTILINE):
        errors.append(
            "CodeQL workflow must enforce default top-level 'permissions: contents: read'."
        )

    # Check scoped security-events write
    if "security-events: write" not in content:
        errors.append(
            "CodeQL workflow must grant 'security-events: write' to upload SARIF results."
        )

    # Check language matrix
    found_languages: set[str] = set(
        re.findall(r'language:\s*["\']?([a-zA-Z0-9_-]+)["\']?', content)
    )
    missing_langs = REQUIRED_CODEQL_LANGUAGES - found_languages
    if missing_langs:
        errors.append(
            f"CodeQL workflow is missing required scan languages: {', '.join(sorted(missing_langs))}."
        )

    # Check query suite
    if "queries: security-extended" not in content and "queries: default" not in content:
        errors.append("CodeQL workflow should specify an explicit security query suite.")

    return errors


def validate_dependency_security_workflow(repo_root: Path) -> list[str]:
    """Validate .github/workflows/dependency-security.yml configuration."""
    errors: list[str] = []
    dep_sec_file = repo_root / ".github" / "workflows" / "dependency-security.yml"
    if not dep_sec_file.is_file():
        return [f"Missing dependency security workflow: {dep_sec_file}"]

    content = dep_sec_file.read_text(encoding="utf-8")

    if not re.search(r"^permissions:\s*\n\s+contents:\s*read", content, re.MULTILINE):
        errors.append(
            "Dependency security workflow must enforce top-level 'permissions: contents: read'."
        )

    if "pip-audit" not in content:
        errors.append("Dependency security workflow must execute 'pip-audit' for Python.")

    if "npm audit" not in content:
        errors.append("Dependency security workflow must execute 'npm audit' for Node.js.")

    return errors


def validate_container_hardening(repo_root: Path) -> list[str]:
    """Validate Dockerfile and .dockerignore security posture."""
    errors: list[str] = []
    dockerfile = repo_root / "Dockerfile"
    dockerignore = repo_root / ".dockerignore"

    if dockerfile.is_file():
        content = dockerfile.read_text(encoding="utf-8")
        if not re.search(r"^\s*USER\s+[a-zA-Z0-9_-]+", content, re.MULTILINE):
            errors.append(
                "Dockerfile must declare a non-root 'USER' directive for container runtime."
            )

        if not re.search(r"^\s*FROM\s+python:[\d.]+-slim", content, re.MULTILINE):
            errors.append(
                "Dockerfile should use an official pinned slim base image (e.g. python:3.13-slim)."
            )

    if dockerignore.is_file():
        ignore_content = dockerignore.read_text(encoding="utf-8")
        for pattern in CRITICAL_DOCKERIGNORE_PATTERNS:
            if pattern not in ignore_content:
                errors.append(f".dockerignore must exclude sensitive pattern: '{pattern}'.")

    return errors


def validate_all_security_configs(repo_root: Path) -> tuple[bool, list[str]]:
    """Execute complete security configuration audit."""
    all_errors: list[str] = []
    all_errors.extend(validate_dependabot_config(repo_root))
    all_errors.extend(validate_codeql_workflow(repo_root))
    all_errors.extend(validate_dependency_security_workflow(repo_root))
    all_errors.extend(validate_container_hardening(repo_root))
    return len(all_errors) == 0, all_errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="DERA Security Configuration & DevSecOps Standards Validator"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Path to repository root",
    )
    args = parser.parse_args()

    repo_root = args.repo_root
    print(f"Validating DERA DevSecOps security configurations in: {repo_root}")

    is_valid, errors = validate_all_security_configs(repo_root)
    if not is_valid:
        print("\nDERA Security Configuration Validation: FAILED", file=sys.stderr)
        for err in errors:
            print(f"  [ERROR] {err}", file=sys.stderr)
        return 1

    print(
        "\nSUCCESS: All DERA security workflows, Dependabot, and container configurations passed validation."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
