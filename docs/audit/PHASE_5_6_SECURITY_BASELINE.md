# Phase 5.6 Baseline Audit: Read-Only Enforcement, Timeouts & Safety

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Milestone:** Phase 5.6 — Read-Only Enforcement, Timeouts & Safety  
**Base Commit SHA:** `9d1be2d56f2c79a7030ee19af01ed62c2a1ec490`  
**Implementation Branch:** `security/phase-5.6-connector-safety`  
**Date:** October 27, 2026  
**Auditor:** Principal Application Security Architect & DevSecOps Engineering Team  

---

## 1. Executive Summary

Phase 5.6 is the concluding milestone of **Phase 5 (Database Connectors & Metadata Inspection)**. It conducts the comprehensive cross-connector security and reliability qualification across all supported database adapters in DERA:
- **PostgreSQL** (and **Supabase-hosted PostgreSQL**)
- **SQLite**
- **MySQL**
- **MariaDB**
- **Metadata Normalization & Identity Engine** (Phase 5.5)

The objective of Phase 5.6 is to guarantee that DERA's connector layer operates under strict, fail-closed security invariants:
1. **Strict Read-Only Enforcement:** Introspection queries are restricted to metadata catalogs only; zero customer DDL/DML, stored procedure invocation, or arbitrary user SQL execution is permitted.
2. **SSRF & Network Destination Boundaries:** All network connections are validated against RFC 1918 private address ranges, RFC 3927 link-local addresses, loopback interfaces, cloud metadata endpoints (`169.254.169.254`, `metadata.google.internal`), and dangerous service ports.
3. **SQLite Filesystem Containment:** SQLite file paths are canonicalized, validated against approved workspace storage roots, checked for symlink escape attacks, and guarded against operating system device files (`CON`, `PRN`, `NUL`, `/dev/*`).
4. **Multi-Tenant Workspace Isolation:** Database connections, cached metadata, and secret resolutions are strictly scoped to authenticated workspace IDs. Cross-workspace access is denied prior to secret resolution.
5. **Centralized Timeouts & Deadlines:** All multi-step connection and inspection routines are governed by bounded deadlines that propagate throughout sub-queries, preventing infinite hangs or resource exhaustion.
6. **Cooperative & Asynchronous Cancellation:** Operations support cancellation tokens that abort socket reads, rollback in-flight read transactions, and release pool resources promptly.
7. **Resource Limits & Denial-of-Service Defense:** Strict limits are enforced on maximum returned result rows (50,000), identifier lengths (1,024 characters), SQL definition sizes (1MB), and total schema objects (100,000).
8. **Credential Confidentiality & Redaction:** Credentials and connection strings are masked across all error messages, structured logs, diagnostics payloads, and stable object IDs.
9. **Zero AI/LLM Dependency:** All security controls, query policies, and catalog inspections are 100% deterministic, rule-based, and auditable.

---

## 2. Verified Prerequisites Status

| Prerequisite Subsystem | Repository Path | Base Commit Status | Verification Result |
| :--- | :--- | :--- | :--- |
| **Phase 5.1 Connector Protocol** | `packages/connectors/src/dera_connectors/` | Integrated (`9d1be2d`) | **VERIFIED** — `DatabaseConnector`, `CapabilityRegistry`, `ConnectorContext`, `ConnectorLifecycleManager`. |
| **Phase 5.2 PostgreSQL & Supabase** | `packages/connectors/src/dera_connectors/postgresql/` | Integrated (`9d1be2d`) | **VERIFIED** — Asyncpg-based catalog inspection, schema isolation, JSON/JSONB/Array/Domain types. |
| **Phase 5.3 SQLite Connector** | `packages/connectors/src/dera_connectors/sqlite/` | Integrated (`9d1be2d`) | **VERIFIED** — Filesystem boundary, PRAGMA/catalog inspection, STRICT/WITHOUT ROWID, type affinities. |
| **Phase 5.4 MySQL & MariaDB** | `packages/connectors/src/dera_connectors/mysql/`, `mariadb/`, `mysql_family/` | Integrated (`9d1be2d`) | **VERIFIED** — PyMySQL thread pooling, INFORMATION_SCHEMA extraction, session read-only, engine distinction. |
| **Phase 5.5 Metadata Normalization** | `packages/core/src/dera/metadata/` | Integrated (`9d1be2d`) | **VERIFIED** — Strongly typed canonical contracts, stable SHA-256 object IDs, deterministic ordering, UTF-8 serialization. |
| **Phase 4 Authentication & RBAC** | `apps/api/src/dera_api/auth/` | Integrated (`9d1be2d`) | **VERIFIED** — JWT verification, workspace membership validation, role permission checks. |
| **Phase 4 Background Jobs** | `apps/api/src/dera_api/jobs/` | Integrated (`9d1be2d`) | **VERIFIED** — Celery task dispatching, heartbeat monitoring, outbox worker dispatch. |
| **Phase 4 Structured Logging** | `apps/api/src/dera_api/core/` | Integrated (`9d1be2d`) | **VERIFIED** — Structured JSON logging, correlation ID tracking, exception masking. |
| **Current Test Suite Baseline** | `tests/` | 534 tests passing (532 passed, 2 skipped, 0 failed) | **VERIFIED** — Baseline test suite runs cleanly in 66s. |

---

## 3. Connector Security Inventory

