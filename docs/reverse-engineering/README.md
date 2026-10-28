# DERA Reverse Engineering Core Engine — Canonical Schema Representation (Phase 6.1)

Welcome to the **DERA Reverse Engineering Core Engine** documentation.

Phase 6.1 delivers the foundational **Canonical Schema Representation Layer** that transforms validated Phase 5.5 canonical database metadata into a coherent, strongly-typed, navigable, registry-backed representation of database architecture.

---

## 1. Mission & Architectural Role

DERA (Database Engineering & Reverse Analysis) is a deterministic database engineering platform. Its tagline is:
> *Understand Every Schema. Engineer Every Change.*

In Phase 6.1, the schema representation layer bridges the gap between raw catalog metadata and advanced reverse-engineering operations:

```text
Source Database
     │
     ▼ (Phase 5 Connectors: PostgreSQL, SQLite, MySQL, MariaDB)
Phase 5 Canonical Metadata Report
     │
     ▼ (Phase 5.5 Normalizer & Identity)
CanonicalDatabase (Immutable Domain Model)
     │
     ▼ (Phase 6.1 SchemaBuilder)
┌────────────────────────────────────────────────────────┐
│               SchemaRepresentation                     │
│  ├─ Database Metadata & Provenance                     │
│  ├─ ObjectRegistry (O(1) kind-verified lookup)         │
│  ├─ SchemaHierarchy (Deterministic tree navigation)    │
│  ├─ Typed References (ForeignKeyReference, TypedRef)   │
│  ├─ Capability Profile & Completeness Tracking         │
│  └─ Referential Integrity & Structural Validation      │
└────────────────────────────────────────────────────────┘
     │
     ▼
Phase 6.2+ Downstream Analysis (Constraint Reconstruction, ER Graphs, Dependency Analysis)
```

---

## 2. Core Non-Negotiable Principles

1. **Strictly AI/LLM/ML-Free**: Zero large language models, machine learning inference, probabilistic relationship guessing, or AI APIs.
2. **Deterministic & Reproducible**: Identical input metadata always produces identical schema representations and cryptographic SHA-256 digests.
3. **No Database Reconnection**: Operates purely on authorized, validated canonical metadata without modifying or re-querying live databases.
4. **No Arbitrary SQL Execution**: Views, triggers, and check constraints are cataloged as plain text without execution.
5. **Full Provenance Preservation**: Every schema object retains its source engine, version, native identifier, and extraction timestamp.
6. **No Silent Overwrites**: The `ObjectRegistry` detects and rejects duplicate canonical ObjectIds via `DuplicateRegistrationError`.

---

## 3. Key Modules

| Module | Purpose |
|---|---|
| [`dera.reverse_engineering.schema`](./CANONICAL_SCHEMA.md) | Root `SchemaRepresentation` model and public API |
| [`dera.reverse_engineering.builder`](./SCHEMA_BUILDER.md) | `SchemaBuilder` construction pipeline and resource limits |
| [`dera.reverse_engineering.registry`](./OBJECT_REGISTRY.md) | `ObjectRegistry` with O(1) kind-indexed lookup |
| [`dera.reverse_engineering.references`](./OBJECT_REFERENCES.md) | `TypedRef` and `ForeignKeyReference` models |
| [`dera.reverse_engineering.hierarchy`](./HIERARCHY.md) | `SchemaHierarchy` deterministic tree traversal |
| [`dera.reverse_engineering.validation`](./VALIDATION.md) | Structural and referential integrity validator |
| [`dera.reverse_engineering.ordering`](./DETERMINISM.md) | Deterministic sorting algorithms |
| [`dera.reverse_engineering.serialization`](./SERIALIZATION.md) | Canonical JSON serialization, hashing, and safe deserialization |
| [`dera.reverse_engineering.capabilities`](./COMPATIBILITY.md) | Capability profiling and completeness tracking |
| [`dera.reverse_engineering.errors`](./ARCHITECTURE.md) | Strongly typed error hierarchy |
| [`dera.reverse_engineering.models`](./ARCHITECTURE.md) | Schema model type aliases re-exported from Phase 5.5 |

---

## 4. Documentation Index

