# DERA — Phase 8.3 Baseline Audit
## Relationship & Dependency Diagnostics Foundation

**Timestamp**: 2026-10-31  
**Base Commit SHA**: `2878e912d602db9026996c20c6b75b2e76e2bcc8`  
**Milestone**: 8.3 — Relationship & Dependency Diagnostics  
**Status**: VERIFIED & QUALIFIED  

---

## 1. Verified Prerequisites

The repository audit verifies that the entire foundational architecture from Phase 5 through Phase 8.2 is operational, tested, and passing all quality gates:

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
| **Foreign Key Graph** | Phase 6.3 | PASS | `dera.reverse_engineering.graph` (`ForeignKeyGraph`, `ForeignKeyEdge`, `TableNode`) |
| **Dependency Analysis & DAG** | Phase 6.4 | PASS | `dera.reverse_engineering.dependencies` (Tarjan SCC, Johnson cycles, topological sort) |
| **Immutable Schema Snapshots** | Phase 6.5 | PASS | `dera.reverse_engineering.snapshots` (SHA-256 canonical hashing) |
| **Reverse Engineering APIs** | Phase 6.6 | PASS | `apps/api/src/dera_api/api/v1/endpoints/reverse_engineering/` |
| **ER Canvas & Dependency Explorer** | Phase 7.4–7.5 | PASS | `apps/web/src/components/canvas/`, `components/inspector/` |
| **Diagnostic Rules Engine** | Phase 8.1 | PASS | `packages/core/src/dera/diagnostics/` (protocols, registry, context, evaluator, foundational rules) |
| **Index & Constraint Diagnostics** | Phase 8.2 | PASS | `dera.diagnostics.rules.indexes`, `dera.diagnostics.rules.constraints` (9 production rules) |

---

## 2. Graph Contracts & Data Model

From `ForeignKeyGraph` ([`packages/core/src/dera/reverse_engineering/graph/models.py`](../../packages/core/src/dera/reverse_engineering/graph/models.py)):

| Contract Entity | Type | Description | Diagnostic Significance |
|---|---|---|---|
| `ForeignKeyGraph` | `BaseModel` (frozen) | Immutable directed multigraph of relational constraints | Root container for nodes, edges, unresolved references, and capability profile |
| `TableNode` | `BaseModel` (frozen) | Verified table node | Source/target node endpoint validation, namespace scoping, primary key metadata |
| `ForeignKeyEdge` | `BaseModel` (frozen) | Verified foreign key constraint edge | Relationship edge identity, actions (`on_delete`, `on_update`), column mappings |
| `ColumnPairMapping` | `BaseModel` (frozen) | Ordered source child and target parent column pair | Composite key ordering and ordinal alignment verification |
| `UnresolvedReference` | `BaseModel` (frozen) | Record of unresolvable foreign key constraint | Catalog transparency, missing target discovery without phantom node creation |
| `AdjacencyIndex` | Helper class | O(1) indexed lookup for outgoing, incoming, and pairwise edges | Rapid graph traversal and neighborhood inspection |

---

## 3. Edge Direction Convention

Phase 6.3 and Phase 6.4 strictly establish the canonical foreign key edge convention:

```text
Referencing Child Table (source) ---> Referenced Parent Table (target)
```

**Example**:
```text
order_items (order_id) ---> orders (id) ---> customers (id)
```

### Definitions
- **Direct Outgoing Dependencies (`dependency_adj`)**: Tables directly referenced by the selected table (upstream prerequisite parents that must exist before the child).
- **Direct Incoming Dependents (`prerequisite_adj` / `dependent_adj`)**: Tables that directly reference the selected table (downstream children depending on the parent).
- **Transitive Dependencies (Ancestors)**: All upstream tables reachable by following outgoing edges.
- **Transitive Dependents (Descendants / Blast Radius)**: All downstream tables reachable by following incoming edges in reverse.

---

## 4. Verified Dependency Algorithms

From [`packages/core/src/dera/reverse_engineering/dependencies/algorithms/`](../../packages/core/src/dera/reverse_engineering/dependencies/algorithms/):

1. **Tarjan's Strongly Connected Components (`tarjan.py`)**:
   - Computes all maximal strongly connected components in $O(V + E)$ time.
   - Accurately classifies trivial components (single node without self-loop) vs cyclic components (nodes in circular reference or self-loop).
2. **Johnson's Elementary Cycle Enumeration (`johnson.py`)**:
   - Finds all simple circuits within cyclic SCCs up to configured resource limits (`max_cycles`).
3. **Topological Sort & Condensation DAG (`topological_sort.py`)**:
   - Computes deterministic creation order for acyclic subgraphs using Kahn's algorithm.
   - Condenses cyclic SCCs into supernodes to construct an acyclic condensation DAG.
4. **Graph Metrics & Centrality (`metrics.py`)**:
   - Calculates in-degree (fan-in / referenced count), out-degree (fan-out / dependency count).
   - Computes transitive dependency and dependent counts via bounded BFS.
   - Evaluates dependency depth (longest simple path from root nodes).

---

## 5. Existing Diagnostic Rules Catalog

The repository currently registers 14 production diagnostic rules across Phase 8.1 and Phase 8.2:

