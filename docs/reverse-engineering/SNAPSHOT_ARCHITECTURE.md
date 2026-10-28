# Schema Snapshot Architecture

## 1. Architectural Position

The Schema Snapshot Subsystem functions as the persistent culmination of the DERA Reverse Engineering Core Engine pipeline.

```text
┌────────────────────────────────────────────────────────┐
│ Phase 5: Connector & Canonical Metadata Ingestion      │
└───────────────────────────┬────────────────────────────┘
                            │ CanonicalDatabase
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 6.1: Canonical Schema Representation             │
└───────────────────────────┬────────────────────────────┘
                            │ SchemaRepresentation
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 6.2: Structural Reconstruction                   │
└───────────────────────────┬────────────────────────────┘
                            │ ReconstructedDatabase
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 6.3: Foreign Key Relationship Graph              │
└───────────────────────────┬────────────────────────────┘
                            │ ForeignKeyGraph
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 6.4: Dependency Analysis & Cycle Detection       │
└───────────────────────────┬────────────────────────────┘
                            │ DependencyAnalysisResult
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 6.5: Schema Snapshot Builder                     │
│  - Cross-Phase Consistency Verification                │
│  - Structural Payload Canonicalization                 │
│  - RFC 8785 Compact JSON Serialization                 │
│  - SHA-256 Fingerprint with Domain Separation          │
│  - Envelope Construction & Provenance Binding          │
│  - Immutability Enforcement                            │
└───────────────────────────┬────────────────────────────┘
                            │ SchemaSnapshot
                            ▼
┌────────────────────────────────────────────────────────┐
│ Storage & Persistence Engine                           │
│  - InMemorySnapshotStorage (Content Deduplication)     │
│  - FileSystemSnapshotStorage (Atomic tmp+replace)      │
│  - Workspace Isolation & Directory Traversal Guards    │
│  - Retention Policies & Expiration Pruning             │
└────────────────────────────────────────────────────────┘
```

---

## 2. Ingestion Pipeline & Cross-Phase Validation

The `SchemaSnapshotBuilder.from_analysis` factory coordinates inputs from earlier phases:
1. **SchemaRepresentation** (Phase 6.1): Provides canonical tables, views, columns, constraints, indexes, and native expressions.
2. **ReconstructedDatabase** (Phase 6.2, optional): Provides enriched structural reconstructions.
3. **ForeignKeyGraph** (Phase 6.3, optional): Provides verified relationship topology edges.
4. **DependencyAnalysisResult** (Phase 6.4, optional): Provides dependency ordering, cycle reports, and SCC metrics.

### Cross-Phase Identity Consistency

Before construction begins, the builder validates:
- `database_id`: Matches identically across `schema`, `reconstructed`, `graph`, and `dependencies`.
- `database_name`: Matches identically across all provided components.
- `engine`: Matches identically across all provided components.
- Workspace boundary: Verifies all components belong to the designated workspace.

If any discrepancy is detected, `SnapshotValidationError` is raised immediately, preventing corrupted hybrid snapshots.

---

## 3. Structural Payload vs. Operational Envelope Separation

A core architectural principle of DERA is the strict demarcation between:

### Structural Payload (`SnapshotStructuralPayload`)
The intrinsic, schema-defining content that affects database structure, semantics, and relationships:
- Database identity and name
- Engine identifier (`postgresql`, `sqlite`, `mysql`, `mariadb`)
- Canonical tables and columns (types, nullability, defaults)
- Primary, foreign key, unique, and check constraints
- Indexes and unicity
- Views and definitions
- Triggers and event bindings
- Verified relationships (edges)
- Dependency metrics and cycle summaries
- Metadata completeness level

### Operational Envelope (`SnapshotEnvelope`)
Volatile operational context that varies across captures but does not alter schema structure:
- Capture timestamp (`datetime` in UTC)
- Workspace identity (`workspace_id`)
- Requester identity (`user_id`, `client_id`)
- Source provenance (`SnapshotProvenance`: engine version, connector version, consistency indicator)
- Storage metadata (tags, custom labels)
- Validation findings and status

**Crucial Guarantee**: Re-capturing the identical database schema at different times or from different workspaces produces an identical structural fingerprint.

---

## 4. Immutability Architecture

All snapshot classes are configured with Pydantic v2 `ConfigDict(frozen=True, extra="forbid")`:
- Attempting to mutate any attribute on `SchemaSnapshot`, `SnapshotStructuralPayload`, or child payload records raises `pydantic.ValidationError`.
- Nested sequences are represented as immutable tuples (`tuple[...]`).
- In-memory repositories perform defensive shallow copies (`model_copy()`), while filesystem repositories serialize to immutable read-only JSON files.
