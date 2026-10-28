# Canonical Schema Representation Contract (Phase 6.1)

## 1. Overview

`SchemaRepresentation` is the root immutable model representing one authorized, validated database schema inspection result. It provides a strongly typed API for accessing:
- Database identity and provenance
- Hierarchical namespaces, tables, columns, constraints, indexes, triggers, and views
- Foreign key referential linkages and resolution states
- Object registry and O(1) typed lookup
- Engine capability profile and completeness assessment
- Referential integrity validation diagnostics

```python
from dera.reverse_engineering.schema import SchemaRepresentation
```

---

## 2. Model Specification

```python
class SchemaRepresentation(BaseModel):
    contract_version: str = "1.0.0"
    database_id: str                      # Canonical ObjectId: dera:database:<24hex>
    database_name: str                    # Logical database identifier
    engine: str                           # 'postgresql', 'sqlite', 'mysql', 'mariadb'
    engine_version: str | None = None     # Server version string
    source_reference: str                 # Authorized connection label (no credentials)
    provenance: MetadataProvenance        # Audit extraction provenance
    database: CanonicalDatabase           # Normalized CanonicalDatabase root
    namespaces: tuple[CanonicalNamespace, ...] # Deterministically ordered schemas
    foreign_key_references: tuple[ForeignKeyReference, ...] # Resolved FK links
    capability_profile: SchemaCapabilityProfile | None = None
    completeness: MetadataCompleteness = MetadataCompleteness.COMPLETE
    is_validated: bool = False            # Referential integrity validation status
    validation_issues: tuple[str, ...] = ()
    resource_metrics: dict[str, Any]      # Bounded metrics (object counts, etc.)
```

---

## 3. Public API Methods

### Object Lookup
```python
schema.get_object(object_id: str) -> Any | None
schema.contains(object_id: str) -> bool
schema.get_database(object_id: str) -> CanonicalDatabase
schema.get_namespace(object_id: str) -> CanonicalNamespace
schema.get_table(object_id: str) -> CanonicalTable
schema.get_column(object_id: str) -> CanonicalColumn
schema.get_constraint(object_id: str) -> CanonicalConstraint
schema.get_foreign_key(object_id: str) -> CanonicalForeignKey
schema.get_index(object_id: str) -> CanonicalIndex
schema.get_view(object_id: str) -> CanonicalView
schema.get_trigger(object_id: str) -> CanonicalTrigger
```

### Hierarchical Queries
```python
schema.find_table(schema_name: str, table_name: str) -> CanonicalTable | None
schema.find_column(schema_name: str, table_name: str, column_name: str) -> CanonicalColumn | None
schema.all_tables() -> tuple[CanonicalTable, ...]
schema.all_views() -> tuple[CanonicalView, ...]
schema.all_foreign_keys() -> tuple[CanonicalForeignKey, ...]
```

### Deterministic Serialization
```python
schema.to_dict() -> dict[str, Any]
schema.to_json(indent: int | None = 2) -> str
schema.compute_hash() -> str  # SHA-256 fingerprint over compact JSON bytes
```

### Properties
```python
schema.total_objects -> int           # Total count of registered objects
schema.build_duration_ms -> float | None # Elapsed construction time in ms
schema.registry -> ObjectRegistry     # Backing O(1) object registry
schema.hierarchy -> SchemaHierarchy   # Deterministic hierarchy navigator
```
