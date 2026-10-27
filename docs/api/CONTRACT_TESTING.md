# DERA API Contract Testing Guide

This guide details the contract verification framework, test suites, and execution instructions for validating DERA API stability and schema conformance.

---

## 1. Test Suite Architecture

Contract tests reside in [`tests/contracts/`](../../tests/contracts/) and are executed via Python's standard `unittest` framework and DERA's standardized test reporter.

| Test File | Focus & Verification Domain |
|---|---|
| [`test_request_schemas.py`](../../tests/contracts/test_request_schemas.py) | Required vs. optional fields, string length bounds, numeric bounds, nested models |
| [`test_response_schemas.py`](../../tests/contracts/test_response_schemas.py) | `DataEnvelope`, `CollectionEnvelope`, metadata serialization, item counts |
| [`test_error_contracts.py`](../../tests/contracts/test_error_contracts.py) | RFC 9457 `ProblemDetail`, `ErrorCode` taxonomy, exception-to-HTTP status mapping |
| [`test_pagination.py`](../../tests/contracts/test_pagination.py) | `PaginationParams` bounds, `PageInfo.create()` page math, `PaginatedResponse` |
| [`test_filtering.py`](../../tests/contracts/test_filtering.py) | `SortParams` injection rejection, `FilterOperator` allowlist, max 20 condition limit |
| [`test_identifiers.py`](../../tests/contracts/test_identifiers.py) | Slugs, UUIDs, PostgreSQL 63-byte identifiers, schema.table qualified tuples |
| [`test_serialization.py`](../../tests/contracts/test_serialization.py) | ISO 8601 UTC datetimes, decimal precision, rejection of NaN/Infinity, UTF-8 safety |
| [`test_openapi_snapshot.py`](../../tests/contracts/test_openapi_snapshot.py) | Zero-drift verification of live app schema against `docs/api/openapi.v1.json` |
| [`test_api_compatibility.py`](../../tests/contracts/test_api_compatibility.py) | Breaking-change detector validation across removed routes, methods, and parameters |

---

## 2. Running Contract Tests

### Execute Entire Test Suite with Telemetry & JUnit XML

```bash
python scripts/ci/test_reporter.py --test-dir tests/
```

### Execute Contract Tests Only

```bash
python -m unittest discover -s tests/contracts -p "test_*.py" -v
```

### Validate OpenAPI Snapshot Drift

```bash
python scripts/ci/validate_openapi.py --check
```

---

## 3. CI Telemetry & Artifacts

All test runs emit machine-readable telemetry:

* `reports/test-results.xml`: JUnit XML report for CI test runners.
* `reports/test-summary.json`: JSON execution summary (duration, passed, failed, skipped).
* `reports/manifest.json`: Cryptographic SHA-256 integrity manifest for test artifacts.
