#!/usr/bin/env python3
"""DERA Release Artifact Integrity & Checksum Verification Engine.

Computes and verifies SHA-256 cryptographic digests, enforces artifact
naming conventions, audits release manifests, and detects tampered or
corrupted release distribution files.

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

# Supported canonical artifact patterns
VALID_ARTIFACT_PATTERNS = [
    re.compile(r"^dera[-_]core-.*\.whl$"),
    re.compile(r"^dera[-_]core-.*\.tar\.gz$"),
    re.compile(r"^dera[-_]contracts-.*\.tgz$"),
    re.compile(r"^@?dera[-_].*\.tgz$"),
    re.compile(r"^SHA256SUMS\.txt$"),
    re.compile(r"^manifest\.json$"),
]


def compute_sha256(file_path: Path) -> str:
    """Compute lowercase SHA-256 hexadecimal digest for a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest().lower()


def parse_checksums_file(checksum_file: Path) -> dict[str, str]:
    """Parse standard sha256sum format (hash  filename or hash *filename)."""
    expected: dict[str, str] = {}
    content = checksum_file.read_text(encoding="utf-8")
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) == 2:
            digest, filename = parts[0].strip().lower(), parts[1].strip()
            # Remove leading * indicating binary mode in some sha256 tools
            if filename.startswith("*"):
                filename = filename[1:]
            filename = Path(filename).name  # Normalize to basename
            expected[filename] = digest
    return expected


def verify_directory_artifacts(
    dist_dir: Path,
    checksum_file: Path | None = None,
    manifest_file: Path | None = None,
    require_checksums: bool = True,
) -> tuple[bool, list[str], dict[str, str]]:
    """Verify integrity, naming, and hashes of all artifacts in dist_dir.

    Returns:
        (is_valid, error_list, computed_hashes)
    """
    errors: list[str] = []
    computed_hashes: dict[str, str] = {}

    if not dist_dir.exists() or not dist_dir.is_dir():
        return False, [f"Distribution directory '{dist_dir}' does not exist."], {}

    files = [f for f in dist_dir.iterdir() if f.is_file()]
    if not files:
        return False, [f"No release artifacts found in directory '{dist_dir}'."], {}

    # Check naming conventions
    for f in files:
        matched = any(p.match(f.name) for p in VALID_ARTIFACT_PATTERNS)
        if not matched:
            errors.append(
                f"Artifact '{f.name}' violates canonical naming conventions for DERA releases."
            )
        computed_hashes[f.name] = compute_sha256(f)

    # Verify against SHA256SUMS.txt
    target_checksum_file = checksum_file or (dist_dir / "SHA256SUMS.txt")
    if target_checksum_file.exists():
        expected_sums = parse_checksums_file(target_checksum_file)
        for expected_name, expected_hash in expected_sums.items():
            if expected_name not in computed_hashes:
                errors.append(
                    f"Artifact '{expected_name}' listed in SHA256SUMS.txt is missing from directory."
                )
            elif computed_hashes[expected_name] != expected_hash:
                errors.append(
                    f"Integrity failure on '{expected_name}': expected SHA-256 {expected_hash}, computed {computed_hashes[expected_name]}."
                )
    elif require_checksums:
        errors.append(f"Missing required checksums manifest 'SHA256SUMS.txt' in '{dist_dir}'.")

    # Verify against manifest.json
    target_manifest_file = manifest_file or (dist_dir / "manifest.json")
    if target_manifest_file.exists():
        try:
            with open(target_manifest_file, encoding="utf-8") as f:
                data = json.load(f)
            manifest_arts = data.get("artifacts", [])
            for art in manifest_arts:
                art_name = art.get("name")
                art_hash = art.get("sha256", "").lower()
                if not art_name:
                    continue
                if art_name not in computed_hashes:
                    errors.append(
                        f"Artifact '{art_name}' listed in manifest.json is missing from directory."
                    )
                elif computed_hashes[art_name] != art_hash:
                    errors.append(
                        f"Integrity failure on '{art_name}' against manifest.json: expected {art_hash}, computed {computed_hashes[art_name]}."
                    )
        except Exception as exc:
            errors.append(f"Could not parse manifest file '{target_manifest_file}': {exc}")

    return len(errors) == 0, errors, computed_hashes


def main() -> int:
    parser = argparse.ArgumentParser(description="DERA Release Artifact Integrity Verifier")
    parser.add_argument(
        "--dist-dir",
        default="dist",
        help="Path to directory containing built artifacts (default: 'dist')",
    )
    parser.add_argument(
        "--checksums",
        help="Explicit path to SHA256SUMS.txt file",
    )
    parser.add_argument(
        "--manifest",
        help="Explicit path to manifest.json file",
    )
    parser.add_argument(
        "--no-require-checksums",
        action="store_true",
        help="Do not require SHA256SUMS.txt if only computing digests",
    )

    args = parser.parse_args()
    dist_dir = Path(args.dist_dir)
    cs_file = Path(args.checksums) if args.checksums else None
    mf_file = Path(args.manifest) if args.manifest else None

    print("[DERA] Release Artifact Integrity & Checksum Verifier")
    print(f"[DERA] Target Directory: {dist_dir.resolve()}")

    is_valid, errors, hashes = verify_directory_artifacts(
        dist_dir=dist_dir,
        checksum_file=cs_file,
        manifest_file=mf_file,
        require_checksums=not args.no_require_checksums,
    )

    if hashes:
        print("\n[DERA] Computed Cryptographic SHA-256 Digests:")
        for fname, h in sorted(hashes.items()):
            print(f"  {h}  {fname}")

    if not is_valid:
        print(f"\n[FAIL] Artifact verification failed with {len(errors)} error(s):")
        for err in errors:
            print(f"  • {err}")
        return 1

    print(
        f"\n[SUCCESS] All {len(hashes)} artifacts verified successfully against integrity policies."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
