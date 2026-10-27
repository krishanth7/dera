#!/usr/bin/env python3
"""DERA Standardized Test Reporter & JUnit XML Generator.

Executes Python test suites using the standard library `unittest` framework,
recording execution timings, capturing failure/error diagnostics, and emitting
both JUnit XML (`reports/test-results.xml`) and JSON summary telemetry (`reports/test-summary.json`).

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import time
import unittest
from xml.etree import ElementTree as ET


class StructuredTestResult(unittest.TestResult):
    """Custom TestResult collecting detailed per-test telemetry and diagnostics."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[dict] = []
        self._test_start_time: float = 0.0

    def startTest(self, test: unittest.TestCase) -> None:
        super().startTest(test)
        self._test_start_time = time.perf_counter()

    def stopTest(self, test: unittest.TestCase) -> None:
        super().stopTest(test)
        duration = time.perf_counter() - self._test_start_time
        # Record test completion if not already marked as error/failure/skip
        test_id = test.id()
        existing = next((r for r in self.records if r["id"] == test_id), None)
        if existing:
            existing["duration"] = duration
        else:
            self.records.append(
                {
                    "id": test_id,
                    "classname": test.__class__.__module__ + "." + test.__class__.__name__,
                    "name": test._testMethodName,
                    "status": "passed",
                    "duration": duration,
                    "message": None,
                    "details": None,
                }
            )

    def addSuccess(self, test: unittest.TestCase) -> None:
        super().addSuccess(test)

    def addError(self, test: unittest.TestCase, err) -> None:
        super().addError(test, err)
        duration = time.perf_counter() - self._test_start_time
        self.records.append(
            {
                "id": test.id(),
                "classname": test.__class__.__module__ + "." + test.__class__.__name__,
                "name": getattr(test, "_testMethodName", str(test)),
                "status": "error",
                "duration": duration,
                "message": str(err[1]),
                "details": self._exc_info_to_string(err, test),
            }
        )

    def addFailure(self, test: unittest.TestCase, err) -> None:
        super().addFailure(test, err)
        duration = time.perf_counter() - self._test_start_time
        self.records.append(
            {
                "id": test.id(),
                "classname": test.__class__.__module__ + "." + test.__class__.__name__,
                "name": getattr(test, "_testMethodName", str(test)),
                "status": "failure",
                "duration": duration,
                "message": str(err[1]),
                "details": self._exc_info_to_string(err, test),
            }
        )

    def addSkip(self, test: unittest.TestCase, reason: str) -> None:
        super().addSkip(test, reason)
        duration = time.perf_counter() - self._test_start_time
        self.records.append(
            {
                "id": test.id(),
                "classname": test.__class__.__module__ + "." + test.__class__.__name__,
                "name": getattr(test, "_testMethodName", str(test)),
                "status": "skipped",
                "duration": duration,
                "message": reason,
                "details": None,
            }
        )


