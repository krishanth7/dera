# DERA Phase 6.1 — Canonical Schema Representation: Baseline Audit

**Audit Type:** Pre-Implementation Baseline
**Phase:** 6.1 — Canonical Schema Representation
**Auditor:** DERA Engineering Team
**Date:** 2026-10-27

---

## 1. Repository State

| Item | Value |
|------|-------|
| **Base Commit SHA** | `3730ed7` |
| **Branch** | `main` |
| **Commit Message** | `fix(ci): add dera_connectors to PYTHONPATH in schema regression workflow` |
| **Repository** | `https://github.com/krishanth7/dera` |

---

## 2. Verified Prerequisites

### Phase 5.1 — Connector Interface & Capability Model
- **Status:** VERIFIED ✅
- `packages/connectors/src/dera_connectors/protocol.py` — `DatabaseConnector` protocol
- `packages/connectors/src/dera_connectors/capabilities.py` — capability registry
- `packages/connectors/src/dera_connectors/engine.py` — engine enumeration
- `packages/connectors/src/dera_connectors/registry.py` — connector registry

### Phase 5.2 — PostgreSQL & Supabase Connector
- **Status:** VERIFIED ✅
- `packages/connectors/src/dera_connectors/postgresql/` — complete adapter, config, connection

### Phase 5.3 — SQLite Connector
- **Status:** VERIFIED ✅
- `packages/connectors/src/dera_connectors/sqlite/` — adapter, catalog queries, type affinity

### Phase 5.4 — MySQL & MariaDB Connectors
- **Status:** VERIFIED ✅
- `packages/connectors/src/dera_connectors/mysql/` — MySQL adapter
- `packages/connectors/src/dera_connectors/mariadb/` — MariaDB adapter
- `packages/connectors/src/dera_connectors/mysql_family/` — shared catalog, security, errors

### Phase 5.5 — Metadata Normalization & Identity
- **Status:** VERIFIED ✅
- `packages/core/src/dera/metadata/__init__.py` — full public API
- `packages/core/src/dera/metadata/identity.py` — `compute_stable_object_id`, length-prefixed SHA-256
- `packages/core/src/dera/metadata/models/` — all canonical models present
- `packages/core/src/dera/metadata/enums.py` — `ObjectKind`, `CanonicalTypeCategory`, etc.
- `packages/core/src/dera/metadata/contracts.py` — `CANONICAL_METADATA_CONTRACT_VERSION = "1.0.0"`
- `packages/core/src/dera/metadata/provenance.py` — `MetadataProvenance`
- `packages/core/src/dera/metadata/serialization.py` — deterministic JSON + SHA-256
- `packages/core/src/dera/metadata/ordering.py` — all sort functions
- `packages/core/src/dera/metadata/validation.py` — `validate_canonical_database`
- `packages/core/src/dera/metadata/capabilities.py` — `assess_engine_metadata_completeness`
- `packages/core/src/dera/metadata/errors.py` — full error taxonomy
- `packages/core/src/dera/metadata/normalization.py` — `MetadataNormalizer`

