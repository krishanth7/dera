# Phase 5.4 Baseline Audit: MySQL & MariaDB Connector Adapters

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Milestone:** Phase 5.4 — MySQL & MariaDB Connectors  
> **Base Commit SHA:** `330ec932eec6c310cb2bc32e60057be6c01e67fa`  
> **Audit Date:** 2026-10-27  
> **Audit Status:** Verified Complete — Ready for Implementation  

---

## 1. Executive Summary

This baseline audit establishes the technical foundation for **Phase 5.4: MySQL & MariaDB Connectors**. Following the successful completion and verification of Phase 5.1 (Universal Connector Protocol), Phase 5.2 (PostgreSQL & Supabase), and Phase 5.3 (SQLite), Phase 5.4 introduces production-grade, asynchronous, read-only metadata adapters for the MySQL-family database engines:
- **MySQL Connector Adapter (`MySqlConnector`)**
- **MariaDB Connector Adapter (`MariaDbConnector`)**
- **Shared MySQL-Family Subsystem (`mysql_family`)**

In strict adherence to DERA Non-Negotiable Engineering Principles, both adapters are deterministic, read-only by design, fully typed, bounded by multi-tier network and SSRF security controls, and incorporate **Zero Artificial Intelligence, Zero LLM APIs, and Zero Machine-Learning inference**.

---

## 2. Verified Repository Prerequisites

| Component / Subsystem | Location | Status | Implementation Evidence |
|---|---|---|---|
| **Phase 5.1 Universal Protocol** | `packages/connectors/src/dera_connectors/protocol.py` | **Verified** | `DatabaseConnector` abstract protocol with async lifecycle and metadata methods |
| **Capability Model** | `packages/connectors/src/dera_connectors/capabilities.py` | **Verified** | `ConnectorCapability` enum and `ConnectorCapabilities` structured declaration model |
| **Metadata Contracts** | `packages/connectors/src/dera_connectors/metadata.py` | **Verified** | Pydantic v2 schemas for schemas, tables, columns, PKs, FKs, UQs, checks, indexes, views, triggers |
| **Error Taxonomy** | `packages/connectors/src/dera_connectors/errors.py` | **Verified** | RFC 9457-compatible error codes and exception hierarchy with credential masking |
| **Connection Lifecycle** | `packages/connectors/src/dera_connectors/lifecycle.py` | **Verified** | Explicit state machine (`CREATED` -> `CONNECTING` -> `CONNECTED` -> `CLOSING` -> `CLOSED`) |
| **Network & SSRF Guards** | `packages/connectors/src/dera_connectors/security.py` | **Verified** | IP address validation, cloud metadata blocking (`169.254.169.254`), private net filters |
| **Connector Registry** | `packages/connectors/src/dera_connectors/registry.py` | **Verified** | Factory and registry mapping `DatabaseEngine` to connector adapter constructors |
| **Reusable Conformance Suite** | `packages/connectors/src/dera_connectors/testing/conformance.py` | **Verified** | `BaseConnectorConformanceTests` validating protocol, lifecycle, ordering, and read-only boundaries |
| **Phase 5.2 PostgreSQL Adapter** | `packages/connectors/src/dera_connectors/postgresql/` | **Verified** | Merged in PR #44 (PostgreSQL 14–18, Supabase direct and pooler connection modes) |
| **Phase 5.3 SQLite Adapter** | `packages/connectors/src/dera_connectors/sqlite/` | **Verified** | Merged in PR #45 (SQLite 3.35+, filesystem isolation, `mode=ro`, type affinity 1–5) |
| **Authentication & RBAC** | `apps/api/src/dera_api/auth/` | **Verified** | Multi-tenant workspace isolation, JWT session tokens, role-based access control |
| **Background Job Workers** | `apps/api/src/dera_api/jobs/`, `workers/` | **Verified** | Async task queue, job dispatching, timeout enforcement, outbox pattern |
| **Observability & Logging** | `apps/api/src/dera_api/telemetry/` | **Verified** | Structured JSON logging, Prometheus metrics, sanitized operational telemetry |

---

## 3. Driver Evaluation & Selection Rationale

| Driver Candidate | Type | Async Model | TLS Support | Dependencies | Verdict & Justification |
|---|---|---|---|---|---|
| **PyMySQL** | Pure Python | Threaded (`asyncio.to_thread`) | Native Python `ssl.SSLContext` | Zero C-extensions | **SELECTED (Tier 1)**: Universally portable, zero binary build requirements, mature, fully compatible with both MySQL 8.x and MariaDB 10/11. |
| **asyncmy** | C-extension / Cython | Native Async | Native OpenSSL | Requires C compiler | Viable alternative, but introduces packaging and compilation complexity on certain runtime environments. |
| **mysqlclient** | C-extension (`libmysqlclient`) | Synchronous | Native C library | Heavy external C headers | Rejected: requires system-level MySQL client libraries which fail in minimal environments. |
| **aiomysql** | Async wrapper | Event loop | Standard SSL | Pure Python | Wraps PyMySQL; using PyMySQL directly via `asyncio.to_thread` guarantees cleaner thread cancellation and resource teardown. |

**Decision:** DERA adopts **`PyMySQL` (>=1.1.0)** wrapped asynchronously with Python's built-in `asyncio.to_thread`. This aligns directly with the proven architecture used by DERA's SQLite adapter in Phase 5.3, guaranteeing non-blocking FastAPI execution, robust socket timeout enforcement, zero binary compilation hazards, and uniform TLS verification across all deployment targets.

---

## 4. Architectural Separation: MySQL vs. MariaDB

