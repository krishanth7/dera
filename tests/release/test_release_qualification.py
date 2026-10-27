"""DERA Release Qualification, Artifact Integrity & Recovery Tests.

Validates Semantic Versioning enforcement, release manifest schemas,
SHA-256 cryptographic artifact verification, workspace consistency, and
safe dry-run qualification logic.

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.release.validate_manifest import (
    generate_manifest,
    validate_manifest_dict,
)
from scripts.release.validate_version import (
    check_workspace_consistency,
    normalize_pep440_to_semver,
    parse_semver,
    validate_release_tag,
)
from scripts.release.verify_artifacts import (
    verify_directory_artifacts,
)


class TestSemanticVersioning(unittest.TestCase):
    """Test SemVer 2.0.0 compliance and validation rules."""

    def test_valid_semver_strings(self) -> None:
        valid_cases = [
            ("0.1.0", (0, 1, 0, None, None)),
            ("0.1.0-alpha.1", (0, 1, 0, "alpha.1", None)),
            ("0.1.0-beta.2", (0, 1, 0, "beta.2", None)),
            ("0.1.0-rc.1", (0, 1, 0, "rc.1", None)),
            ("1.0.0", (1, 0, 0, None, None)),
            ("2.1.3-alpha.0+build.42", (2, 1, 3, "alpha.0", "build.42")),
        ]
        for ver_str, expected in valid_cases:
            with self.subTest(version=ver_str):
                parsed = parse_semver(ver_str)
                self.assertEqual(parsed.major, expected[0])
                self.assertEqual(parsed.minor, expected[1])
                self.assertEqual(parsed.patch, expected[2])
                self.assertEqual(parsed.prerelease, expected[3])
                self.assertEqual(parsed.buildmetadata, expected[4])

    def test_invalid_semver_strings(self) -> None:
        invalid_cases = [
            "0.1",  # Missing patch
            "0.1.0.0",  # 4 numbers (historical non-standard)
            "01.1.0",  # Leading zero in major
            "1.02.0",  # Leading zero in minor
            "1.2.03",  # Leading zero in patch
            "0.1.0-alpha..1",  # Empty dot-separated identifier
            "v0.1.0",  # Raw v-prefix passed to semver parser directly
            "beta-version",  # Non-numeric major
            "",  # Empty string
        ]
        for ver_str in invalid_cases:
            with self.subTest(version=ver_str):
                with self.assertRaises(ValueError):
                    parse_semver(ver_str)

    def test_pep440_normalization(self) -> None:
        cases = [
            ("0.1.0.dev1", "0.1.0-dev"),
            ("0.1.0a1", "0.1.0-alpha.1"),
            ("0.1.0b2", "0.1.0-beta.2"),
            ("0.1.0rc1", "0.1.0-rc.1"),
            ("0.1.0", "0.1.0"),
        ]
        for pep, expected_semver in cases:
            with self.subTest(pep=pep):
                self.assertEqual(normalize_pep440_to_semver(pep), expected_semver)

    def test_release_tag_validation(self) -> None:
        # Valid tags
        self.assertEqual(validate_release_tag("v0.1.0").raw, "0.1.0")
        self.assertEqual(validate_release_tag("v0.1.0-rc.1").raw, "0.1.0-rc.1")

        # Invalid tags: missing 'v' prefix
        with self.assertRaises(ValueError):
            validate_release_tag("0.1.0")

        # Mismatch with expected version
        with self.assertRaises(ValueError):
            validate_release_tag("v0.2.0", expected_version="0.1.0")


class TestWorkspaceConsistency(unittest.TestCase):
    """Test consistency detection across repository version declarations."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp_dir.name)

        # Create mock structure
        (self.root / "packages/contracts").mkdir(parents=True)
        (self.root / "packages/connectors").mkdir(parents=True)
        (self.root / "packages/core/src/dera_core").mkdir(parents=True)
        (self.root / "packages/core/src/dera").mkdir(parents=True)
        (self.root / "packages/connectors/src/dera_connectors").mkdir(parents=True)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def _write_mock_files(self, version_str: str) -> None:
        (self.root / "package.json").write_text(
            json.dumps({"name": "dera", "version": version_str}), encoding="utf-8"
        )
        (self.root / "packages/contracts/package.json").write_text(
            json.dumps({"name": "@dera/contracts", "version": version_str}), encoding="utf-8"
        )
        (self.root / "packages/connectors/package.json").write_text(
            json.dumps({"name": "@dera/connectors", "version": version_str}), encoding="utf-8"
        )
        (self.root / "pyproject.toml").write_text(
            f'[project]\nname = "dera-core"\nversion = "{version_str}"\n', encoding="utf-8"
        )
        (self.root / "packages/core/src/dera_core/__init__.py").write_text(
            f'__version__ = "{version_str}"\n', encoding="utf-8"
        )
        (self.root / "packages/core/src/dera/__init__.py").write_text(
            f'__version__ = "{version_str}"\n', encoding="utf-8"
        )
        (self.root / "packages/connectors/src/dera_connectors/__init__.py").write_text(
            f'__version__ = "{version_str}"\n', encoding="utf-8"
        )

    def test_synchronized_workspace(self) -> None:
        self._write_mock_files("0.1.0")
        consistent, errors, canonical_v = check_workspace_consistency(self.root, allow_dev=False)
        self.assertTrue(consistent)
        self.assertEqual(len(errors), 0)
        self.assertEqual(canonical_v, "0.1.0")

    def test_inconsistent_workspace_detected(self) -> None:
        self._write_mock_files("0.1.0")
        # Tamper with one package version
        (self.root / "packages/contracts/package.json").write_text(
            json.dumps({"name": "@dera/contracts", "version": "0.2.0"}), encoding="utf-8"
        )
        consistent, errors, _ = check_workspace_consistency(self.root, allow_dev=False)
        self.assertFalse(consistent)
        self.assertTrue(any("Version mismatch" in err for err in errors))

    def test_disallow_dev_versions_for_qualification(self) -> None:
        self._write_mock_files("0.1.0-dev")
        consistent, errors, _ = check_workspace_consistency(self.root, allow_dev=False)
        self.assertFalse(consistent)
        self.assertTrue(any("requires a formal release or candidate" in err for err in errors))


