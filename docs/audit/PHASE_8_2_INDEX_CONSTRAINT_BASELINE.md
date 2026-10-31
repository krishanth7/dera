# DERA — Phase 8.2 Baseline Audit
## Index & Constraint Diagnostics Foundation

**Timestamp**: 2026-10-31  
**Base Commit SHA**: `53fdb9d46dea5d5ed3b4ab4fa80b9c3c49b6e442`  
**Milestone**: 8.2 — Index & Constraint Diagnostics  
**Status**: VERIFIED & QUALIFIED  

---

## 1. Verified Prerequisites

The repository audit verifies that the foundational architecture is operational, tested, and passing all quality gates:

| Component | Target Phase | Status | Evidence / Verification Path |
|---|---|---|---|
| **Base Connectors** | Phase 5.1 | PASS | `packages/connectors/src/dera_connectors/base/connector.py` |
| **PostgreSQL & Supabase** | Phase 5.2 | PASS | `packages/connectors/src/dera_connectors/postgres/` |
| **SQLite Connector** | Phase 5.3 | PASS | `packages/connectors/src/dera_connectors/sqlite/` |
| **MySQL & MariaDB Connectors** | Phase 5.4 | PASS | `packages/connectors/src/dera_connectors/mysql/`, `mariadb/` |
| **Metadata Normalization & Identity** | Phase 5.5 | PASS | `packages/core/src/dera/metadata/models/` |
| **Connector Safety & Read-Only Invariant** | Phase 5.6 | PASS | Interceptor enforcing `PRAGMA query_only = ON;`, `BEGIN READ ONLY` |
| **Canonical Schema Models** | Phase 6.1 | PASS | `dera.metadata.models.table`, `index`, `constraint`, `relationship` |
| **Structural Reconstruction** | Phase 6.2 | PASS | `dera.reverse_engineering.reconstruction` |
| **Foreign Key Graph** | Phase 6.3 | PASS | `dera.reverse_engineering.graph` |
| **Dependency Analysis & DAG** | Phase 6.4 | PASS | `dera.reverse_engineering.dependencies` (Tarjan SCC, Kahn topological sort) |
| **Immutable Schema Snapshots** | Phase 6.5 | PASS | `dera.reverse_engineering.snapshots` (SHA-256 canonical hashing) |
| **Reverse Engineering APIs** | Phase 6.6 | PASS | `apps/api/src/dera_api/api/v1/endpoints/reverse_engineering/` |
| **Diagnostic Rules Engine** | Phase 8.1 | PASS | `packages/core/src/dera/diagnostics/` (protocols, registry, context, evaluator, foundational rules) |

---

## 2. Supported Index Metadata

From `CanonicalIndex` and `CanonicalIndexTerm` ([`packages/core/src/dera/metadata/models/index.py`](../../packages/core/src/dera/metadata/models/index.py)):

| Field | Type | Description | Diagnostic Use |
|---|---|---|---|
| `id` | `str` | Deterministic ObjectId | Unique identity and finding fingerprinting |
| `parent_table_id` | `str` | Owning table ObjectId | Scoping index comparisons to parent table |
| `name` | `str` | Native index name | Reporting and evidence references |
| `is_unique` | `bool` | Uniqueness enforcement flag | Uniqueness preservation in equivalence/redundancy |
| `is_primary` | `bool` | Backs Primary Key | Constraint ownership detection |
| `index_type` | `IndexType` | Physical access method (`BTREE`, `HASH`, `GIN`, `GIST`, etc.) | Prefix analysis applicability (B-tree only) |
| `terms` | `tuple[CanonicalIndexTerm]` | Ordered terms (column or expression) | Key order, column comparison, sort direction, expressions |
| `predicate` | `str \| None` | Partial index `WHERE` filter | Partial index equivalence comparison |
| `provenance` | `MetadataProvenance` | Extraction metadata | Source engine, completeness, and collection timestamp |

From `CanonicalIndexTerm`:
- `column_name`: native column identifier (if standard column)
- `expression`: SQL expression string (if expression index)
- `ordinal_position`: 1-based order within index key definition
- `is_descending`: `True` for `DESC`, `False` for `ASC`
- `nulls_first`: `True` for `NULLS FIRST`
- `is_expression`: `True` if functional/expression term

---

## 3. Supported Constraint Metadata

From `CanonicalConstraint` ([`packages/core/src/dera/metadata/models/constraint.py`](../../packages/core/src/dera/metadata/models/constraint.py)) and `CanonicalForeignKey` ([`packages/core/src/dera/metadata/models/relationship.py`](../../packages/core/src/dera/metadata/models/relationship.py)):

