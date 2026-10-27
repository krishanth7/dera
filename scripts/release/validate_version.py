#!/usr/bin/env python3
"""DERA Semantic Versioning & Package Consistency Validator.

Enforces Semantic Versioning 2.0.0 compliance, validates pre-release
and release candidate identifiers, and ensures version synchronization across
monorepo workspaces (Python and TypeScript).

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import NamedTuple

# Semantic Versioning 2.0.0 official specification regex
SEMVER_REGEX = re.compile(
    r"^(?P<major>0|[1-9]\d*)\."
    r"(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

# Standard DERA release channels
ALLOWED_CHANNELS = ("alpha", "beta", "rc", "dev")

# Canonical files containing version declarations
VERSION_SOURCES = [
    {
        "path": "package.json",
        "type": "json",
        "field": "version",
        "description": "Root workspace package.json",
    },
    {
        "path": "packages/contracts/package.json",
        "type": "json",
        "field": "version",
        "description": "TypeScript contracts workspace package.json",
    },
    {
        "path": "packages/connectors/package.json",
        "type": "json",
        "field": "version",
        "description": "TypeScript connectors workspace package.json",
    },
    {
        "path": "pyproject.toml",
        "type": "toml",
        "field": "version",
        "description": "Python core build metadata (pyproject.toml)",
    },
    {
        "path": "packages/core/src/dera_core/__init__.py",
        "type": "python",
        "field": "__version__",
        "description": "Python dera_core package __init__.py",
    },
    {
        "path": "packages/core/src/dera/__init__.py",
        "type": "python",
        "field": "__version__",
        "description": "Python dera namespace package __init__.py",
    },
    {
        "path": "packages/connectors/src/dera_connectors/__init__.py",
        "type": "python",
        "field": "__version__",
        "description": "Python dera_connectors package __init__.py",
    },
]


class VersionComponents(NamedTuple):
    major: int
    minor: int
    patch: int
    prerelease: str | None
    buildmetadata: str | None
    raw: str


def parse_semver(version_str: str, allow_v_prefix: bool = False) -> VersionComponents:
    """Parse and validate a version string against SemVer 2.0.0.

    Raises:
        ValueError: If version does not strictly conform to SemVer 2.0.0.
    """
    clean_version = version_str.strip()
    if clean_version.startswith("v"):
        if not allow_v_prefix:
            raise ValueError(
                f"Invalid Semantic Version '{version_str}'. Semantic versions cannot include leading 'v' prefix. Use validate_release_tag() for Git tags."
            )
        clean_version = clean_version[1:]

    match = SEMVER_REGEX.match(clean_version)
    if not match:
        raise ValueError(
            f"Invalid Semantic Version '{version_str}'. Must follow SemVer 2.0.0 (MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD])."
        )

    return VersionComponents(
        major=int(match.group("major")),
        minor=int(match.group("minor")),
        patch=int(match.group("patch")),
        prerelease=match.group("prerelease"),
        buildmetadata=match.group("buildmetadata"),
        raw=clean_version,
    )


def normalize_pep440_to_semver(pep_version: str) -> str:
    """Convert standard PEP 440 version strings to SemVer 2.0.0 for comparison.

    Examples:
        0.1.0.dev1 -> 0.1.0-dev
        0.1.0a1    -> 0.1.0-alpha.1
        0.1.0b1    -> 0.1.0-beta.1
        0.1.0rc1   -> 0.1.0-rc.1
        0.1.0      -> 0.1.0
    """
    v = pep_version.strip()
    # Handle dev releases: 0.1.0.dev1 -> 0.1.0-dev
    dev_match = re.match(r"^(\d+\.\d+\.\d+)\.dev\d*$", v)
    if dev_match:
        return f"{dev_match.group(1)}-dev"

    # Handle alpha: 0.1.0a1 -> 0.1.0-alpha.1
    alpha_match = re.match(r"^(\d+\.\d+\.\d+)a(\d+)$", v)
    if alpha_match:
        return f"{alpha_match.group(1)}-alpha.{alpha_match.group(2)}"

    # Handle beta: 0.1.0b1 -> 0.1.0-beta.1
    beta_match = re.match(r"^(\d+\.\d+\.\d+)b(\d+)$", v)
    if beta_match:
        return f"{beta_match.group(1)}-beta.{beta_match.group(2)}"

    # Handle rc: 0.1.0rc1 -> 0.1.0-rc.1
    rc_match = re.match(r"^(\d+\.\d+\.\d+)rc(\d+)$", v)
    if rc_match:
        return f"{rc_match.group(1)}-rc.{rc_match.group(2)}"

    return v


def extract_version_from_file(file_path: Path, source_type: str, field: str) -> str:
    """Extract declared version string from file based on type."""
    content = file_path.read_text(encoding="utf-8")
    if source_type == "json":
        data = json.loads(content)
        val = data.get(field)
        if not val:
            raise ValueError(f"Field '{field}' not found in {file_path}")
        return str(val)

    if source_type == "toml":
        # Extract version under [project]
        match = re.search(r'\[project\][^\[]*?version\s*=\s*["\']([^"\']+)["\']', content, re.DOTALL)
        if not match:
            # Fallback to simple version regex
            match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if not match:
            raise ValueError(f"Version field not found in {file_path}")
        return match.group(1)

    if source_type == "python":
        match = re.search(rf'{field}\s*=\s*["\']([^"\']+)["\']', content)
        if not match:
            raise ValueError(f"Variable '{field}' not found in {file_path}")
        return match.group(1)

    raise ValueError(f"Unsupported source type '{source_type}' for {file_path}")


def validate_release_tag(tag_str: str, expected_version: str | None = None) -> VersionComponents:
    """Validate Git tag format 'vX.Y.Z[-channel.N]' and check alignment with expected version."""
    if not tag_str.startswith("v"):
        raise ValueError(f"Release tag '{tag_str}' must start with 'v' prefix (e.g., v0.1.0-rc.1).")

    version_part = tag_str[1:]
    components = parse_semver(version_part)

    if expected_version:
        expected_clean = expected_version[1:] if expected_version.startswith("v") else expected_version
        if components.raw != expected_clean:
            raise ValueError(
                f"Tag '{tag_str}' (resolving to '{components.raw}') does not match expected version '{expected_clean}'."
            )

    return components


def check_workspace_consistency(
    repo_root: Path, allow_dev: bool = True
) -> tuple[bool, list[str], str]:
    """Check that all version source files in the repository declare matching versions.

    Returns:
        (is_consistent, errors, canonical_version)
    """
    errors: list[str] = []
    versions_found: dict[str, str] = {}

    for src in VERSION_SOURCES:
        file_path = repo_root / src["path"]
        if not file_path.exists():
            errors.append(f"Missing required version file: {src['path']}")
            continue

        try:
            raw_v = extract_version_from_file(file_path, src["type"], src["field"])
            norm_v = normalize_pep440_to_semver(raw_v)
            # Verify parsed version is valid SemVer
            parse_semver(norm_v)
            versions_found[src["path"]] = norm_v
        except Exception as exc:
            errors.append(f"Error parsing version from {src['path']}: {exc}")

    if not versions_found:
        return False, errors + ["No version files could be read."], ""

    # Choose package.json as canonical reference
    canonical_version = versions_found.get("package.json") or next(iter(versions_found.values()))

    # Check for mismatches
    for path, v in versions_found.items():
        if v != canonical_version:
            errors.append(
                f"Version mismatch in '{path}': declared '{v}' does not match canonical '{canonical_version}'."
            )

    # If dev versions not allowed (e.g. for release qualification)
    if not allow_dev and ("dev" in canonical_version):
        errors.append(
            f"Release qualification requires a formal release or candidate version; found developmental '{canonical_version}'."
        )

    return len(errors) == 0, errors, canonical_version


def main() -> int:
    parser = argparse.ArgumentParser(description="DERA Version & SemVer Qualification Engine")
    parser.add_argument("--version", help="Validate a specific version string against SemVer 2.0.0")
    parser.add_argument("--tag", help="Validate a Git tag format (e.g., 'v0.1.0-rc.1')")
    parser.add_argument(
        "--check-consistency",
        action="store_true",
        help="Check version synchronization across all repository files",
    )
    parser.add_argument(
        "--require-candidate",
        action="store_true",
        help="Require version to be a release candidate (e.g., contains -rc.) or stable",
    )
    parser.add_argument(
        "--disallow-dev",
        action="store_true",
        help="Fail if developmental versions (-dev, .devN) are encountered",
    )
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parent.parent.parent),
        help="Path to repository root",
    )

    args = parser.parse_args()
    repo_root = Path(args.repo_root)

    success = True
    errors: list[str] = []

    print("[DERA] Version Validation Engine")
    print(f"[DERA] Repository Root: {repo_root}")

    # 1. Validate isolated version if specified
    if args.version:
        try:
            parsed = parse_semver(args.version)
            print(f"[SUCCESS] Version '{args.version}' is valid SemVer 2.0.0:")
            print(f"          Major: {parsed.major}, Minor: {parsed.minor}, Patch: {parsed.patch}")
            print(f"          Pre-release: {parsed.prerelease}, Build Metadata: {parsed.buildmetadata}")
            if args.require_candidate:
                if not (parsed.prerelease and "rc" in parsed.prerelease or parsed.prerelease is None):
                    errors.append(f"Version '{args.version}' is neither an RC nor a stable release.")
        except ValueError as err:
            errors.append(str(err))

    # 2. Validate tag if specified
    if args.tag:
        try:
            parsed_tag = validate_release_tag(args.tag, expected_version=args.version)
            print(f"[SUCCESS] Tag '{args.tag}' strictly conforms to SemVer tag specification.")
        except ValueError as err:
            errors.append(str(err))

    # 3. Check repository consistency if requested or default
    if args.check_consistency or (not args.version and not args.tag):
        print("[DERA] Auditing workspace version consistency...")
        consistent, cons_errors, canonical_v = check_workspace_consistency(
            repo_root=repo_root, allow_dev=not args.disallow_dev
        )
        if consistent:
            print(f"[SUCCESS] All workspace version sources are synchronized at canonical '{canonical_v}'.")
            for src in VERSION_SOURCES:
                print(f"          [OK] {src['path']}")
        else:
            errors.extend(cons_errors)

    if errors:
        print("\n[FAIL] Version validation failed with errors:")
        for err in errors:
            print(f"  • {err}")
        return 1

    print("\n[SUCCESS] Version qualification completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
