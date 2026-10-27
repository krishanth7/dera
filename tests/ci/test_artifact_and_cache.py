# ============================================================
# DERA — Database Engineering & Reverse Analysis
# Regression Tests: Artifact Naming, Cache Policy & Test Telemetry
# ============================================================

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from scripts.ci.artifact_manager import (
    CANONICAL_CATEGORIES,
    CANONICAL_PLATFORMS,
    generate_artifact_name,
    generate_directory_manifest,
    scan_directory_for_sensitive_files,
    validate_artifact_name,
)
from scripts.ci.test_reporter import (
    generate_json_summary,
    generate_junit_xml,
)


class TestArtifactAndCachePolicy(unittest.TestCase):
    """Exhaustive regression test suite for CI artifact naming, cache integrity, and test reporting."""

    def test_canonical_categories_and_platforms_presence(self) -> None:
        """Verify that all Phase 3.5 canonical categories and platforms are registered."""
        expected_cats = {
            "test-results",
            "coverage",
            "build",
            "diagnostics",
            "security",
            "docs",
            "audit",
        }
        self.assertTrue(expected_cats.issubset(CANONICAL_CATEGORIES))
        expected_platforms = {"linux", "windows", "macos"}
        self.assertTrue(expected_platforms.issubset(CANONICAL_PLATFORMS))

    def test_generate_and_validate_canonical_names(self) -> None:
        """Verify generation and validation of canonical artifact names across all categories."""
        for cat in CANONICAL_CATEGORIES:
            name = generate_artifact_name(
                category=cat,
                platform="linux",
                runtime="py313",
                run_id="40456988257",
                attempt=1,
            )
            self.assertTrue(name.startswith(f"dera-{cat}-linux-py313-"))
            valid, msg = validate_artifact_name(name)
            self.assertTrue(valid, f"Failed validation for '{name}': {msg}")

    def test_rejection_of_invalid_categories(self) -> None:
        """Verify that non-canonical categories are rejected."""
        invalid_name = "dera-arbitrarydata-linux-py313-12345-1"
        valid, msg = validate_artifact_name(invalid_name)
        self.assertFalse(valid)
        self.assertIn("not in canonical registry", msg)

    def test_rejection_of_invalid_platforms(self) -> None:
        """Verify that unsupported platforms are rejected."""
        invalid_name = "dera-build-solaris-py313-12345-1"
        valid, msg = validate_artifact_name(invalid_name)
        self.assertFalse(valid)
        self.assertIn("not in canonical platforms", msg)

    def test_rejection_of_malformed_artifact_names(self) -> None:
        """Verify that malformed artifact names failing regex structure are rejected."""
        malformed = [
            "artifact-1",
            "dera-build-linux",
            "dera-build-linux-py313",
            "dera-build-linux-py313-abc-1",
            "dera_build_linux_py313_123_1",
            "",
        ]
        for name in malformed:
            valid, msg = validate_artifact_name(name)
            self.assertFalse(valid, f"Expected '{name}' to be rejected")

    def test_sensitive_file_detection_in_directories(self) -> None:
        """Verify that scan_directory_for_sensitive_files identifies credentials and forbidden secrets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "safe_report.json").write_text("{}", encoding="utf-8")
            (tmppath / ".env").write_text("DB_PASS=123", encoding="utf-8")
            (tmppath / "private_key.pem").write_text("CERT", encoding="utf-8")
            (tmppath / "user_credentials.json").write_text("{}", encoding="utf-8")
            (tmppath / "auth_token.txt").write_text("secret", encoding="utf-8")

            violations = scan_directory_for_sensitive_files(tmppath)
            self.assertEqual(len(violations), 4)
            found_names = [Path(v).name for v in violations]
            self.assertIn(".env", found_names)
            self.assertIn("private_key.pem", found_names)
            self.assertIn("user_credentials.json", found_names)
            self.assertIn("auth_token.txt", found_names)

    def test_clean_directory_passes_sensitive_scan(self) -> None:
        """Verify that clean build/report directories pass sensitive file scan with zero violations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "test-results.xml").write_text("<xml/>", encoding="utf-8")
            (tmppath / "test-summary.json").write_text("{}", encoding="utf-8")
            (tmppath / "build.wheel").write_text("binary", encoding="utf-8")

            violations = scan_directory_for_sensitive_files(tmppath)
            self.assertEqual(len(violations), 0)

    def test_directory_checksum_manifest_generation(self) -> None:
        """Verify that generate_directory_manifest computes deterministic SHA-256 digests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            f1 = tmppath / "report.xml"
            f1.write_text("<data>123</data>", encoding="utf-8")
            f2 = tmppath / "subdir" / "summary.json"
            f2.parent.mkdir(parents=True, exist_ok=True)
            f2.write_text('{"status": "ok"}', encoding="utf-8")

            manifest = generate_directory_manifest(tmppath)
            self.assertEqual(manifest["total_files"], 2)
            self.assertIn("report.xml", manifest["checksums"])
            self.assertIn("subdir/summary.json", manifest["checksums"])
            # Check length of SHA-256 hex digest
            self.assertEqual(len(manifest["checksums"]["report.xml"]), 64)

    def test_junit_xml_report_formatting(self) -> None:
        """Verify that generate_junit_xml generates valid XML parseable by ElementTree."""
        records = [
            {
                "id": "tests.unit.test_foo.TestFoo.test_success",
                "classname": "tests.unit.test_foo.TestFoo",
                "name": "test_success",
                "status": "passed",
                "duration": 0.05,
                "message": None,
                "details": None,
            },
            {
                "id": "tests.unit.test_foo.TestFoo.test_fail",
                "classname": "tests.unit.test_foo.TestFoo",
                "name": "test_fail",
                "status": "failure",
                "duration": 0.02,
                "message": "Values not equal",
                "details": "Traceback:\nAssertionError",
            },
            {
                "id": "tests.unit.test_foo.TestFoo.test_skip",
                "classname": "tests.unit.test_foo.TestFoo",
                "name": "test_skip",
                "status": "skipped",
                "duration": 0.001,
                "message": "Not implemented yet",
                "details": None,
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = str(Path(tmpdir) / "junit.xml")
            generate_junit_xml(records, total_time=0.071, output_path=xml_path)

            tree = ET.parse(xml_path)
            root = tree.getroot()
            self.assertEqual(root.tag, "testsuites")
            self.assertEqual(root.attrib["tests"], "3")
            self.assertEqual(root.attrib["failures"], "1")
            self.assertEqual(root.attrib["errors"], "0")
            self.assertEqual(root.attrib["skipped"], "1")

            suite = root.find("testsuite")
            self.assertIsNotNone(suite)
            self.assertEqual(suite.attrib["name"], "tests.unit.test_foo.TestFoo")
            cases = suite.findall("testcase")
            self.assertEqual(len(cases), 3)

    def test_json_summary_telemetry(self) -> None:
        """Verify that generate_json_summary outputs correct counts and slowest tests."""
        records = [
            {
                "id": "test_fast",
                "classname": "C",
                "name": "fast",
                "status": "passed",
                "duration": 0.01,
            },
            {
                "id": "test_slow",
                "classname": "C",
                "name": "slow",
                "status": "passed",
                "duration": 0.50,
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = str(Path(tmpdir) / "summary.json")
            generate_json_summary(
                records, total_time=0.51, output_path=json_path, suite_dir="tests"
            )

            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)

            self.assertEqual(data["total"], 2)
            self.assertEqual(data["passed"], 2)
            self.assertEqual(data["failures"], 0)
            self.assertEqual(data["status"], "PASSED")
            self.assertEqual(data["slowest_tests"][0]["id"], "test_slow")
            self.assertEqual(data["slowest_tests"][0]["duration_ms"], 500.0)


if __name__ == "__main__":
    unittest.main()
