# DERA Milestone 5.2 PostgreSQL Baseline Audit: PostgreSQL & Supabase PostgreSQL Connector

**Milestone:** Phase 5.2 — PostgreSQL & Supabase PostgreSQL Connector  
**Audit Date:** 2026-10-27  
**Base Commit SHA:** `f94797d`  
**Default Branch:** `main`  
**Target Branch:** `feat/phase-5.2-postgresql-supabase-connector`  
**Maintainer:** Bunga Krishanth (`@krishanth7`)  
**Standard:** Secure, deterministic, read-only, typed, resilient, testable, production-oriented  

---

## 1. Baseline Repository Inspection

A live audit was conducted on repository `https://github.com/krishanth7/dera` at base commit `f94797d`.

### Verification Matrix

| Subsystem | Verified Baseline Infrastructure | Status | Evidence |
|---|---|---|---|
| **Phase 5.1 Protocol** | Typed `DatabaseConnector` async protocol and context manager | **READY** | `packages/connectors/src/dera_connectors/protocol.py` |
| **Capability Model** | 17 `ConnectorCapability` enum items, 4 `CapabilityStatus` states | **READY** | `packages/connectors/src/dera_connectors/capabilities.py` |
| **Metadata Contracts** | Pydantic v2 `SchemaInfo`, `TableInfo`, `ColumnInfo`, `PrimaryKeyInfo`, `ForeignKeyInfo`, `UniqueConstraintInfo`, `CheckConstraintInfo`, `IndexInfo`, `ViewInfo` | **READY** | `packages/connectors/src/dera_connectors/metadata.py` |
| **Configuration & Secrets** | `ConnectorConfig`, `TLSSettings`, `TimeoutSettings`, `SecretStr` password protection | **READY** | `packages/connectors/src/dera_connectors/configuration.py` |
| **Connection Lifecycle** | Explicit state machine (`CREATED` -> `CONNECTING` -> `CONNECTED` -> `CLOSING` -> `CLOSED`) | **READY** | `packages/connectors/src/dera_connectors/lifecycle.py` |
| **Error Taxonomy** | Standardized domain errors (`ConnectorAuthenticationFailedError`, `ConnectorPermissionDeniedError`, `ConnectorTimeoutError`, etc.) | **READY** | `packages/connectors/src/dera_connectors/errors.py` |
| **Connector Registry** | Thread-safe engine registry with `register()`, `get_connector_class()`, `create()` | **READY** | `packages/connectors/src/dera_connectors/registry.py` |
| **Security & SSRF Boundaries** | Egress IP validation, cloud metadata blocking (`169.254.169.254`), diagnostic secret masking | **READY** | `packages/connectors/src/dera_connectors/security.py` |
| **Conformance Suite** | `BaseConnectorConformanceTests` abstract verification harness | **READY** | `packages/connectors/src/dera_connectors/testing/conformance.py` |
| **Test Suite Status** | 341 tests passing across backend platform | **READY** | `tests/` |

---

## 2. Driver Evaluation & Selection

We evaluated candidate PostgreSQL drivers for Python 3.12+ async operations:

1. **`asyncpg` (Selected):**
   - Already a vetted core dependency of the DERA platform (`asyncpg>=0.29.0`).
   - Native async binary PostgreSQL frontend/backend protocol implementation with high throughput.
   - Built-in connection cancellation (`Connection.cancel()`), statement timeout support, and native SSL context configuration.
   - Direct support for parameterized type-rich catalog queries (`Record` returning native Python datatypes).
   - Supabase compatibility: Direct connections (port 5432) and session poolers (port 6543) work natively. Transaction poolers (PgBouncer mode) prohibit server-side prepared statement caching; setting `statement_cache_size=0` enables robust compatibility with PgBouncer transaction pooling.
2. **`psycopg 3` (Alternative):**
   - Supports async connections; however, introducing it would add an additional binary C/Rust dependency alongside existing `asyncpg`.
3. **`SQLAlchemy` (Platform persistence only):**
   - Used for DERA's internal persistence. For external customer database introspection, direct catalog queries via `asyncpg` provide strict isolation from DERA's platform ORM models and avoid any customer database metadata leakage into internal engine state.

**Driver Decision:** Standardize on `asyncpg` for the PostgreSQL and Supabase PostgreSQL connector adapter.

---

## 3. Supported Metadata & Catalog Inspection Inventory

