#!/usr/bin/env python3
"""DERA Artifact Management & Naming Integrity Engine.

Provides deterministic artifact naming generation, name policy validation,
sensitive content scanning, and SHA-256 integrity manifest generation
according to DERA DevSecOps standards.

Artifact naming pattern:
    dera-{category}-{platform}-{runtime}-{run-id}-{attempt}

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

# Canonical categories permitted for DERA CI artifacts
CANONICAL_CATEGORIES = frozenset(
    {
        "test-results",
        "coverage",
        "build",
        "diagnostics",
        "security",
        "docs",
        "audit",
    }
)

CANONICAL_PLATFORMS = frozenset({"linux", "windows", "macos", "multi", "any"})

# Sensitive filename patterns forbidden from artifact packaging
FORBIDDEN_FILE_PATTERNS = [
    re.compile(r"^\.env(\..+)?$", re.IGNORECASE),
    re.compile(r".*\.pem$", re.IGNORECASE),
    re.compile(r".*\.key$", re.IGNORECASE),
    re.compile(r".*id_rsa.*", re.IGNORECASE),
    re.compile(r".*credential.*", re.IGNORECASE),
    re.compile(r".*secret.*", re.IGNORECASE),
    re.compile(r".*token.*", re.IGNORECASE),
]

# Strict pattern for canonical artifact names
ARTIFACT_NAME_PATTERN = re.compile(
    r"^dera-(?P<category>[a-z0-9]+(?:-[a-z0-9]+)*)"
    r"-(?P<platform>[a-z0-9]+)"
    r"-(?P<runtime>[a-z0-9]+)"
    r"-(?P<run_id>[0-9]+)"
    r"-(?P<attempt>[0-9]+)$"
)


def generate_artifact_name(
    category: str,
    platform: str,
    runtime: str,
    run_id: str | int,
    attempt: str | int = 1,
) -> str:
    """Generate canonical DERA artifact name adhering to Phase 3.5 policy."""
    clean_cat = category.strip().lower()
    clean_plat = platform.strip().lower()
    clean_rt = runtime.strip().lower().replace(".", "")
    clean_run = str(run_id).strip()
    clean_att = str(attempt).strip()

    name = f"dera-{clean_cat}-{clean_plat}-{clean_rt}-{clean_run}-{clean_att}"
    return name


def validate_artifact_name(name: str) -> tuple[bool, str]:
    """Validate artifact name against canonical pattern and category registry."""
    if not name:
        return False, "Artifact name cannot be empty."

    match = ARTIFACT_NAME_PATTERN.match(name)
    if not match:
        return False, (
            f"Artifact name '{name}' does not match canonical format: "
            "dera-{category}-{platform}-{runtime}-{run-id}-{attempt}"
        )

    category = match.group("category")
    if category not in CANONICAL_CATEGORIES:
        return False, (
            f"Category '{category}' in artifact '{name}' is not in canonical registry: "
            f"{sorted(CANONICAL_CATEGORIES)}"
        )

    platform = match.group("platform")
    if platform not in CANONICAL_PLATFORMS:
        return False, (
            f"Platform '{platform}' in artifact '{name}' is not in canonical platforms: "
            f"{sorted(CANONICAL_PLATFORMS)}"
        )

    # Check for forbidden sensitive keywords in the name itself
    lower_name = name.lower()
    for sensitive in ["password", "secret", "private", "token", "credential"]:
        if sensitive in lower_name and category != "security":
            return False, f"Artifact name contains forbidden sensitive term '{sensitive}'."

    return True, "Valid artifact name."


def scan_directory_for_sensitive_files(directory_path: str | Path) -> list[str]:
    """Scan directory recursively and return list of forbidden/sensitive files."""
    violations: list[str] = []
    base_path = Path(directory_path).resolve()

    if not base_path.exists():
        return violations

    for root, _, files in os.walk(base_path):
        for file in files:
            for pattern in FORBIDDEN_FILE_PATTERNS:
                if pattern.match(file):
                    rel = os.path.relpath(os.path.join(root, file), base_path)
                    violations.append(rel)
                    break

    return violations


def generate_directory_manifest(directory_path: str | Path) -> dict:
    """Generate SHA-256 checksum manifest for all files in a directory."""
    base_path = Path(directory_path).resolve()
    manifest: dict[str, str] = {}

    if not base_path.is_dir():
        raise ValueError(f"Path '{directory_path}' is not a directory.")

    for root, _, files in os.walk(base_path):
        for file in sorted(files):
            full_path = Path(root) / file
            rel_path = full_path.relative_to(base_path).as_posix()
            hasher = hashlib.sha256()
            with open(full_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            manifest[rel_path] = hasher.hexdigest()

    return {
        "directory": str(base_path),
        "total_files": len(manifest),
        "checksums": manifest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="DERA Artifact Management CLI")
    subparsers = parser.add_subparsers(dest="command")

    gen_p = subparsers.add_parser("generate", help="Generate canonical artifact name")
    gen_p.add_argument("--category", required=True, help="Artifact category")
    gen_p.add_argument("--platform", default="linux", help="Target OS platform (default: linux)")
    gen_p.add_argument("--runtime", default="py313", help="Target runtime (e.g. py312, node22)")
    gen_p.add_argument("--run-id", required=True, help="GitHub Actions Run ID")
    gen_p.add_argument("--attempt", default="1", help="GitHub Actions Run Attempt (default: 1)")

    val_p = subparsers.add_parser("validate", help="Validate an artifact name")
    val_p.add_argument("name", help="Artifact name to validate")

    scan_p = subparsers.add_parser("scan-safe", help="Scan directory for forbidden sensitive files")
    scan_p.add_argument("path", help="Directory path to scan")

    man_p = subparsers.add_parser(
        "manifest", help="Generate SHA-256 checksum manifest for directory"
    )
    man_p.add_argument("path", help="Directory path to process")
    man_p.add_argument("--output", help="Optional output path for manifest JSON")

    args = parser.parse_args()

    if args.command == "generate":
        name = generate_artifact_name(
            category=args.category,
            platform=args.platform,
            runtime=args.runtime,
            run_id=args.run_id,
            attempt=args.attempt,
        )
        valid, msg = validate_artifact_name(name)
        if not valid:
            print(f"ERROR: Generated invalid name: {msg}", file=sys.stderr)
            return 1
        print(name)
        return 0

    elif args.command == "validate":
        valid, msg = validate_artifact_name(args.name)
        if valid:
            print(f"PASS: {args.name} is a canonical DERA artifact name.")
            return 0
        else:
            print(f"FAIL: {msg}", file=sys.stderr)
            return 1

    elif args.command == "scan-safe":
        violations = scan_directory_for_sensitive_files(args.path)
        if violations:
            print(f"FAIL: Found {len(violations)} sensitive/forbidden files:", file=sys.stderr)
            for v in violations:
                print(f"  - {v}", file=sys.stderr)
            return 1
        print(f"PASS: Directory '{args.path}' contains no sensitive or credential files.")
        return 0

    elif args.command == "manifest":
        manifest_data = generate_directory_manifest(args.path)
        output_json = json.dumps(manifest_data, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_json)
            print(f"SUCCESS: Wrote checksum manifest to {args.output}")
        else:
            print(output_json)
        return 0

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
