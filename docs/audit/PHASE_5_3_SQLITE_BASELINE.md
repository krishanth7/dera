# Phase 5.3: SQLite Connector Baseline Audit

**DERA — Database Engineering & Reverse Analysis**  
*Understand Every Schema. Engineer Every Change.*

---

## 1. Executive Summary

This baseline audit establishes the engineering prerequisites, architectural foundation, and security boundary for **Phase 5.3: SQLite Connector**. DERA is implementing a production-grade, asynchronous, read-only database connector adapter for SQLite 3.x embedded databases.

SQLite operates directly against local filesystem resources rather than network sockets. Consequently, this milestone prioritizes **strict filesystem path isolation, directory traversal prevention, symlink redirection rejection, and defense-in-depth read-only URI enforcement** alongside comprehensive schema introspection using `sqlite_schema` and `PRAGMA` facilities.

---

## 2. Baseline Repository Metadata

- **Repository:** `https://github.com/krishanth7/dera`
- **Maintainer:** Bunga Krishanth (`@krishanth7`)
- **Base Commit SHA:** `6b2db493fa225ea91ca4d7fe7f94899b7a438bea`
- **Target Branch:** `main`
- **Implementation Branch:** `feat/phase-5.3-sqlite-connector`
- **Execution Date:** 2026-10-27
- **Audit Verdict:** **PROCEED WITH PHASE 5.3 IMPLEMENTATION**

---

## 3. Prerequisite Verification Matrix

| Component | Required Status | Verified Status | Evidence |
| :--- | :--- | :--- | :--- |
| **Phase 5.1 Connector Protocol** | Merged on `main` | **VERIFIED** | `DatabaseConnector` in `dera_connectors.protocol` |
| **Phase 5.1 Capability Model** | Merged on `main` | **VERIFIED** | `ConnectorCapabilities` in `dera_connectors.capabilities` |
| **Phase 5.1 Metadata Contracts** | Merged on `main` | **VERIFIED** | Pydantic v2 models in `dera_connectors.metadata` |
| **Phase 5.1 Error Taxonomy** | Merged on `main` | **VERIFIED** | `ConnectorError` hierarchy in `dera_connectors.errors` |
| **Phase 5.1 Conformance Suite** | Merged on `main` | **VERIFIED** | `BaseConnectorConformanceTests` in `dera_connectors.testing` |
| **Phase 5.2 PostgreSQL Adapter** | Merged on `main` | **VERIFIED** | `PostgresConnector` in `dera_connectors.postgresql` |
| **Phase 4 Multi-Tenant RBAC** | Available | **VERIFIED** | `ConnectorContext` workspace scoping |
| **Phase 4 Observability** | Available | **VERIFIED** | Sanitized metric tags & structured logging |
| **Zero-AI Project Invariant** | Enforced | **VERIFIED** | Zero generative AI or LLM dependencies in repository |

---

## 4. SQLite Driver Evaluation & Selection

| Evaluation Criterion | Python Standard `sqlite3` (Thread Executor) | `aiosqlite` | Raw C-FFI / `ctypes` |
| :--- | :--- | :--- | :--- |
| **Asynchronous Architecture** | Uses `asyncio.to_thread` for non-blocking I/O | Async event loop wrapping worker thread | Complex manual event-loop binding |
| **Dependency Footprint** | Zero external dependencies (batteries included) | Lightweight pure-Python wrapper over `sqlite3` | High maintenance overhead |
| **Read-Only URI Support** | Native `uri=True` with `?mode=ro` | Native support via `connect(..., uri=True)` | Manual flag configuration |
| **Cancellation Safety** | Interruptible via `sqlite3_interrupt` | Supported via `conn.interrupt()` | Unsafe signal handling |
| **Memory Isolation** | Standard C-runtime memory management | Standard C-runtime memory management | Potential memory leak surface |
| **Decision** | **PRIMARY SELECTION (`sqlite3` + `asyncio.to_thread`)** | Viable alternative but introduces external dependency | Rejected due to complexity |

---

## 5. Security & Filesystem Boundary Architecture

Unlike network databases (PostgreSQL, MySQL), SQLite connects directly to filesystem files. The connector enforces a multi-tier security model:

1. **Approved Storage Roots:** Databases must reside within explicit, server-configured workspace directories (`approved_storage_roots`).
2. **Path Normalization & Traversal Defense:** Absolute path resolution (`os.path.realpath`) rejects relative escapes (`../`), null-byte poisoning, and UNC/device path syntax (`/dev/`, `\\.\`, `CON:`, `NUL:`).
3. **Symlink Redirection Rejection:** Symlinks that resolve outside the approved root are rejected immediately with `ConnectorSecurityViolationError`.
4. **URI Mode Read-Only Enforcement:** Connections use `file:{escaped_path}?mode=ro` with `uri=True`.
5. **Session Safety:** Immediately upon connection checkout, the session executes `PRAGMA query_only = ON;` and `PRAGMA busy_timeout = <ms>;`.
6. **No Arbitrary ATTACH:** `ATTACH DATABASE` statements are strictly prohibited; schema introspection queries inspect only the approved database namespace (`main`).
7. **Extension Loading Disabled:** `enable_load_extension` is strictly disabled.
8. **Credential & Path Scrubbing:** Public error messages sanitize internal filesystem paths to prevent directory disclosure.

---

## 6. Implementation Scope & Deliverables

- `packages/connectors/src/dera_connectors/sqlite/`:
  - `configuration.py`: `SqliteConnectorConfig` with storage root bounds and timeout constraints.
  - `filesystem.py`: `validate_sqlite_path` for root containment, symlink verification, and file existence.
  - `connection.py`: `SqliteConnectionManager` with read-only URI connection and thread pool offloading.
  - `errors.py`: `map_sqlite_error` mapping `sqlite3.Error` codes to Phase 5.1 domain exceptions.
  - `types.py`: SQLite type affinity rules (INTEGER, TEXT, BLOB, REAL, NUMERIC) and declared type preservation.
  - `queries.py`: Pre-reviewed, parameterized queries for `sqlite_schema` and PRAGMA routines.
  - `catalog.py`: Introspection routines for tables, columns, keys, constraints, indexes, views, and triggers.
  - `capabilities.py`: `get_sqlite_capabilities` reporting supported vs unsupported features.
  - `adapter.py`: `SqliteConnector` implementing `DatabaseConnector`.
- `tests/connectors/sqlite/`: Unit, security, and conformance tests.
- `tests/integration/sqlite/`: End-to-end integration tests on disposable SQLite databases.
- `docs/connectors/sqlite/`: Comprehensive architectural and operational documentation.
- `docs/audit/PHASE_5_3_SQLITE_ACCEPTANCE.md`: Final qualification report.
