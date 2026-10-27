# Canonical Metadata Contracts

**Contract Specification:** DERA Canonical Schema v1.0.0  
**Implementation:** `dera.metadata.contracts`  

---

## 1. Contract Overview

All normalized metadata models inherit from Pydantic `BaseModel` with `ConfigDict(frozen=True)` to ensure total immutability and thread safety throughout reverse-engineering pipelines.

---

## 2. Model Definitions

### CanonicalDatabase
- `id: str`: Cryptographic root ObjectId.
- `name: str`: Logical database identifier.
- `engine: str`: Engine dialect string (`postgresql`, `sqlite`, `mysql`, `mariadb`).
- `contract_version: str`: Schema contract version (`"1.0.0"`).
- `namespaces: tuple[CanonicalNamespace, ...]`: Deterministically sorted namespaces.
- `provenance: MetadataProvenance`: Root extraction provenance.

### CanonicalNamespace
- `id: str`: Namespace ObjectId.
- `name: str`: Native schema name (`public`, `main`, etc.).
- `tables: tuple[CanonicalTable, ...]`: Alphabetically sorted tables.
- `views: tuple[CanonicalView, ...]`: Alphabetically sorted views.
- `comment: str | None`: Optional documentation remark.
- `provenance: MetadataProvenance`: Namespace audit provenance.

### CanonicalTable
- `id: str`: Table ObjectId.
- `namespace_id: str`: Owning namespace ObjectId.
- `name: str`: Native declared table identifier.
- `table_type: TableType`: `TABLE`, `SYSTEM_TABLE`, `PARTITIONED_TABLE`.
- `columns: tuple[CanonicalColumn, ...]`: Ordinal-sorted columns.
- `primary_key: CanonicalConstraint | None`: Explicit primary key constraint.
- `foreign_keys: tuple[CanonicalForeignKey, ...]`: Foreign key constraints.
- `unique_constraints: tuple[CanonicalConstraint, ...]`: Non-primary unique constraints.
- `check_constraints: tuple[CanonicalConstraint, ...]`: Evaluated check constraints.
- `indexes: tuple[CanonicalIndex, ...]`: Secondary indexes.
- `triggers: tuple[CanonicalTrigger, ...]`: Procedural triggers.
- `comment: str | None`: Table documentation comment.
- `provenance: MetadataProvenance`: Table extraction audit record.

### CanonicalColumn
- `id: str`: Column ObjectId.
- `parent_table_id: str`: Parent table ObjectId.
- `name: str`: Native column identifier.
- `ordinal_position: int`: 1-based column position.
- `native_data_type: str`: Full declared database type.
- `canonical_type: CanonicalTypeCategory`: High-level taxonomy category.
- `is_nullable: bool`: Nullability enforcement.
- `default_expression: str | None`: Raw default value expression.
- `is_identity: bool`: Auto-increment/serial flag.
- `is_generated: bool`: Computed/generated column indicator.
- `generation_mode: GenerationMode`: `STORED`, `VIRTUAL`, or `NONE`.
- `generation_expression: str | None`: Expression formula.
- `provenance: MetadataProvenance`: Column audit record.
