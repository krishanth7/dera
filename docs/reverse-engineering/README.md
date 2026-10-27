# DERA Reverse Engineering Core Engine — Canonical Schema Representation (Phase 6.1)

Welcome to the **DERA Reverse Engineering Core Engine** documentation.

Phase 6.1 delivers the foundational **Canonical Schema Representation Layer** that transforms validated Phase 5.5 canonical database metadata into a coherent, strongly-typed, navigable, registry-backed representation of database architecture.

---

## 1. Mission & Architectural Role

DERA (Database Engineering & Reverse Analysis) is a deterministic database engineering platform. Its tagline is:
> *Understand Every Schema. Engineer Every Change.*

In Phase 6.1, the schema representation layer bridges the gap between raw catalog metadata and advanced reverse-engineering operations:

```
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
