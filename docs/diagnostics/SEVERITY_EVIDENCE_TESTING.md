# Diagnostic Testing Specification

## Overview

DERA Phase 8.5 mandates rigorous, deterministic test coverage across all diagnostic subsystems. Testing verifies severity derivation, evidence sanitization, recommendation safety, stable prioritization, suppression governance, and cross-engine portability.

## Test Matrix

| Test Suite | File Location | Scope Verified |
| :--- | :--- | :--- |
| **Severity Policy** | `tests/diagnostics/test_severity_policy.py` | Conservative severity, override authorization, policy versioning, rationales |
| **Evidence Traceability** | `tests/diagnostics/test_evidence_traceability.py` | Evidence validation, secret sanitization, completeness grading, matrix generation |
| **Recommendations** | `tests/diagnostics/test_recommendations.py` | Template selection, variable substitution, safety checks prohibiting destructive SQL |
| **Prioritization** | `tests/diagnostics/test_prioritization.py` | Score computation, stable deterministic multi-key ordering, tie-breaking |
| **Suppression Governance** | `tests/diagnostics/test_suppression_governance.py` | Fingerprint and object matching, expiration handling, audit trail logging |
| **End-to-End Integration** | `tests/diagnostics/test_phase_8_5_integration.py` | Pipeline execution from raw rules to explainable report with suppressions and overrides |
| **OpenAPI Snapshot** | `tests/contracts/test_openapi_snapshot.py` | Contract drift detection against `docs/api/openapi.v1.json` |

## Execution Protocol

All test suites must run deterministically without internet connectivity or external database dependencies:

```bash
python -m pytest tests/diagnostics/ -v
python -m pytest tests/contracts/test_openapi_snapshot.py -v
```
