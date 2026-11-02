# DERA API Architecture & Contracts

> **Understand Every Schema. Engineer Every Change.**

This directory establishes the authoritative standards, schemas, error taxonomies, and testing procedures for the **DERA REST API Gateway** (Phase 4.2).

---

## Architecture Overview

DERA provides an enterprise-oriented, deterministic, and strongly-typed API architecture adhering to the following design pillars:

1. **Zero-AI & Deterministic Execution**: No artificial intelligence, machine learning inference, generative services, or non-deterministic heuristics are permitted within API processing.
2. **Explicit Type Safety**: Every request, query parameter, path identifier, and response is governed by typed Pydantic v2 schemas and documented via OpenAPI 3.1.
3. **Standard Error Handling**: All operational, domain, and validation errors are normalized into RFC 9457-compliant Problem Details (`application/problem+json`).
4. **Read-Only Database Guarantees**: In alignment with DERA core principles, all analysis and reverse-engineering capabilities operate strictly read-only.
5. **Zero-Drift OpenAPI Governance**: The OpenAPI contract is maintained as a versioned, tested artifact (`docs/api/openapi.v1.json`) with automated breaking-change detection.

---

## Documentation Index

| Specification Document | Scope & Focus |
|---|---|
| [Authentication & Workspace API](AUTHENTICATION_API.md) | Opaque session authentication, CSRF rules, workspace lifecycle, and member RBAC |
| [API Contract Standard](API_CONTRACT_STANDARD.md) | Resource naming, HTTP verbs, status codes, field casing, and JSON formatting |
| [RFC 9457 Error Model](ERROR_MODEL.md) | Problem Details structure, error taxonomy codes, remediation, and retry semantics |
| [Validation Policy](VALIDATION_POLICY.md) | Pydantic v2 validation rules, bounded collections, identifier syntax, and security |
| [Pagination & Filtering](PAGINATION_AND_FILTERING.md) | Offset and cursor pagination, allowlisted sorting, and bounded filter expressions |
| [Versioning & Compatibility](VERSIONING_AND_COMPATIBILITY.md) | API version lifecycle, additive vs. breaking change policy, and deprecation |
| [OpenAPI Governance](OPENAPI_GOVERNANCE.md) | Contract generation, drift verification, and CI breaking-change gate |
| [Contract Testing Guide](CONTRACT_TESTING.md) | Reusable test suites, parameter matrices, and regression verification |

---

## Canonical OpenAPI Specification

The authoritative OpenAPI 3.1 snapshot is committed at:

* [`openapi.v1.json`](openapi.v1.json)

To verify contract compliance locally:

```bash
# Verify live OpenAPI spec matches snapshot (zero drift)
python scripts/ci/validate_openapi.py --check

# Regenerate snapshot after intentional additive modifications
python scripts/ci/validate_openapi.py --update
```

## SQL Engineering Diagnostics (Phase 10.2)

The dependent Phase 10.2 branch adds authenticated static SQL diagnostics at
`POST /api/v1/sql-engineering/diagnostics?workspace_id=<UUID>`, preserving the Phase 10.1
analysis endpoint. See the [API contract](../phase-10/PHASE_10_2_API_CONTRACT.md),
[rule catalog](../phase-10/PHASE_10_2_RULE_CATALOG.md) and
[structural scoring formula](../phase-10/PHASE_10_2_COMPLEXITY_SCORING.md).
No SQL execution or automated rewrite is provided.

## Imported Execution Plans (Phase 10.3)

Authenticated offline `POST /api/v1/sql-engineering/execution-plans/analyze` uses the [plan API contract](../phase-10/PHASE_10_3_API_CONTRACT.md). No live EXPLAIN or SQL execution.
