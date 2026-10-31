# Typed Object References & Foreign Key References (Phase 6.1)

## 1. Overview

Schema objects frequently point to other objects (e.g. columns pointing to parent tables, foreign keys pointing to target tables). Instead of using untyped strings or circular Python pointers, DERA uses **strongly typed, resolution-aware references**:

```python
from dera.reverse_engineering.references import (
    ForeignKeyReference,
    ResolutionStatus,
    TypedRef,
)
```

---

## 2. Resolution Status

`ResolutionStatus` enumerates all possible outcomes of an object reference resolution attempt:

| Status | Meaning |
|---|---|
| `RESOLVED` | Target `ObjectId` was found in the schema registry with the expected object kind. |
| `MISSING` | Target `ObjectId` is not present in the current schema representation. |
| `RESTRICTED` | Target exists but catalog access was restricted by database user permissions. |
| `UNSUPPORTED`| Target kind is not supported by the inspected engine catalog. |
| `AMBIGUOUS` | Multiple objects match the reference specification. |
| `INVALID` | The reference is structurally malformed or targets an object of the wrong kind. |

---

## 3. TypedRef Specification

`TypedRef[T]` is a generic, frozen Pydantic model:

```python
class TypedRef(BaseModel, Generic[T]):
    target_id: str                      # Canonical ObjectId: dera:<kind>:<hex>
    expected_kind: str                  # Expected ObjectKind string
    status: ResolutionStatus = MISSING   # Resolution status
    source_context: str | None = None   # Human-readable context

    # Properties & Transitions
    is_resolved: bool
    is_missing: bool
    def resolve() -> TypedRef[T]
    def mark_missing() -> TypedRef[T]
    def mark_restricted() -> TypedRef[T]
    def mark_invalid() -> TypedRef[T]
```

---

## 4. ForeignKeyReference Specification

`ForeignKeyReference` represents verified relational foreign key links:

```python
class ForeignKeyReference(BaseModel):
    foreign_key_id: str  # Canonical ObjectId of the FK
    foreign_key_name: str  # Native or surrogate constraint name
    source_table_id: str  # Child table ObjectId
    source_table_name: str  # Native child table name
    source_columns: tuple[str, ...]  # Referencing columns in child table
    referenced_table_id: str | None  # Resolved parent table ObjectId
    referenced_table_name: str  # Target parent table name
    referenced_schema: str | None  # Target parent schema name
    referenced_columns: tuple[str, ...]  # Referenced columns in parent table
    on_update: str = "NO ACTION"  # Referential action on UPDATE
    on_delete: str = "NO ACTION"  # Referential action on DELETE
    status: ResolutionStatus = MISSING  # Resolution status in schema registry
```

During `SchemaBuilder` construction, target tables are deterministically resolved against the `ObjectRegistry`. If the referenced table exists in the schema, `referenced_table_id` is linked and `status` transitions to `RESOLVED`. If absent, it remains `MISSING` without inventing fictional placeholder objects.
