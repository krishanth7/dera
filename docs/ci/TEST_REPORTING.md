# DERA Test Reporting & Telemetry Standardization

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Maintainer:** Bunga Krishanth (`@krishanth7`)  
> **Classification:** Official DevSecOps Test Infrastructure Standard  

---

## 1. Overview & Objectives

Clear, structured test reporting transforms raw test outputs into actionable diagnostic telemetry. DERA standardizes test execution reporting across all Python and TypeScript test suites using open, machine-readable specifications:
* **JUnit XML (`reports/test-results.xml`):** Industry-standard XML format parseable by CI/CD aggregators, test dashboards, and pull request summary bots.
* **JSON Summary (`reports/test-summary.json`):** Machine-readable telemetry capturing pass/fail rates, execution durations, and per-test timing benchmarks.
* **Console Diagnostics:** Structured human-readable tables detailing failure tracebacks, error contexts, and slowest-executing tests.

---

## 2. Standardized Test Reporter (`scripts/ci/test_reporter.py`)

DERA provides an in-tree test runner and reporter built strictly on the Python standard library (`unittest` and `xml.etree.ElementTree`), eliminating third-party dependencies while providing comprehensive telemetry:

```bash
# Execute full test suite with JUnit XML and JSON telemetry
python scripts/ci/test_reporter.py --test-dir tests/

# Specify custom output locations
python scripts/ci/test_reporter.py --test-dir tests/unit --xml-output reports/unit-results.xml --json-output reports/unit-summary.json
```

---

## 3. JUnit XML Schema Specifications

The generated JUnit XML adheres to standard CI schemas:

```xml
<?xml version='1.0' encoding='utf-8'?>
<testsuites name="DERA Test Suite" tests="116" failures="0" errors="0" skipped="3" time="0.855">
  <testsuite name="architecture.test_module_boundaries.TestArchitectureBoundaries" tests="5" failures="0" errors="0" skipped="0" time="0.039">
    <testcase classname="architecture.test_module_boundaries.TestArchitectureBoundaries" name="test_core_package_independence" time="0.0134" />
    <testcase classname="architecture.test_module_boundaries.TestArchitectureBoundaries" name="test_zero_ai_dependencies_in_packages" time="0.0251" />
  </testsuite>
</testsuites>
```

### Element Attributes
* `<testsuites>`: Root aggregator containing total `tests`, `failures`, `errors`, `skipped`, and aggregate `time`.
* `<testsuite>`: Class-level grouping mapping to specific test classes.
* `<testcase>`: Individual test method with execution duration in fractional seconds (`time`).
* `<failure>` / `<error>`: Child nodes populated on failure containing the error message and full exception traceback.
* `<skipped>`: Child node populated when a test is skipped with `@unittest.skip()`.

---

## 4. JSON Telemetry & Slow Test Observability

The companion JSON summary records run metadata and automatically isolates the top 5 slowest test cases to assist maintainers in detecting performance regressions:

```json
{
  "timestamp": "2026-10-27T05:47:24.568926+00:00",
  "suite_directory": "tests",
  "total": 116,
  "passed": 113,
  "failures": 0,
  "errors": 0,
  "skipped": 3,
  "duration_seconds": 0.855,
  "status": "PASSED",
  "slowest_tests": [
    {
      "id": "docs.test_language_navigation.TestLanguageNavigation.test_idempotent_and_deterministic_output",
      "duration_ms": 64.54
    },
    {
      "id": "integration.test_sqlite_connector.TestSqliteConnector.test_inspect_table_columns_and_constraints",
      "duration_ms": 62.45
    }
  ]
}
```

---

## 5. Failure Diagnostics & Evidence Collection

When any CI step encounters an unhandled exception or assertion failure:
1. **Exit Code Preservation:** The test reporter strictly exits with non-zero code `1` if any failure or error occurs; failures are never suppressed.
2. **Failure Artifact Upload (`if: failure()`):** In `.github/workflows/ci.yml`, the `Upload Failure Diagnostics` step uploads `reports/` with a shortened 5-day retention period.
3. **Actionable Traces:** Maintainers can inspect the exact failing line and assertion without needing to re-run the workflow with verbose flags.

---

## 6. Frontend Test & Build Reporting

For TypeScript and monorepo workspace packages (`packages/contracts`, `apps/web`):
* `npm run typecheck` (`tsc --noEmit`): Validates static types across workspaces, emitting compiler error diagnostics.
* `npm run build`: Validates production bundle generation, verifying asset and schema contract compilation.
