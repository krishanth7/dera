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
