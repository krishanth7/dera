# Foreign Key Graph Architecture

## 1. System Position & Data Flow

The Phase 6.3 Foreign Key Relationship Graph sits within the DERA Reverse Engineering Core Engine pipeline:

```text
┌────────────────────────────────────────────────────────┐
│ Phase 5 Multi-Engine Connectors                       │
│ (PostgreSQL, Supabase, SQLite, MySQL, MariaDB)        │
└───────────────────────────┬────────────────────────────┘
                            │ DatabaseMetadataReport
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 5.5 Canonical Metadata Normalization            │
│ (Stable SHA-256 ObjectIds, CanonicalDatabase)          │
└───────────────────────────┬────────────────────────────┘
                            │ CanonicalDatabase
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 6.1 Canonical Schema Representation              │
│ (SchemaRepresentation, ObjectRegistry, SchemaHierarchy)│
└───────────────────────────┬────────────────────────────┘
                            │ SchemaRepresentation
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 6.2 Structural Reconstruction                   │
│ (ReconstructedSchema, ReconstructedForeignKey)         │
└───────────────────────────┬────────────────────────────┘
                            │ ReconstructedSchema / CanonicalDatabase
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 6.3 Foreign Key Relationship Graph Engine        │
│                                                        │
│  ForeignKeyGraphBuilder                                │
│   ├── Resource Limits Check                            │
│   ├── Table Node Extraction & Normalization            │
│   ├── Edge Construction & Column Pair Mapping          │
│   ├── Unresolved Target Reference Resolution           │
│   ├── Deterministic Sorting & Normalization            │
│   ├── Adjacency Index Construction                     │
│   ├── Graph Validation (STRICT / PERMISSIVE)           │
│   └── Frozen ForeignKeyGraph Materialization           │
└───────────────────────────┬────────────────────────────┘
                            │ Frozen ForeignKeyGraph
                            ▼
┌────────────────────────────────────────────────────────┐
│ Downstream: Phase 6.4 Dependency Engine                │
│ (SCCs, Topological Sorters, Circular Dependency Eval) │
└────────────────────────────────────────────────────────┘
```

---

## 2. Ingestion Interfaces

[`ForeignKeyGraphBuilder`](file:///packages/core/src/dera/reverse_engineering/graph/builder.py) provides three standard ingestion paths:

1. **`from_reconstruction(reconstructed_schema)`**: Direct consumption of Phase 6.2 `ReconstructedSchema` models.
2. **`from_schema(schema_representation)`**: Ingestion from Phase 6.1 `SchemaRepresentation` by automatically executing Phase 6.2 structural reconstruction.
3. **`from_canonical(canonical_database)`**: Direct ingestion from Phase 5.5 `CanonicalDatabase` domain models.

All ingestion pipelines yield an identical, immutable [`ForeignKeyGraph`](file:///packages/core/src/dera/reverse_engineering/graph/models.py).

---

## 3. Immutability Architecture

All domain models are implemented as frozen Pydantic v2 classes:

- Every field is read-only after instantiation (`frozen=True`).
- Collections are stored as immutable Python `tuple`s rather than mutable `list`s.
- Dictionaries inside [`AdjacencyIndex`](file:///packages/core/src/dera/reverse_engineering/graph/adjacency.py) are constructed during initialization and encapsulated behind read-only accessors returning immutable tuples.
- The root `ForeignKeyGraph` caches its `AdjacencyIndex` via a cached property to avoid redundant construction while preserving immutability.

---

## 4. Algorithmic Complexity

| Operation | Time Complexity | Space Complexity | Description |
| :--- | :--- | :--- | :--- |
| Graph Construction | $O(V + E + P)$ | $O(V + E + P)$ | Linear scan where $V = \text{tables}$, $E = \text{constraints}$, $P = \text{column pairs}$. |
| Direct Adjacency Query | $O(1)$ lookup + $O(\text{deg}(v))$ | $O(\text{deg}(v))$ | Hash-map lookup yielding pre-computed tuple of edges. |
| Neighbor Discovery | $O(1)$ lookup + $O(\text{deg}(v))$ | $O(\text{deg}(v))$ | Hash-map lookup yielding unique table `ObjectId`s. |
| Edge Existence (`between`) | $O(1)$ lookup + $O(k)$ | $O(k)$ | Lookup yielding parallel edges between source and target. |
| Bounded Traversal (BFS/DFS) | $O(\min(V_{\text{visited}} + E_{\text{visited}}, \text{limits}))$ | $O(V_{\text{visited}})$ | Traversal with strict depth, node, and edge caps. |
| Weakly Connected Components | $O(V + E)$ | $O(V)$ | Undirected BFS partitioning. |
| Deterministic Hashing | $O(V + E)$ | $O(\text{bytes})$ | SHA-256 digest over canonical JSON. |