def generate_junit_xml(records: list[dict], total_time: float, output_path: str) -> None:
    """Generate standard JUnit XML formatted test report."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    suites_by_class: dict[str, list[dict]] = {}
    for r in records:
        suites_by_class.setdefault(r["classname"], []).append(r)

    total_tests = len(records)
    total_failures = sum(1 for r in records if r["status"] == "failure")
    total_errors = sum(1 for r in records if r["status"] == "error")
    total_skipped = sum(1 for r in records if r["status"] == "skipped")

    root = ET.Element(
        "testsuites",
        {
            "name": "DERA Test Suite",
            "tests": str(total_tests),
            "failures": str(total_failures),
            "errors": str(total_errors),
            "skipped": str(total_skipped),
            "time": f"{total_time:.3f}",
        },
    )

    for classname, suite_records in suites_by_class.items():
        suite_time = sum(r["duration"] for r in suite_records)
        suite_failures = sum(1 for r in suite_records if r["status"] == "failure")
        suite_errors = sum(1 for r in suite_records if r["status"] == "error")
        suite_skipped = sum(1 for r in suite_records if r["status"] == "skipped")

        suite_el = ET.SubElement(
            root,
            "testsuite",
            {
                "name": classname,
                "tests": str(len(suite_records)),
                "failures": str(suite_failures),
                "errors": str(suite_errors),
                "skipped": str(suite_skipped),
                "time": f"{suite_time:.3f}",
            },
        )

        for r in suite_records:
            case_el = ET.SubElement(
                suite_el,
                "testcase",
                {
                    "classname": r["classname"],
                    "name": r["name"],
                    "time": f"{r['duration']:.4f}",
                },
            )
            if r["status"] == "failure":
                fail_el = ET.SubElement(
                    case_el,
                    "failure",
                    {
                        "message": r.get("message") or "Test failed",
                        "type": "AssertionError",
                    },
                )
                fail_el.text = r.get("details") or ""
            elif r["status"] == "error":
                err_el = ET.SubElement(
                    case_el,
                    "error",
                    {
                        "message": r.get("message") or "Test execution error",
                        "type": "Exception",
                    },
                )
                err_el.text = r.get("details") or ""
            elif r["status"] == "skipped":
                ET.SubElement(
                    case_el,
                    "skipped",
                    {
                        "message": r.get("message") or "Test skipped",
                    },
                )

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def generate_json_summary(
    records: list[dict], total_time: float, output_path: str, suite_dir: str
) -> None:
    """Generate machine-readable JSON summary of test run."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    total_tests = len(records)
    total_failures = sum(1 for r in records if r["status"] == "failure")
    total_errors = sum(1 for r in records if r["status"] == "error")
    total_skipped = sum(1 for r in records if r["status"] == "skipped")
    total_passed = sum(1 for r in records if r["status"] == "passed")

    # Top 5 slowest tests
    sorted_by_duration = sorted(records, key=lambda r: r["duration"], reverse=True)
    slowest = [
        {"id": r["id"], "duration_ms": round(r["duration"] * 1000, 2)}
        for r in sorted_by_duration[:5]
    ]

    summary = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "suite_directory": suite_dir,
        "total": total_tests,
        "passed": total_passed,
        "failures": total_failures,
        "errors": total_errors,
        "skipped": total_skipped,
        "duration_seconds": round(total_time, 4),
        "status": "PASSED" if (total_failures == 0 and total_errors == 0) else "FAILED",
        "slowest_tests": slowest,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="DERA Test Reporter & JUnit Generator")
    parser.add_argument(
        "--test-dir",
        default="tests",
        help="Root directory for test discovery (default: 'tests')",
    )
    parser.add_argument(
        "--xml-output",
        default="reports/test-results.xml",
        help="Output path for JUnit XML report (default: 'reports/test-results.xml')",
    )
    parser.add_argument(
        "--json-output",
        default="reports/test-summary.json",
        help="Output path for JSON summary telemetry (default: 'reports/test-summary.json')",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose test output",
    )
    args = parser.parse_args()

    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    print(f"Discovering tests in '{args.test_dir}'...")
    start_time = time.perf_counter()

    loader = unittest.defaultTestLoader
    suite = loader.discover(args.test_dir)

    result = StructuredTestResult()
    suite.run(result)

    total_time = time.perf_counter() - start_time

    # Generate reports
    generate_junit_xml(result.records, total_time, args.xml_output)
    generate_json_summary(result.records, total_time, args.json_output, args.test_dir)

    total_tests = len(result.records)
    total_failures = len(result.failures)
    total_errors = len(result.errors)
    total_skipped = len(result.skipped)
    total_passed = total_tests - total_failures - total_errors - total_skipped

    print("\n" + "=" * 50)
    print("DERA Test Execution Telemetry")
    print("=" * 50)
    print(f"Total Tests Executed: {total_tests}")
    print(f"Passed:               {total_passed}")
    print(f"Failures:             {total_failures}")
    print(f"Errors:               {total_errors}")
    print(f"Skipped:              {total_skipped}")
    print(f"Execution Duration:   {total_time:.3f}s")
    print(f"JUnit XML Report:     {args.xml_output}")
    print(f"JSON Summary:         {args.json_output}")
    print("=" * 50)

    if result.failures:
        print("\n--- Failures ---")
        for test, err in result.failures:
            print(f"[FAIL] {test.id()}:\n{err}")

    if result.errors:
        print("\n--- Errors ---")
        for test, err in result.errors:
            print(f"[ERROR] {test.id()}:\n{err}")

    return 0 if (total_failures == 0 and total_errors == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
