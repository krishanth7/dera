# DERA Database Connector Capability Matrix

> **Package:** `packages/connectors`  
> **Status:** Authoritative Support Matrix  
> **Maintainer:** Krishanth  
> **Last Verified:** 2026-10-26 (Commit `e550fdd`)  

---

## 1. Overview & Capability Evaluation Criteria

This matrix details the exact, evidence-based feature support for every target database engine in DERA.

Each database capability is classified using standardized status labels:
- **Implemented:** Code is merged in `main`, passes automated tests, and is usable in development.
- **In Development:** Adapter code or test fixtures exist, but full catalog extraction is not yet certified for release.
- **Planned:** Architecture is specified in the roadmap, but implementation has not started.
- **Unsupported:** Engine capability is explicitly not supported by DERA's deterministic metadata model.

---

## 2. Comprehensive Engine Capability Matrix

| Feature / Dimension | SQLite | PostgreSQL | Supabase (PG) | MySQL | MariaDB | Snowflake |
|---|---|---|---|---|---|---|
| **Dialect Identifier** | `sqlite` | `postgresql` | `postgresql` | `mysql` | `mariadb` | `snowflake` |
| **Connector Implementation** | **Implemented** | **In Development** | **Planned** | **Planned** | **Planned** | **Planned** |
| **Source File** | [`sqlite/connector.py`](../../packages/connectors/src/dera_connectors/sqlite/connector.py) | `postgresql/connector.py` | `postgresql/connector.py` | `mysql/connector.py` | `mariadb/connector.py` | `snowflake/connector.py` |
| **Connection Safety** | `PRAGMA query_only = ON;` + URI `mode=ro` | `SET TRANSACTION READ ONLY;` | `SET TRANSACTION READ ONLY;` + SSL | `SET SESSION TRANSACTION READ ONLY;` | `SET SESSION TRANSACTION READ ONLY;` | Role-based read-only session |
| **Tables & Columns** | **Supported** | Planned (Phase 5) | Planned (Phase 5) | Planned (Phase 6) | Planned (Phase 6) | Planned (Phase 8) |
| **Primary Keys** | **Supported** | Planned (Phase 5) | Planned (Phase 5) | Planned (Phase 6) | Planned (Phase 6) | Planned (Phase 8) |
| **Foreign Keys** | **Supported** | Planned (Phase 5) | Planned (Phase 5) | Planned (Phase 6) | Planned (Phase 6) | Planned (Phase 8) |
| **Indexes** | **Supported** | Planned (Phase 5) | Planned (Phase 5) | Planned (Phase 6) | Planned (Phase 6) | Planned (Phase 8) |
| **Views & Materialized Views** | Filtered Out (Tables only) | Planned (Phase 5) | Planned (Phase 5) | Planned (Phase 6) | Planned (Phase 6) | Planned (Phase 8) |
| **Enum / Custom Data Types** | **Unsupported** (SQLite typeless affinity) | Planned (Phase 5) | Planned (Phase 5) | Planned (Phase 6) | Planned (Phase 6) | Planned (Phase 8) |
| **Partitioned Tables** | **Unsupported** (Not in SQLite) | Planned (Phase 5) | Planned (Phase 5) | Planned (Phase 6) | Planned (Phase 6) | Planned (Phase 8) |
| **Automated Tests** | [`tests/integration/test_sqlite_connector.py`](../../tests/integration/test_sqlite_connector.py) | Ephemeral fixtures | Ephemeral fixtures | None | None | None |
| **Known Limitations** | SQLite does not enforce column type constraints natively; PRAGMA foreign_key_list required for composite keys. | Requires running PostgreSQL server instance for live integration testing. | Connection pooling (PgBouncer) requires transaction-level read-only syntax. | MySQL 5.7 vs 8.0 catalog syntax differences. | Similar to MySQL; MariaDB system-versioned tables require specialized catalog parsing. | High latency catalog querying; virtual warehouse billing considerations. |

---

## 3. Evidence-Based Verification Links

1. **SQLite Adapter Implementation:** [`packages/connectors/src/dera_connectors/sqlite/connector.py`](../../packages/connectors/src/dera_connectors/sqlite/connector.py)
2. **Read-Only Base Interface:** [`packages/connectors/src/dera_connectors/base/connector.py`](../../packages/connectors/src/dera_connectors/base/connector.py)
3. **Connector Integration Test:** [`tests/integration/test_sqlite_connector.py`](../../tests/integration/test_sqlite_connector.py)
4. **Boundary Mutation Tests:** [`tests/architecture/test_module_boundaries.py`](../../tests/architecture/test_module_boundaries.py)

---

## 4. Related Documentation

- [Connector Architecture & Safety](CONNECTOR_ARCHITECTURE.md)
- [Connectors Documentation Hub](README.md)
- [Core Domain Models](../core/README.md)
- [Database Security Specification](../security/DATABASE_SECURITY.md)