| Model | Classification | Supported Attributes | Diagnostic Use |
|---|---|---|---|
| `CanonicalConstraint` | `PRIMARY_KEY` | `id`, `parent_table_id`, `name`, `columns`, `is_enforced` | Primary key column validation, nullability, uniqueness |
| `CanonicalConstraint` | `UNIQUE` | `id`, `parent_table_id`, `name`, `columns`, `is_enforced` | Unique constraint integrity, redundancy against PK |
| `CanonicalConstraint` | `CHECK` | `id`, `parent_table_id`, `name`, `check_clause`, `is_enforced` | Check expression safety, metadata integrity |
| `CanonicalForeignKey` | `FOREIGN_KEY` | `id`, `source_table_id`, `referenced_table_id`, `column_mappings`, `on_update`, `on_delete`, `is_deferrable` | Composite referential mapping integrity, index coverage |

---

## 4. Engine-Specific Index & Constraint Capability Matrix

| Engine | B-Tree Prefix Traversal | Expression Indexes | Partial Indexes | Descending Sort (`DESC`) | Included Columns (`INCLUDE`) | Engine-Managed FK Index |
|---|---|---|---|---|---|---|
| **PostgreSQL** | Yes | Yes | Yes | Yes | Yes (v11+) | No (manual indexing recommended) |
| **Supabase PostgreSQL** | Yes | Yes | Yes | Yes | Yes | No |
| **SQLite** | Yes | Yes (v3.9+) | Yes (v3.8+) | Yes | No | No |
| **MySQL (InnoDB)** | Yes | Yes (v8.0.13+) | No | Yes (v8.0+) | No | Yes (automatic FK supporting index) |
| **MariaDB (InnoDB)** | Yes | No (virtual cols) | No | No (ignored syntax) | No | Yes (automatic FK supporting index) |

---

## 5. Phase 8.2 Scope & Rule Catalog

| Rule ID | Rule Version | Category | Title | Default Severity |
|---|---|---|---|---|
| `DERA-IDX-001` | `1.0.0` | `INDEXES` | Exact Duplicate Index Definition | `MEDIUM` |
| `DERA-IDX-002` | `1.0.0` | `INDEXES` | Potentially Redundant B-Tree Index | `LOW` |
| `DERA-IDX-003` | `1.0.0` | `INDEXES` | Foreign Key Supporting Index Coverage | `MEDIUM` |
| `DERA-IDX-004` | `1.0.0` | `INDEXES` | Index Column Integrity | `HIGH` |
| `DERA-CON-001` | `1.0.0` | `CONSTRAINTS` | Primary Key Structural Integrity | `HIGH` |
| `DERA-CON-002` | `1.0.0` | `CONSTRAINTS` | Foreign Key Referential Mapping Integrity | `HIGH` |
| `DERA-CON-003` | `1.0.0` | `CONSTRAINTS` | Unique Constraint Structural Integrity | `MEDIUM` |
| `DERA-CON-004` | `1.0.0` | `CONSTRAINTS` | Check Constraint Metadata Integrity | `LOW` |
| `DERA-CON-005` | `1.0.0` | `CONSTRAINTS` | Constraint Column Integrity | `HIGH` |

---

## 6. Implementation Risks & Mitigations

1. **False Redundancy Claims:**
   - *Risk:* Labeling a prefix index as redundant when it is required for index-only scans, distinct uniqueness, or distinct sort orders.
   - *Mitigation:* Classify prefix overlap as conservative `LOW` severity review candidate (`DERA-IDX-002`). Require identical method (B-Tree), identical sort direction per term, and compatible predicates/uniqueness before flagging.
2. **Dropping Constraint-Owned Indexes:**
   - *Risk:* Recommending deletion of an index backing a primary key or unique constraint.
   - *Mitigation:* Explicit index ownership checks identify indexes backing PKs or unique constraints, warning that the index is constraint-owned.
3. **Engine FK Asymmetry:**
   - *Risk:* Falsely flagging missing FK indexes on MySQL/MariaDB which automatically enforces/generates supporting indexes.
   - *Mitigation:* Check engine capability profile: MySQL/MariaDB engines are skipped or marked `NOT_APPLICABLE` for `DERA-IDX-003` if an engine-generated index is detected.
4. **Untrusted Check Expressions:**
   - *Risk:* Executing customer SQL expressions from check constraints.
   - *Mitigation:* Strict Zero-Execution rule: check clauses are treated strictly as unparsed, sanitized string metadata.

---

## 7. Baseline Qualification Verdict

**Prerequisites Status**: **PASS**  
All architectural dependencies from Phases 5.1–5.6, 6.1–6.6, and 8.1 are in place. The Phase 8.2 implementation may proceed immediately.