| Connector | Engine Target | Transport / Driver | Security Focus & Invariants |
| :--- | :--- | :--- | :--- |
| **PostgreSQL** | PostgreSQL 13 - 17 | `asyncpg` (asyncio TCP) | Read-only session transaction mode, `statement_timeout`, TLS certificate chain verification, catalog allowlist. |
| **Supabase PostgreSQL** | Supabase managed pg | `asyncpg` via PgBouncer | Transaction pooler compatibility, session read-only fallback, TLS SNI validation, tenant isolation. |
| **SQLite** | SQLite 3.35+ | `aiosqlite` (in-process) | Filesystem root containment, canonical realpath resolution, `mode=ro` URI parameter, symlink escape defense. |
| **MySQL** | MySQL 8.0+ | `pymysql` via threadpool | `SET SESSION TRANSACTION READ ONLY`, `max_execution_time`, TLS verification, `INFORMATION_SCHEMA` query allowlist. |
| **MariaDB** | MariaDB 10.5+ | `pymysql` via threadpool | Engine-specific read-only parameters, JSON alias handling, session reset on pool return. |

---

## 4. Security Gap Analysis & Missing Controls

Prior to Phase 5.6, foundational controls were established in early milestones (e.g. `dera_connectors.security.validate_read_only_sql` and `validate_network_target`). However, a thorough application security audit identified the following gaps that require cohesive, cross-cutting remediation:

1. **Monolithic Security Module:** `dera_connectors.security` was a single file (`security.py`) lacking modular decomposition for query allowlists, centralized timeout budgets, cancellation propagation, workspace authorization, and structured security auditing.
2. **Metadata Query Allowlist Registry:** Connectors executed catalog queries without an explicit, centrally governed allowlist defining approved operation IDs, authorized query templates, and bounded output row limits.
3. **Multi-Step Deadline Propagation:** Individual queries honored isolated timeouts, but complex multi-step schema inspections lacked a centralized `DeadlineTracker` enforcing an overall inspection budget across all catalog calls.
4. **Enhanced DNS Rebinding Defense:** Hostname validation checked string representations and IP literals, but did not guard against DNS rebinding attacks where host resolution shifts between pre-flight check and TCP handshake.
5. **Cross-Tenant Storage Segregation:** SQLite path checks validated approved roots, but did not explicitly tie approved roots to authenticated `workspace_id` parameters to prevent Workspace A from accessing Workspace B's database files.
6. **Centralized Security Audit Logging:** Connector security events (SSRF blocks, read-only violations, tenant mismatches) were raised as exceptions but not recorded in a structured security audit log with correlation IDs and redaction guarantees.
7. **Comprehensive Adversarial Test Suites:** Existing tests covered positive paths and basic SQL regex checks, but lacked adversarial test cases for stacked queries, SQL comment bypasses, symlink escapes, DNS resolution spoofing, and cancellation aborts during active queries.

---

## 5. Remediation & Implementation Plan

| Action Item | Target Component | Architecture |
| :--- | :--- | :--- |
| **1. Modular Security Package** | `packages/connectors/src/dera_connectors/security/` | Decompose into 13 dedicated modules (`policy`, `authorization`, `destinations`, `credentials`, `readonly`, `query_policy`, `timeouts`, `cancellation`, `resource_limits`, `isolation`, `redaction`, `errors`, `audit`). |
| **2. Query Allowlist Registry** | `security/query_policy.py` | Implement `ApprovedMetadataQueryRegistry` mapping engine operations to immutable query templates with parameter binding and row limits. |
| **3. Centralized Deadline Tracker** | `security/timeouts.py` | Implement `TimeoutBudget` and `DeadlineTracker` enforcing overall inspection deadlines (default 120s) and remaining-time calculations. |
| **4. Cooperative Cancellation** | `security/cancellation.py` | Implement `CancellationToken` with parent-child linkage, callback dispatch, and async event triggers. |
| **5. Strict SSRF & DNS Defense** | `security/destinations.py` | Enforce RFC 1918, RFC 3927 link-local, loopback, cloud metadata (`169.254.169.254`), dangerous port blocks, and IP literal pinning. |
| **6. Workspace Isolation** | `security/authorization.py` & `isolation.py` | Enforce order of authorization: Authenticate -> Authorize Workspace -> Authorize Connection -> Validate Operation -> Resolve Secret -> Validate Destination -> Execute Query. |
| **7. SQLite Containment** | `security/isolation.py` | Enforce canonical `os.path.realpath`, workspace directory containment, symlink escape rejection, and Windows device name blocking. |
| **8. Structured Security Auditing** | `security/audit.py` | Record `SecurityAuditEvent` capturing workspace, caller, engine, operation ID, latency, and status (`ALLOW`, `DENY`, `VIOLATION`) with zero credential leakage. |
| **9. Unified Security Policy** | `security/policy.py` | Provide `ConnectorSecurityPolicy` acting as the single enforcement entry point for all connector adapters. |
| **10. Adversarial Test Suites** | `tests/security/` & `tests/integration/` | Build unit, adversarial, network, filesystem, tenant, and regression test suites. |

---

## 6. Verification Strategy

The qualification of Phase 5.6 requires passing the following automated validation gates:
1. `python -m unittest discover tests/security`: All connector security unit and negative tests pass.
2. `python -m unittest discover tests/connectors`: All connector catalog and adapter unit tests pass without regression.
3. `python -m unittest discover tests`: The entire DERA test suite (530+ tests) passes with 0 failures.
4. `npm run docs:lint`: 100% clean markdown formatting across all audit and security docs.
5. `python scripts/ci/validate_docs.py`: 100% link and anchor integrity across all documentation.
6. `python -m ruff check packages tests`: Zero lint errors across packages and test suites.
7. `python -m ruff format --check packages tests`: Code formatting verified.
8. `npm run typecheck`: TypeScript verification clean.