class TestReleaseManifestValidation(unittest.TestCase):
    """Test schema verification and generation of release/manifest.json."""

    def test_valid_manifest_dict(self) -> None:
        valid_manifest = {
            "project": "dera",
            "version": "0.1.0-rc.1",
            "channel": "rc",
            "commit": "a" * 40,
            "generated_at": "2026-10-27T12:00:00+00:00",
            "qualification_status": "QUALIFIED",
            "build_environment": {"os": "linux", "python": "3.13.0"},
            "artifacts": [
                {
                    "name": "dera_core-0.1.0rc1-py3-none-any.whl",
                    "type": "python-wheel",
                    "sha256": "b" * 64,
                    "size_bytes": 1024,
                }
            ],
        }
        is_valid, errors = validate_manifest_dict(valid_manifest)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_manifest_missing_fields(self) -> None:
        is_valid, errors = validate_manifest_dict({"project": "dera"})
        self.assertFalse(is_valid)
        self.assertTrue(any("Missing mandatory manifest field" in err for err in errors))

    def test_manifest_invalid_commit_sha(self) -> None:
        manifest = {
            "project": "dera",
            "version": "0.1.0",
            "channel": "stable",
            "commit": "not-a-sha",
            "generated_at": "2026-10-27T12:00:00+00:00",
            "qualification_status": "QUALIFIED",
            "build_environment": {"os": "linux", "python": "3.13"},
            "artifacts": [{"name": "art.whl", "sha256": "c" * 64, "size_bytes": 50}],
        }
        is_valid, errors = validate_manifest_dict(manifest)
        self.assertFalse(is_valid)
        self.assertTrue(any("Invalid Git commit SHA" in err for err in errors))

    def test_manifest_generator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            dist = Path(tmp_dir)
            sample_file = dist / "dera_core-0.1.0-py3-none-any.whl"
            sample_file.write_bytes(b"sample-wheel-content")

            manifest = generate_manifest(
                project="dera",
                version="0.1.0",
                channel="stable",
                commit_sha="f" * 40,
                dist_dir=dist,
            )
            self.assertEqual(manifest["project"], "dera")
            self.assertEqual(manifest["version"], "0.1.0")
            self.assertEqual(len(manifest["artifacts"]), 1)
            self.assertEqual(manifest["artifacts"][0]["name"], sample_file.name)
            self.assertEqual(manifest["artifacts"][0]["size_bytes"], len(b"sample-wheel-content"))


class TestArtifactIntegrity(unittest.TestCase):
    """Test cryptographic SHA-256 verification and tampering detection."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.dist = Path(self.tmp_dir.name)

        # Create valid sample artifacts
        self.whl = self.dist / "dera_core-0.1.0-py3-none-any.whl"
        self.whl.write_bytes(b"content-of-wheel-package")

        self.tgz = self.dist / "dera-contracts-0.1.0.tgz"
        self.tgz.write_bytes(b"content-of-npm-package")

        # Generate SHA256SUMS.txt
        whl_hash = hashlib.sha256(b"content-of-wheel-package").hexdigest()
        tgz_hash = hashlib.sha256(b"content-of-npm-package").hexdigest()
        self.checksums = self.dist / "SHA256SUMS.txt"
        self.checksums.write_text(
            f"{whl_hash}  {self.whl.name}\n{tgz_hash}  {self.tgz.name}\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_valid_artifacts_pass(self) -> None:
        is_valid, errors, hashes = verify_directory_artifacts(self.dist)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        self.assertIn(self.whl.name, hashes)
        self.assertIn(self.tgz.name, hashes)

    def test_tampered_artifact_detected(self) -> None:
        # Tamper with wheel content
        self.whl.write_bytes(b"corrupted-tampered-content")
        is_valid, errors, _ = verify_directory_artifacts(self.dist)
        self.assertFalse(is_valid)
        self.assertTrue(any("Integrity failure" in err for err in errors))

    def test_missing_artifact_detected(self) -> None:
        # Delete npm package that is listed in SHA256SUMS.txt
        self.tgz.unlink()
        is_valid, errors, _ = verify_directory_artifacts(self.dist)
        self.assertFalse(is_valid)
        self.assertTrue(any("is missing from directory" in err for err in errors))

    def test_illegal_artifact_naming_detected(self) -> None:
        illegal_file = self.dist / "unknown_binary.exe"
        illegal_file.write_bytes(b"malicious-or-unsupported-binary")
        is_valid, errors, _ = verify_directory_artifacts(self.dist, require_checksums=False)
        self.assertFalse(is_valid)
        self.assertTrue(any("violates canonical naming conventions" in err for err in errors))

    def test_empty_directory_rejected(self) -> None:
        empty_dir = Path(self.tmp_dir.name) / "empty"
        empty_dir.mkdir()
        is_valid, errors, _ = verify_directory_artifacts(empty_dir)
        self.assertFalse(is_valid)
        self.assertTrue(any("No release artifacts found" in err for err in errors))


if __name__ == "__main__":
    unittest.main()