While MySQL and MariaDB share a common wire protocol origin, modern versions exhibit significant metadata and syntactic differences that must not be conflated:

```text
┌─────────────────────────────────────────────────────────────────┐
│               DERA Universal DatabaseConnector Protocol         │
├────────────────────────────────┬────────────────────────────────┤
│       MySqlConnector           │       MariaDbConnector         │
│   (Engine: DatabaseEngine.MYSQL)│(Engine: DatabaseEngine.MARIADB)│
├────────────────────────────────┴────────────────────────────────┤
│             Shared MySQL-Family Metadata Subsystem              │
│                 (dera_connectors.mysql_family)                  │
│  - Parameterized INFORMATION_SCHEMA Queries                     │
│  - Read-Only Session Configuration (READ ONLY transactions)     │
│  - TLS Context Builder (verify-full, custom CA bundles)         │
│  - Network Destination & SSRF Validation                        │
│  - Exception Taxonomy Mapping & Credential Redaction            │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       ┌───────────────────┐           ┌───────────────────┐
       │   MySQL 8.0/8.4   │           │ MariaDB 10.11/11.4│
       └───────────────────┘           └───────────────────┘
```

### Critical Engine-Specific Distinctions

| Feature / Behavior | MySQL 8.0 / 8.4 LTS | MariaDB 10.11 / 11.4 LTS | DERA Metadata Strategy |
|---|---|---|---|
| **Engine Identification** | `SELECT VERSION()` lacks "MariaDB" | `SELECT VERSION()` contains "MariaDB" | Inspects version string and `SHOW VARIABLES LIKE 'version_comment'` |
| **CHECK Constraints** | Enforced in 8.0.16+; listed in `INFORMATION_SCHEMA.CHECK_CONSTRAINTS` | Supported in 10.2+; exposed in `INFORMATION_SCHEMA.TABLE_CONSTRAINTS` & `CHECK_CONSTRAINTS` | Engine-specific query adaptation with fallback to `TABLE_CONSTRAINTS` |
| **Functional / Expression Indexes** | Stored with `EXPRESSION` in `INFORMATION_SCHEMA.STATISTICS` | Not natively exposed in `STATISTICS` in identical structure | Distinguish expression terms without inventing fake column names |
| **Generated Columns** | `STORED` vs `VIRTUAL` in `COLUMNS.EXTRA` | `STORED` (or `PERSISTENT`) vs `VIRTUAL` | Normalize to universal `is_generated` and preserve raw syntax |
| **Invisible Indexes** | Supported via `IS_VISIBLE` in `STATISTICS` | `IGNORED` keyword in MariaDB 10.6+ | Map to `engine_specific["is_visible"]` |
| **System Databases** | `information_schema`, `performance_schema`, `mysql`, `sys` | `information_schema`, `performance_schema`, `mysql`, `sys` | Exclude from user schema listings by default |

---

## 5. Security & Read-Only Defense in Depth

1. **Network & SSRF Guard:** Every target hostname and IP is validated via `validate_database_destination` before connection initiation, blocking AWS/GCP/Azure cloud metadata endpoints (`169.254.169.254`) and loopback destinations unless explicitly permitted.
2. **Strict TLS Enforcement:** Standard TLS configuration (`require`, `verify-ca`, `verify-full`) verifies server certificates against trusted CA bundles, preventing silent downgrade.
3. **Session Read-Only Mode:** Every checkout from the connection pool executes:
   ```sql
   SET SESSION TRANSACTION READ ONLY;
   SET SESSION max_execution_time = 30000;
   ```
4. **Least-Privilege Role:** Requires only `SELECT` privileges on target databases and `INFORMATION_SCHEMA`. No `SUPER`, `PROCESS`, or `FILE` privileges are requested.
5. **Mutation Interception:** In addition to read-only transaction mode, the connector interface exposes no mutation or DDL methods.

---

## 6. Implementation Sequence

1. Update `pyproject.toml` to declare `pymysql>=1.1.0`.
2. Implement `dera_connectors.mysql_family`:
   - Connection manager, connection pool, and thread-safe execution wrapper.
   - Network security and SSRF destination validation.
   - Standardized `INFORMATION_SCHEMA` queries.
   - Catalog introspection functions (schemas, tables, columns, keys, constraints, indexes, views, triggers).
   - Type mapping and engine-specific normalization.
   - Error mapping and exception taxonomy.
3. Implement `dera_connectors.mysql`:
   - `MySqlConnectorConfig`
   - `MySqlConnector` adapter
   - MySQL 8.x capability reporting
4. Implement `dera_connectors.mariadb`:
   - `MariaDbConnectorConfig`
   - `MariaDbConnector` adapter
   - MariaDB 10.x/11.x capability reporting
5. Register both adapters in `dera_connectors.registry`.
6. Implement comprehensive test suites:
   - MySQL & MariaDB configuration tests.
   - Network security & SSRF prevention tests.
   - Catalog query unit tests.
   - Error mapping and credential redaction tests.
   - Conformance test suites (`BaseConnectorConformanceTests`).
   - Live integration tests against disposable testbeds.
   - Read-only mutation rejection tests.
7. Create comprehensive technical documentation across `docs/connectors/mysql/`, `docs/connectors/mariadb/`, and `docs/connectors/mysql-family/`.
8. Complete Phase 5.4 acceptance audit in `docs/audit/PHASE_5_4_MYSQL_MARIADB_ACCEPTANCE.md`.
9. Submit reviewable pull request on `feat/phase-5.4-mysql-mariadb-connectors`.