Inspection leverages PostgreSQL system catalogs (`pg_catalog`) via safe parameterized queries:
- **Schemas:** `pg_catalog.pg_namespace` filtered for user/accessible schemas.
- **Tables & Relational Objects:** `pg_catalog.pg_class` (ordinary tables `'r'`, partitioned tables `'p'`, foreign tables `'f'`).
- **Columns:** `pg_catalog.pg_attribute`, `pg_catalog.pg_type`, `pg_catalog.pg_attrdef`, `pg_catalog.pg_description`, capturing native data types, nullability, default expressions, identity flags (`attidentity`), and generated columns (`attgenerated`).
- **Primary Keys:** `pg_catalog.pg_constraint` (`contype = 'p'`) with ordered key columns.
- **Foreign Keys:** `pg_catalog.pg_constraint` (`contype = 'f'`) with referencing and referenced column arrays, deferrability, and referential actions (`confupdtype`, `confdeltype`).
- **Unique Constraints:** `pg_catalog.pg_constraint` (`contype = 'u'`).
- **Check Constraints:** `pg_catalog.pg_constraint` (`contype = 'c'`) with raw untrusted check clause text.
- **Indexes:** `pg_catalog.pg_index`, `pg_catalog.pg_class`, `pg_catalog.pg_am`, `pg_catalog.pg_indexes` supporting BTREE, HASH, GIN, GIST, BRIN, uniqueness, partial filter predicates, and expression indexes.
- **Views & Materialized Views:** `pg_catalog.pg_views`, `pg_catalog.pg_matviews`, and `pg_catalog.pg_class` (`'v'` and `'m'`).
- **Sequences:** `pg_catalog.pg_sequences`, `pg_catalog.pg_class` (`'S'`).
- **Partition Metadata:** `pg_catalog.pg_partitioned_table`, `pg_catalog.pg_inherits`.

---

## 4. Security Boundaries & Read-Only Enforcement

DERA enforces a five-layer defense-in-depth model:
1. **Layer 1 — API Boundary:** Only approved read-only metadata inspection methods are exposed on `DatabaseConnector`.
2. **Layer 2 — SQL Boundary:** Introspection executes only predefined, parameterized catalog queries against `pg_catalog`. No dynamic customer table row queries; no user-supplied SQL execution.
3. **Layer 3 — Session Hardening:** Every connection immediately executes:
   ```sql
   SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;
   SET statement_timeout = 30000;
   ```
4. **Layer 4 — Network & SSRF Defenses:** `validate_network_target` blocks AWS/GCP/Azure link-local metadata endpoints (`169.254.169.254`) and unauthorized internal network addresses unless explicitly configured.
5. **Layer 5 — Least-Privilege Role Policy:** Connector documentation specifies recommended database grants (`CONNECT`, `USAGE ON SCHEMA`, read access to catalogs; no `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`, `ALTER`, or `TRUNCATE`).

---

## 5. Known Compatibility Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| **Supabase Transaction Pooler (PgBouncer)** | `asyncpg` prepared statements fail on transaction-mode poolers | Detect pooler mode or configure `statement_cache_size=0` for transaction pooling. |
| **Mixed-case and Unicode Identifiers** | Incorrect unquoted identifiers in queries | Use strict parameterized catalog queries matching `nspname` and `relname` as string parameters. |
| **Large Catalog Memory Spikes** | Loading millions of column records simultaneously | Bounded catalog query results and deterministic ordering. |
| **Slow or Hanging Catalog Queries** | Inspection starvation under lock contention | Explicit statement timeout (`SET statement_timeout`) and client-side cancellation tokens. |

---

## 6. Proposed Implementation Plan

1. Package structure in `packages/connectors/src/dera_connectors/postgresql/`:
   - `configuration.py`: `PostgresConnectorConfig` (supporting `ssl_mode`, `provider`, `statement_timeout_ms`, `supabase_pooler_mode`).
   - `connection.py`: `PostgresConnectionManager` handling `asyncpg` connection establishment, TLS context construction, and read-only session initialization.
   - `errors.py`: PostgreSQL SQLSTATE error classifier mapping asyncpg exceptions to Phase 5.1 domain errors.
   - `queries.py`: Parameterized catalog queries against `pg_catalog`.
   - `catalog.py`: Introspection routines transforming catalog results into Phase 5.1 metadata models.
   - `adapter.py`: `PostgresConnector` implementing `DatabaseConnector`.
2. Register `PostgresConnector` with `default_connector_registry` for `DatabaseEngine.POSTGRESQL`.
3. Comprehensive test suite:
   - Conformance tests via `BaseConnectorConformanceTests`.
   - Unit tests for catalog queries, identifier escaping, and type mapping.
   - Supabase configuration and pooler compatibility tests.
   - Read-only security tests verifying transaction mutation rejection.
4. Comprehensive technical documentation in `docs/connectors/postgresql/` and acceptance audit in `docs/audit/PHASE_5_2_POSTGRESQL_ACCEPTANCE.md`.
