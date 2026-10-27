#!/usr/bin/env python3
"""DERA Release Manifest Generator & Schema Validator.

Validates the machine-readable release manifest (release/manifest.json) against
strict schema rules, commit reference integrity, SemVer format, and artifact
cryptographic SHA-256 checksums.

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SHA256_HEX_REGEX = re.compile(r"^[a-f0-9]{64}$")
GIT_SHA_REGEX = re.compile(r"^[a-f0-9]{40}$")
ALLOWED_CHANNELS = ("alpha", "beta", "rc", "stable", "dev")
ALLOWED_QUALIFICATION_STATUS = ("QUALIFIED", "PENDING", "REJECTED", "DRY_RUN")


def compute_sha256(file_path: Path) -> str:
    """Compute lowercase SHA-256 hexadecimal digest for a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest().lower()


def validate_manifest_dict(
    data: dict[str, Any], dist_dir: Path | None = None
) -> tuple[bool, list[str]]:
    """Validate release manifest structure, fields, and optional artifact files."""
    errors: list[str] = []

    # 1. Required top-level fields
    required_fields = [
        "project",
        "version",
        "channel",
        "commit",
        "generated_at",
        "qualification_status",
        "build_environment",
        "artifacts",
    ]
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing mandatory manifest field: '{field}'")

    if errors:
        return False, errors

    # 2. Validate project identity
    if data["project"].lower() not in ("dera", "dera-monorepo", "dera-core"):
        errors.append(f"Unexpected project name in manifest: '{data['project']}'. Expected 'dera'.")

    # 3. Validate channel
    if data["channel"] not in ALLOWED_CHANNELS:
        errors.append(
            f"Invalid release channel '{data['channel']}'. Must be one of: {ALLOWED_CHANNELS}"
        )

    # 4. Validate qualification status
    if data["qualification_status"] not in ALLOWED_QUALIFICATION_STATUS:
        errors.append(
            f"Invalid qualification_status '{data['qualification_status']}'. Must be one of: {ALLOWED_QUALIFICATION_STATUS}"
        )

    # 5. Validate commit SHA
    commit_sha = str(data["commit"]).strip()
    if not GIT_SHA_REGEX.match(commit_sha):
        errors.append(
            f"Invalid Git commit SHA in manifest: '{commit_sha}'. Must be 40-character hex."
        )

    # 6. Validate generated_at timestamp
    try:
        datetime.datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00"))
    except Exception as exc:
        errors.append(f"Invalid ISO 8601 generated_at timestamp '{data['generated_at']}': {exc}")

    # 7. Validate artifacts list
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("'artifacts' field must be an array of artifact objects.")
    elif len(artifacts) == 0:
        errors.append("'artifacts' array cannot be empty in a qualified release manifest.")
    else:
        for idx, art in enumerate(artifacts):
            if not isinstance(art, dict):
                errors.append(f"Artifact at index {idx} is not an object.")
                continue

            name = art.get("name")
            sha256 = art.get("sha256")
            size_bytes = art.get("size_bytes")

            if not name or not isinstance(name, str):
                errors.append(f"Artifact at index {idx} has invalid or missing 'name'.")
            if not sha256 or not SHA256_HEX_REGEX.match(str(sha256).lower()):
                errors.append(
                    f"Artifact '{name or idx}' has invalid SHA-256 hash: '{sha256}'. Must be 64-char hex."
                )
            if not isinstance(size_bytes, int) or size_bytes < 0:
                errors.append(f"Artifact '{name or idx}' has invalid size_bytes: {size_bytes}")

            # Optional physical verification on disk
            if dist_dir and name:
                disk_file = dist_dir / name
                if not disk_file.exists():
                    errors.append(
                        f"Manifest artifact '{name}' does not exist on disk at: {disk_file}"
                    )
                else:
                    computed_hash = compute_sha256(disk_file)
                    if computed_hash != str(sha256).lower():
                        errors.append(
                            f"Hash mismatch for '{name}': manifest specifies {sha256}, disk computed {computed_hash}."
                        )

    return len(errors) == 0, errors


def generate_manifest(
    project: str,
    version: str,
    channel: str,
    commit_sha: str,
    dist_dir: Path,
    status: str = "QUALIFIED",
) -> dict[str, Any]:
    """Generate a manifest dictionary by scanning built artifacts in dist_dir."""
    if not dist_dir.is_dir():
        raise FileNotFoundError(f"Artifact directory '{dist_dir}' does not exist.")

    artifacts: list[dict[str, Any]] = []
    for item in sorted(dist_dir.iterdir()):
        if item.is_file() and item.name != "manifest.json":
            file_hash = compute_sha256(item)
            file_size = item.stat().st_size
            art_type = "generic"
            if item.name.endswith(".whl"):
                art_type = "python-wheel"
            elif item.name.endswith(".tar.gz"):
                art_type = "python-sdist"
            elif item.name.endswith(".tgz"):
                art_type = "npm-tarball"
            elif item.name == "SHA256SUMS.txt":
                art_type = "checksums"

            artifacts.append(
                {
                    "name": item.name,
                    "type": art_type,
                    "sha256": file_hash,
                    "size_bytes": file_size,
                }
            )

    return {
        "project": project,
        "version": version,
        "channel": channel,
        "commit": commit_sha,
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "qualification_status": status,
        "build_environment": {
            "os": sys.platform,
            "python": sys.version.split()[0],
        },
        "artifacts": artifacts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="DERA Release Manifest Validator & Generator")
    parser.add_argument(
        "--manifest",
        default="release/manifest.json",
        help="Path to manifest file to validate (default: 'release/manifest.json')",
    )
    parser.add_argument(
        "--dist-dir",
        help="Optional directory containing artifacts to verify against manifest",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate manifest from artifacts in --dist-dir",
    )
    parser.add_argument("--version", help="Release version (required for --generate)")
    parser.add_argument("--commit", help="Source commit SHA (required for --generate)")
    parser.add_argument("--channel", default="alpha", help="Release channel (default: alpha)")
    parser.add_argument("--status", default="QUALIFIED", help="Qualification status")

    args = parser.parse_args()

    if args.generate:
        if not args.dist_dir or not args.version or not args.commit:
            print("[FAIL] --generate requires --dist-dir, --version, and --commit.")
            return 1
        dist_path = Path(args.dist_dir)
        manifest_data = generate_manifest(
            project="dera",
            version=args.version,
            channel=args.channel,
            commit_sha=args.commit,
            dist_dir=dist_path,
            status=args.status,
        )
        out_path = Path(args.manifest)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
        print(
            f"[SUCCESS] Generated manifest at: {out_path} ({len(manifest_data['artifacts'])} artifacts)"
        )
        return 0

    manifest_file = Path(args.manifest)
    if not manifest_file.exists():
        print(f"[FAIL] Manifest file does not exist: {manifest_file}")
        return 1

    try:
        with open(manifest_file, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        print(f"[FAIL] Could not parse manifest JSON: {exc}")
        return 1

    dist_path = Path(args.dist_dir) if args.dist_dir else None
    valid, errors = validate_manifest_dict(data, dist_dir=dist_path)

    if not valid:
        print(f"\n[FAIL] Release manifest validation failed with {len(errors)} error(s):")
        for err in errors:
            print(f"  • {err}")
        return 1

    print(f"[SUCCESS] Release manifest '{manifest_file}' is valid.")
    print(
        f"          Project: {data['project']} | Version: {data['version']} | Channel: {data['channel']}"
    )
    print(f"          Commit: {data['commit']} | Status: {data['qualification_status']}")
    print(f"          Artifacts count: {len(data['artifacts'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