### Phase 5.6 — Read-Only Enforcement, Timeouts & Safety
- **Status:** VERIFIED ✅ (code present on main, PR #48 code was fast-forward merged)
- `packages/connectors/src/dera_connectors/security/` — full security module package
- `docs/security/` — 12 security architecture documents
- `docs/audit/PHASE_5_6_SECURITY_ACCEPTANCE.md` — acceptance evidence present

### Phase 5 Completion
- **Status:** VERIFIED ✅
- `docs/audit/PHASE_5_COMPLETION.md` — present

---

## 3. Existing Canonical Models (Phase 5.5)

| Model | ObjectId Field | Key Fields |
|-------|---------------|------------|
| `CanonicalDatabase` | `id: str` | name, engine, contract_version, namespaces, provenance |
| `CanonicalNamespace` | `id: str` | name, database_id, tables, views, provenance |
| `CanonicalTable` | `id: str` | namespace_id, name, table_type, columns, primary_key, foreign_keys, indexes, triggers |
| `CanonicalColumn` | `id: str` | parent_table_id, name, ordinal_position, native_data_type, canonical_type |
| `CanonicalConstraint` | `id: str` | parent_table_id, name, constraint_type, columns, check_clause |
| `CanonicalForeignKey` | `id: str` | source_table_id, referenced_table_id, column_mappings, on_update, on_delete |
| `CanonicalIndex` | `id: str` | parent_table_id, name, is_unique, is_primary, index_type, terms |
| `CanonicalIndexTerm` | (embedded) | column_name, expression, ordinal_position, is_descending |
| `CanonicalView` | `id: str` | namespace_id, name, definition |
| `CanonicalTrigger` | `id: str` | parent_table_id, name, timing, events |
| `MetadataProvenance` | (embedded) | source_engine, collection_timestamp, completeness, engine_specific |

---

## 4. Existing Object Identity Design

- **Algorithm:** length-prefixed SHA-256 (`compute_stable_object_id`)
- **Format:** `dera:<object_kind>:<24_hex_chars>`
- **Inputs:** engine, object_kind, native_name, namespace, parent_id, workspace_id, connection_id, terms
- **Properties:** deterministic, workspace-isolated, collision-resistant
- **Version:** `v1` prefix in hash frame

---

## 5. Existing Serialization Conventions

- `serialize_canonical_database`: `json.dumps` with `sort_keys=True`, `ensure_ascii=False`
- `compute_canonical_database_hash`: compact JSON → SHA-256 hexdigest
- Custom serializer handles `datetime` (RFC 3339) and StrEnum values
- Contract version: `CANONICAL_METADATA_CONTRACT_VERSION = "1.0.0"`

---

## 6. Existing Security Controls

- Read-only enforcement via lexical SQL validation
- SSRF/DNS rebinding protection on all network connectors
- SQLite filesystem containment (allowlist paths)
- Multi-tenant workspace authorization
- Centralized timeouts and resource limits
- Structured audit logging without credential exposure

---

## 7. Missing Functionality (Phase 6.1 Target)

| Missing Component | Description |
|-------------------|-------------|
| `dera.reverse_engineering` package | Phase 6.1 top-level package |
| `SchemaRepresentation` root model | Typed wrapper around canonical database with registry |
| `ObjectRegistry` | O(1) lookup by ObjectId, type-safe, duplicate detection |
| Typed object references | `TypedRef[T]` with resolution status |
| Reference resolution engine | Resolve/Missing/Restricted/Unsupported/Ambiguous/Invalid |
| `SchemaBuilder` | Deterministic construction from `CanonicalDatabase` |
| Hierarchical navigation | `schema.tables`, `schema.columns_of(table_id)`, etc. |
| Referential integrity validation | Cross-object parent/child consistency checks |
| Duplicate detection | Detect duplicate ObjectIds in registry |
| Partial metadata handling | Support PARTIAL/RESTRICTED completeness without fabrication |
| Schema-level deterministic serialization | Extend Phase 5.5 conventions to schema representation |
| Schema resource limits | Max objects, max nesting, max identifier size |
| Phase 6.1 test suite | Unit, contract, determinism, security, integration, golden |
| `docs/reverse-engineering/` | Full documentation suite |
| `docs/audit/PHASE_6_1_SCHEMA_ACCEPTANCE.md` | Acceptance audit |

---

## 8. Architectural Risks

| Risk | Mitigation |
|------|------------|
| Duplicating Phase 5.5 models | Reuse `CanonicalDatabase` and all child models directly; add thin registry/navigation layer only |
| ObjectId format drift | Import and use `compute_stable_object_id` exclusively; no new ID algorithm |
| Quadratic registry lookups | Use `dict[str, ...]` keyed by ObjectId for O(1) access |
| Silent partial-metadata fabrication | Preserve `MetadataCompleteness` from provenance; never invent absent objects |
| Circular references in navigation | Validate parent-child links; no cyclic ownership allowed |

---

## 9. Implementation Plan

1. Create `packages/core/src/dera/reverse_engineering/` package
2. Implement `errors.py` — SchemaRepresentation error taxonomy
3. Implement `references.py` — `TypedRef`, `ResolutionStatus`
4. Implement `registry.py` — `ObjectRegistry` with O(1) typed lookup
5. Implement `hierarchy.py` — hierarchical navigation helpers
6. Implement `ordering.py` — Phase 6.1 deterministic ordering (reusing Phase 5.5 sort functions)
7. Implement `validation.py` — referential integrity, duplicate detection
8. Implement `capabilities.py` — capability-aware completeness for schema representation
9. Implement `serialization.py` — deterministic schema representation serialization
10. Implement `schema.py` — `SchemaRepresentation` root model
11. Implement `builder.py` — `SchemaBuilder.from_canonical_database()`
12. Create test fixtures
13. Write all test suites
14. Write all documentation
15. Run CI-equivalent checks
16. Create acceptance audit
17. Open pull request