### Phase 8.1 Foundational Rules (`DERA-FND-*`)
- `DERA-FND-001`: Missing Structural Metadata
- `DERA-FND-002`: Unsupported Engine Capability
- `DERA-FND-003`: Identity Collision
- `DERA-FND-004`: Invalid Relationship Mapping
- `DERA-FND-005`: Unresolved Target Reference

### Phase 8.2 Index Rules (`DERA-IDX-*`)
- `DERA-IDX-001`: Exact Duplicate Index Definition
- `DERA-IDX-002`: Potentially Redundant B-Tree Index (Leftmost Prefix Analysis)
- `DERA-IDX-003`: Foreign Key Supporting Index Coverage
- `DERA-IDX-004`: Index Column Reference Integrity

### Phase 8.2 Constraint Rules (`DERA-CON-*`)
- `DERA-CON-001`: Primary Key Structural Integrity
- `DERA-CON-002`: Foreign Key Referential Mapping Integrity
- `DERA-CON-003`: Unique Constraint Structural Integrity
- `DERA-CON-004`: Check Constraint Metadata Integrity
- `DERA-CON-005`: Constraint Column Integrity

---

## 6. Phase 8.3 Target Rules Catalog

Phase 8.3 introduces 8 specialized static analysis rules targeting relationship integrity and graph dependency topology:

| Rule ID | Version | Category | Target Problem | Default Severity |
|---|---|---|---|---|
| `DERA-REL-001` | `1.0.0` | `RELATIONSHIPS` | Relationship Graph Integrity (Dangling endpoints, invalid edge identities) | `HIGH` |
| `DERA-REL-002` | `1.0.0` | `RELATIONSHIPS` | Unresolved Relationship Targets (Target table not in scope / catalog) | `MEDIUM` |
| `DERA-REL-003` | `1.0.0` | `RELATIONSHIPS` | Composite Foreign Key Mapping Integrity (Mismatched counts, non-existent columns) | `HIGH` |
| `DERA-REL-004` | `1.0.0` | `RELATIONSHIPS` | Cross-Namespace Dependencies (Coupling across schemas) | `INFORMATIONAL` |
| `DERA-DEP-001` | `1.0.0` | `DEPENDENCIES` | Circular Dependencies & Strongly Connected Components (Cyclic groups) | `MEDIUM` |
| `DERA-DEP-002` | `1.0.0` | `DEPENDENCIES` | Deep Dependency Chains (Excessive hierarchy depth) | `INFORMATIONAL` |
| `DERA-DEP-003` | `1.0.0` | `DEPENDENCIES` | High Dependency Concentration (High fan-in / fan-out bottlenecks) | `INFORMATIONAL` |
| `DERA-DEP-004` | `1.0.0` | `DEPENDENCIES` | Structural Impact Radius (Downstream blast radius on parent change) | `INFORMATIONAL` |

---

## 7. Security & Operational Boundaries

1. **Zero AI/LLM/ML Dependencies**: All algorithms are deterministic, mathematical graph operations (Tarjan SCC, Kahn DAG, BFS reachability, hash signatures).
2. **Strictly Read-Only Guarantee**: Diagnostics inspect memory structures or cached snapshots; zero SQL queries or DDL mutations are dispatched to source databases.
3. **Workspace Isolation**: Multitenant boundaries are strictly enforced. Graph nodes and edges cannot reference entities across differing `workspace_id` contexts.
4. **Computational Bounds**: Traversal depth, cycle count, node count, and edge count are strictly bounded by `DiagnosticResourceLimits` to prevent CPU exhaustion or exponential path explosions.

---

## 8. Implementation Plan

1. **Shared Graph Helpers** (`packages/core/src/dera/diagnostics/rules/shared/graph_helpers.py`):
   - Provide `resolve_graph_and_dependencies()` to obtain or construct `ForeignKeyGraph` and `DependencyAnalysisResult` from `DiagnosticContext`.
2. **Relationship Rules Implementation** (`packages/core/src/dera/diagnostics/rules/relationships/`):
   - `graph_integrity.py`: `DERA-REL-001`
   - `unresolved_targets.py`: `DERA-REL-002`
   - `composite_mappings.py`: `DERA-REL-003`
   - `cross_namespace.py`: `DERA-REL-004`
3. **Dependency Rules Implementation** (`packages/core/src/dera/diagnostics/rules/relationships/`):
   - `cyclic_dependencies.py`: `DERA-DEP-001`
   - `dependency_depth.py`: `DERA-DEP-002`
   - `dependency_concentration.py`: `DERA-DEP-003`
   - `structural_impact.py`: `DERA-DEP-004`
4. **Rule Registration**:
   - Register Phase 8.3 rules in `packages/core/src/dera/diagnostics/__init__.py` and the FastAPI service registry.
5. **Comprehensive Testing**:
   - Unit tests, cycle tests, direction tests, cross-engine tests, determinism tests, security bounds.
6. **Documentation & Acceptance Audit**:
   - 15 specialized technical guides under `docs/diagnostics/` and `docs/audit/PHASE_8_3_RELATIONSHIP_ACCEPTANCE.md`.
7. **CI Qualification & Pull Request**:
   - Run complete test suite and linters; open PR #63.
