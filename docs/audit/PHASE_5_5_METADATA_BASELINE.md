# Phase 5.5 Baseline Audit: Metadata Normalization & Identity

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Milestone:** Phase 5.5 — Metadata Normalization & Identity  
**Base Commit SHA:** `319d754da36a546842ecfddbb41b08339f176b99`  
**Implementation Branch:** `feat/phase-5.5-metadata-normalization-identity`  
**Date:** October 27, 2026  
**Auditor:** Principal Database Architecture & Metadata Normalization Engineering Team  

---

## 1. Executive Summary

Phase 5.5 establishes DERA's canonical metadata normalization and object identity engine. This subsystem acts as the deterministic translation and normalization bridge between the external database connectors implemented in Phases 5.1 through 5.4 (PostgreSQL, Supabase PostgreSQL, SQLite, MySQL, and MariaDB) and the downstream reverse engineering and dependency graph engine (Phase 6).

In strict compliance with DERA's foundational principles, the normalization layer:
- Operates 100% deterministically without AI, LLM, or probabilistic heuristics.
- Preserves native database semantics while classifying entities into strongly typed canonical representations.
- Assigns cryptographic, collision-resistant, deterministic object identities (`ObjectId`).
- Records complete provenance, collection timestamps, and capability/visibility states.
- Generates reproducible, canonical JSON serialization with deterministic attribute and collection ordering.

---

## 2. Verified Prerequisites Status

| Prerequisite Subsystem | Repository Path | Merge / Commit Status | Verification Result |
| :--- | :--- | :--- | :--- |
| **Phase 5.1 Universal Connector Protocol** | `packages/connectors/src/dera_connectors/` | Integrated (`319d754`) | **VERIFIED** — `DatabaseConnector`, `CapabilityRegistry`, `ConnectorContext`, `ConnectorLifecycleManager`. |
| **Phase 5.1 Metadata Contracts** | `packages/connectors/src/dera_connectors/metadata.py` | Integrated (`319d754`) | **VERIFIED** — `SchemaInfo`, `TableInfo`, `ColumnInfo`, `PrimaryKeyInfo`, `ForeignKeyInfo`, `UniqueConstraintInfo`, `CheckConstraintInfo`, `IndexInfo`, `ViewInfo`, `TriggerInfo`, `DatabaseMetadataReport`. |
| **Phase 5.2 PostgreSQL & Supabase Adapter** | `packages/connectors/src/dera_connectors/postgresql/` | Integrated (`319d754`) | **VERIFIED** — Asyncpg-based catalog inspection, schema isolation, JSON/JSONB/Array/Domain types. |
| **Phase 5.3 SQLite Adapter** | `packages/connectors/src/dera_connectors/sqlite/` | Integrated (`319d754`) | **VERIFIED** — Filesystem boundary, PRAGMA/catalog inspection, STRICT/WITHOUT ROWID, type affinities. |
| **Phase 5.4 MySQL & MariaDB Adapters** | `packages/connectors/src/dera_connectors/mysql/`, `mariadb/`, `mysql_family/` | Integrated (`319d754`) | **VERIFIED** — PyMySQL thread pooling, INFORMATION_SCHEMA extraction, session read-only, engine distinction. |
| **Phase 4 Backend Infrastructure** | `apps/api/src/dera_api/` | Integrated (`319d754`) | **VERIFIED** — FastAPI gateway, multi-tenant workspace isolation, RBAC, background Celery jobs. |
| **Test Suite Baseline** | `tests/` | 495 tests passing (493 passed, 2 skipped, 0 failed) | **VERIFIED** — Full test suite passing in 61s. |

---

## 3. Architecture Analysis & Target Pipeline

The canonical normalization engine converts engine-specific connector metadata reports into canonical, immutable metadata representations with stable object identities:

```text
+---------------------------------------------------------------------------------+
|                                External Database Engines                        |
|              PostgreSQL | Supabase | SQLite | MySQL | MariaDB                   |
+---------------------------------------------------------------------------------+
                                        |
                                        v (Phase 5.1-5.4 Connectors)
+---------------------------------------------------------------------------------+
|                       Universal DatabaseMetadataReport                          |
|         schemas, tables, columns, constraints, indexes, views, triggers         |
+---------------------------------------------------------------------------------+
                                        |
                                        v (Phase 5.5 Normalization Pipeline)
+---------------------------------------------------------------------------------+
|                       dera.metadata (Canonical Engine)                          |
|  1. Input Validation & Capability Assessment                                    |
|  2. Engine-Specific Adapter Normalization (PostgreSQL, SQLite, MySQL, MariaDB)  |
|  3. Identifier Normalization (Preserving Case & Quoting Semantics)              |
|  4. Canonical Type Classification & Attribute Preservation                      |
|  5. Cryptographic Stable Object ID Generation (SHA-256 Digest)                  |
|  6. Reference Integrity & Collision Detection                                  |
|  7. Deterministic Multi-Level Ordering                                          |
|  8. Canonical UTF-8 Serialization                                               |
+---------------------------------------------------------------------------------+
                                        |
                                        v (Downstream Consumer)
+---------------------------------------------------------------------------------+
|                     Canonical Database Schema Snapshot                          |
|         Ready for Phase 5.6 Safety Qualification & Phase 6 Graph Synthesis      |
+---------------------------------------------------------------------------------+
```

---

## 4. Key Design Decisions

1. **Package Location:**
   - The canonical metadata normalization layer is implemented in [`packages/core/src/dera/metadata`](../../packages/core/src/dera/metadata) with a top-level facade at [`packages/core/src/dera_metadata`](../../packages/core/src/dera_metadata).
   - This ensures zero external framework dependencies and seamless integration with existing core graph and diagnostic utilities.
2. **Stable Object Identity Formulation:**
   - Identity must be deterministic across inspection runs and unique across workspaces, connections, engines, namespaces, and object kinds.
   - Digest algorithm: SHA-256 over length-prefixed canonical components:
     `v1|workspace_id|connection_id|engine|namespace|object_kind|parent_id|native_name`
   - Formatted as `dera:<object_kind>:<24_hex_digits>`.
3. **Canonical Type Taxonomy:**
   - Standard categories: `INTEGER`, `DECIMAL`, `FLOAT`, `BOOLEAN`, `TEXT`, `BINARY`, `DATE`, `TIME`, `TIMESTAMP`, `JSON`, `UUID`, `ENUM`, `SET`, `ARRAY`, `SPATIAL`, `OTHER`, `UNKNOWN`.
   - Native engine type string, precision, scale, character length, and engine-specific attributes are fully preserved alongside the canonical category.
4. **Contract Versioning:**
   - The canonical metadata contract is explicitly versioned as `1.0.0`.
5. **Deterministic Serialization:**
   - Enforces key sorting, explicit null serialization, RFC 3339 UTC timestamps, and stable list ordering.

---

## 5. Identified Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Cross-Engine Identifier Case Folding** | Postgres folds unquoted to lowercase; SQLite/MySQL case sensitivity depends on collation and filesystem. Global lowercasing would destroy fidelity. | Preserve exact native identifier text. Compute case-preserving identities with explicit quoting metadata. |
| **Unnamed Constraints** | SQLite and older MySQL versions may omit explicit constraint names. | Generate deterministic surrogate identity incorporating parent table and sorted column terms without fabricating false native names. |
| **Synthetic View / Trigger Expressions** | Malicious or untrusted view definitions could be injected into metadata. | Treat view/trigger definitions as raw, unexecuted text payloads. Apply bounded size limits (e.g. 1MB max). |
| **Object Identity Collisions** | Different schemas with same table name or same column names in different tables colliding. | Use hierarchical parent identity chaining and strict length-prefixed SHA-256 component hashing. |

---

## 6. Implementation Plan & Phases

1. **Module Scaffolding:** Create `enums.py`, `errors.py`, `identifiers.py`, `provenance.py`, `identity.py`, and `contracts.py`.
2. **Canonical Models:** Implement `CanonicalDatabase`, `CanonicalNamespace`, `CanonicalTable`, `CanonicalColumn`, `CanonicalConstraint`, `CanonicalForeignKey`, `CanonicalIndex`, `CanonicalView`, `CanonicalTrigger`, `CanonicalRelationship`.
3. **Engine-Specific Adapters:** Implement adapters for PostgreSQL, SQLite, MySQL, and MariaDB.
4. **Normalization Pipeline & Ordering:** Implement `MetadataNormalizer`, collision detector, reference integrity validator, and deterministic multi-key sort.
5. **Deterministic Serialization:** Implement canonical UTF-8 JSON encoder and golden file generator.
6. **Cross-Engine Fixtures & Test Suite:** Implement unit, contract, identity, security, golden file, and live integration tests across all 5 supported engines.
7. **Documentation & Acceptance Audit:** Create 14 documentation files under `docs/metadata/` and the final acceptance audit.
