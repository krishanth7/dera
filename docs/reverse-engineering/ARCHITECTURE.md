# Reverse Engineering Core Engine Architecture (Phase 6.1)

## 1. Architectural Positioning

Phase 6.1 sits between Phase 5 Canonical Metadata and downstream Phase 6 reverse-engineering modules:

```
┌──────────────────────────────────────────────┐
│  Phase 5.1 - 5.4 Multi-Engine Connectors    │
│  (PostgreSQL, Supabase, SQLite, MySQL, Maria)│
└──────────────────────┬───────────────────────┘
                       │ DatabaseMetadataReport
                       ▼
┌──────────────────────────────────────────────┐
│  Phase 5.5 Canonical Metadata Normalization  │
│  (Length-prefixed SHA-256 stable ObjectId)   │
└──────────────────────┬───────────────────────┘
                       │ CanonicalDatabase
                       ▼
┌────────────────────────────────────────────────────────┐
│  Phase 6.1 Canonical Schema Representation Layer       │
│                                                        │
│   SchemaBuilder                                        │
│   ├── Enforces resource limits & contract check        │
│   ├── Normalizes collection ordering                   │
│   ├── Builds ObjectRegistry (O(1) kind-indexed access) │
│   ├── Builds SchemaHierarchy (Deterministic traversal) │
│   ├── Resolves Foreign Key References                  │
│   └── Assesses Capability & Completeness Profile       │
│                                                        │
│   SchemaRepresentation (Root Immutable Domain Model)   │
│   ├── to_dict() / to_json() (Canonical JSON)           │
│   ├── compute_hash() (Stable SHA-256 fingerprint)      │
│   ├── get_object(), get_table(), get_column()...       │
│   └── Referential integrity validation state           │
└──────────────────────┬─────────────────────────────────┘
                       │ Validated SchemaRepresentation
                       ▼
┌──────────────────────────────────────────────┐
│  Phase 6.2 - Detailed Structural Analysis    │
│  - Table, column, & constraint reconstruction│
│  - Relationship graphs & ER models           │
│  - Dependency & impact analysis              │
└──────────────────────────────────────────────┘
```

---

## 2. Immutability & Model Reuse

DERA strictly adheres to:
1. **Reuse Existing Domain Models**:
   Reuses `CanonicalDatabase`, `CanonicalNamespace`, `CanonicalTable`, `CanonicalColumn`, `CanonicalConstraint`, `CanonicalIndex`, `CanonicalView`, and `CanonicalTrigger` from `dera.metadata.models`.
   Exposes aliases in `dera.reverse_engineering.models` (`TableRepresentation = CanonicalTable`, etc.) without maintaining duplicated copies.
2. **Immutability by Default**:
   All models inherit Pydantic v2 `ConfigDict(frozen=True)`.
   Intermediate mutable collections used during construction are strictly finalized and frozen into tuples before returning `SchemaRepresentation`.
3. **Private Encapsulation**:
   Heavy runtime state (`ObjectRegistry`, `SchemaHierarchy`, `_build_duration_ms`) is held in private attributes (`PrivateAttr`), keeping public serializations clean and deterministic.

---

## 3. Strongly Typed Error Hierarchy

All Phase 6.1 errors inherit from `SchemaRepresentationError`, derived from `dera_core.exceptions.DeraError`:

```
DeraError
  └── SchemaRepresentationError
        ├── SchemaBuilderError
        │     ├── UnsupportedSchemaContractError
        │     └── InvalidSchemaInputError
        ├── DuplicateRegistrationError
        ├── InvalidSchemaReferenceError
        ├── MissingParentError
        ├── SchemaResourceLimitError
        ├── SchemaValidationError
        └── SchemaSerializationError
```

### Error Catalog

| Error Class | Trigger Scenario |
|---|---|
| `SchemaRepresentationError` | Root exception for all reverse-engineering schema failures. |
| `UnsupportedSchemaContractError` | Metadata uses an unsupported contract version (e.g. not `"1.0.0"`). |
| `InvalidSchemaInputError` | Input is not a valid `CanonicalDatabase` or metadata report dict. |
| `DuplicateRegistrationError` | Multiple objects attempt to register under the same canonical `ObjectId`. |
| `InvalidSchemaReferenceError` | Reference lookup targets a missing ID or mismatched object kind. |
| `MissingParentError` | Child object (table, column, constraint) declares a missing parent `ObjectId`. |
| `SchemaResourceLimitError` | Payload exceeds max objects, identifier length, or definition bytes. |
| `SchemaValidationError` | Referential integrity check fails (e.g. foreign key column missing). |
| `SchemaSerializationError` | JSON serialization, hashing, or safe deserialization encounters an error. |
