# Phase 6.3 Foreign Key Relationship Graph Overview

## 1. Executive Summary

Milestone 6.3 of the DERA Reverse Engineering Core Engine introduces the **Foreign Key Relationship Graph** (`ForeignKeyGraph`), a strongly typed, deterministic, immutable directed multigraph representing verified foreign key relationships across database schemas.

Built on top of Phase 6.1 Canonical Schema Representation (`SchemaRepresentation`) and Phase 6.2 Structural Constraint Reconstruction (`ReconstructedSchema`), the graph model maps tables to typed nodes (`TableNode`) and foreign key constraints to directed relationship edges (`ForeignKeyEdge`).

```text
┌────────────────────────────────────────────────────────┐
│ Phase 5 Canonical Metadata Normalized Objects          │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 6.1 Canonical Schema Representation              │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 6.2 Structural Constraint Reconstruction         │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 6.3 Foreign Key Graph Engine                     │
│  - TableNode (frozen, stable ObjectId identity)        │
│  - ForeignKeyEdge (directed, parallel, self-loop)      │
│  - ColumnPairMapping (ordered source -> target)        │
│  - AdjacencyIndex (O(1) bidirectional lookup)          │
│  - Bounded Traversal (BFS / DFS with depth & limits)   │
│  - Weakly Connected Components (WCC)                   │
│  - Multi-severity Integrity Validation                 │
│  - Deterministic Serialization & SHA-256 Fingerprint   │
└────────────────────────────────────────────────────────┘
```

---

## 2. Core Tenets

1. **Deterministic Construction**: Identical input schemas always yield identical node ordering, edge ordering, adjacency indexes, and serialized JSON representation.
2. **Strict Provenance**: Every edge originates from a verified database constraint. Synthetic, heuristic, or AI/LLM-inferred edges are strictly prohibited.
3. **Canonical Directionality**: Edges are consistently directed from the child table declaring the foreign key to the parent referenced table (`Source FK Table -> Referenced PK/UQ Table`).
4. **Immutability**: All nodes, edges, mappings, indexes, and graphs are immutable (`frozen=True` Pydantic models).
5. **Directed Multigraph**: Multiple distinct foreign key constraints between the same table pair are preserved as distinct edges with unique constraint identities.
6. **Bounded Execution**: Graph traversal, node counts, edge counts, and serialization payloads are subject to strict configurable resource limits (`GraphResourceLimits`).

---

## 3. Package Structure

The Phase 6.3 implementation is housed under `packages/core/src/dera/reverse_engineering/graph/`:

| Module | Description |
| :--- | :--- |
| [`models.py`](file:///packages/core/src/dera/reverse_engineering/graph/models.py) | Root `ForeignKeyGraph` container and `UnresolvedReference` tracking model. |
| [`nodes.py`](file:///packages/core/src/dera/reverse_engineering/graph/nodes.py) | `TableNode` definition and node metadata. |
| [`edges.py`](file:///packages/core/src/dera/reverse_engineering/graph/edges.py) | `ForeignKeyEdge` and `ColumnPairMapping` definitions. |
| [`builder.py`](file:///packages/core/src/dera/reverse_engineering/graph/builder.py) | `ForeignKeyGraphBuilder` constructing graphs from canonical schemas and reconstructed structures. |
| [`adjacency.py`](file:///packages/core/src/dera/reverse_engineering/graph/adjacency.py) | `AdjacencyIndex` providing $O(1)$ bidirectional edge and neighbor queries. |
| [`traversal.py`](file:///packages/core/src/dera/reverse_engineering/graph/traversal.py) | Bounded BFS/DFS traversals and weakly connected component analysis. |
| [`validation.py`](file:///packages/core/src/dera/reverse_engineering/graph/validation.py) | Graph integrity validation rules and `GraphValidationFinding` reporting. |
| [`ordering.py`](file:///packages/core/src/dera/reverse_engineering/graph/ordering.py) | Deterministic sorting keys and ordering routines for all graph primitives. |
| [`serialization.py`](file:///packages/core/src/dera/reverse_engineering/graph/serialization.py) | Canonical JSON serialization, deserialization, and SHA-256 hashing. |
| [`capabilities.py`](file:///packages/core/src/dera/reverse_engineering/graph/capabilities.py) | Engine-specific capability assessment (PostgreSQL, SQLite, MySQL, MariaDB). |
| [`limits.py`](file:///packages/core/src/dera/reverse_engineering/graph/limits.py) | Resource bounds enforcement (`GraphResourceLimits`). |
| [`errors.py`](file:///packages/core/src/dera/reverse_engineering/graph/errors.py) | Strongly typed graph exception taxonomy. |

---

## 4. Key Capabilities

- **Single & Composite Foreign Keys**: Full support for single-column and multi-column composite keys with sequence order preservation.
- **Self-Referencing Keys**: Handles hierarchical tables (e.g., employee managers, category trees) via self-loops.
- **Parallel Relationships**: Distinguishes multiple foreign keys linking the same source and target tables (e.g., `orders.created_by` and `orders.approved_by` to `users.id`).
- **Cross-Namespace References**: Preserves relationships across schemas (e.g., `analytics.fact_sales -> core.dim_customer`).
- **Unresolved Reference Tracking**: Flags external or omitted tables without silently dropping constraints or inventing fictional nodes.
- **Bi-directional Querying**: Direct $O(1)$ retrieval of outgoing edges (`outgoing(table_id)`), incoming edges (`incoming(table_id)`), and relationships between tables (`relationships_between(src, tgt)`).