### Phase 6.1 — Canonical Schema Representation
- [Architecture & Design Decisions](./ARCHITECTURE.md)
- [Canonical Schema Root Contract](./CANONICAL_SCHEMA.md)
- [Schema Construction Pipeline](./SCHEMA_BUILDER.md)
- [Object Registry & Duplicate Detection](./OBJECT_REGISTRY.md)
- [Typed Object References & Foreign Keys](./OBJECT_REFERENCES.md)
- [Hierarchical Navigation API](./HIERARCHY.md)
- [Referential Integrity & Validation](./VALIDATION.md)
- [Deterministic Ordering & Digesting](./DETERMINISM.md)
- [Deterministic Serialization & Deserialization](./SERIALIZATION.md)
- [Security Controls & Workspace Isolation](./SECURITY.md)
- [Cross-Engine Compatibility](./COMPATIBILITY.md)
- [Automated Testing Strategy](./TESTING.md)

### Phase 6.3 — Foreign Key Relationship Graph
- [Foreign Key Graph Overview](./FOREIGN_KEY_GRAPH.md)
- [Graph Architecture & Directed Multigraph Design](./GRAPH_ARCHITECTURE.md)
- [Table Nodes & Identity](./GRAPH_NODES.md)
- [Foreign Key Edges & Constraint Mappings](./GRAPH_EDGES.md)
- [Composite Relationship Handling](./COMPOSITE_RELATIONSHIPS.md)
- [Adjacency Index & Bidirectional Lookup](./GRAPH_ADJACENCY.md)
- [Bounded Traversal & Component Analysis](./GRAPH_TRAVERSAL.md)
- [Graph Validation & Integrity Rules](./GRAPH_VALIDATION.md)
- [Deterministic Graph Serialization](./GRAPH_SERIALIZATION.md)
- [Graph Security & Resource Controls](./GRAPH_SECURITY.md)
- [Graph Testing Strategy](./GRAPH_TESTING.md)

### Phase 6.4 — Dependency Analysis & Cycle Detection
- [Dependency Analysis Overview](./DEPENDENCY_ANALYSIS.md)
- [Dependency Architecture & Pipeline Flow](./DEPENDENCY_ARCHITECTURE.md)
- [Cycle Detection & Classification](./CYCLE_DETECTION.md)
- [Strongly Connected Components (Tarjan's Algorithm)](./STRONGLY_CONNECTED_COMPONENTS.md)
- [Cycle Breakability & Remediation Analysis](./CYCLE_BREAKABILITY.md)
- [Topological Ordering & Condensation DAG](./TOPOLOGICAL_ORDERING.md)
- [Parallel Migration Levels (Generation Stratification)](./PARALLEL_MIGRATION_LEVELS.md)
- [Dependency Metrics & Structural Analysis](./DEPENDENCY_METRICS.md)
- [Dependency Validation Engine](./DEPENDENCY_VALIDATION.md)
- [Dependency Serialization & Fingerprinting](./DEPENDENCY_SERIALIZATION.md)
- [Dependency Security & Resource Protection](./DEPENDENCY_SECURITY.md)
- [Dependency Testing Strategy](./DEPENDENCY_TESTING.md)

### Phase 6.5 — Schema Snapshots & Deterministic Fingerprints
- [Schema Snapshots Overview](./SCHEMA_SNAPSHOTS.md)
- [Snapshot Architecture & Pipeline Flow](./SNAPSHOT_ARCHITECTURE.md)
- [Snapshot Format Specification](./SNAPSHOT_FORMAT.md)
- [Snapshot Canonicalization Specification](./SNAPSHOT_CANONICALIZATION.md)
- [Deterministic Cryptographic Fingerprints](./SNAPSHOT_FINGERPRINTS.md)
- [Snapshot Identity Model](./SNAPSHOT_IDENTITY.md)
- [Snapshot Provenance Specification](./SNAPSHOT_PROVENANCE.md)
- [Metadata Completeness in Snapshots](./SNAPSHOT_COMPLETENESS.md)
- [Cryptographic Integrity Verification](./SNAPSHOT_INTEGRITY.md)
- [Snapshot Storage Architecture](./SNAPSHOT_STORAGE.md)
- [Snapshot Retention & Lifecycle Management](./SNAPSHOT_RETENTION.md)
- [Snapshot Compatibility & Equivalence Model](./SNAPSHOT_COMPATIBILITY.md)
- [Snapshot Security Controls](./SNAPSHOT_SECURITY.md)
- [Snapshot Testing & Verification](./SNAPSHOT_TESTING.md)
- [Snapshot Performance Benchmarks](./SNAPSHOT_PERFORMANCE.md)

