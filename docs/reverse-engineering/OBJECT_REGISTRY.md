# Object Registry & Lookup API (Phase 6.1)

## 1. Overview

`ObjectRegistry` provides an efficient, type-safe, duplicate-detecting registry mapping canonical `ObjectId`s (`dera:<kind>:<24_hex_chars>`) to schema object models.

```python
from dera.reverse_engineering.registry import ObjectRegistry
```

---

## 2. Key Properties

1. **O(1) Direct Lookup**: All object retrievals by `ObjectId` operate in constant time.
2. **Duplicate Detection**: No silent replacement or implicit upsert. Calling `register()` with an existing `ObjectId` raises `DuplicateRegistrationError`.
3. **Kind-Verified Retrieval**: Dedicated typed lookup methods verify the underlying object kind and raise `InvalidSchemaReferenceError` if a kind mismatch occurs.
4. **Kind-Indexed Bucketing**: Maintains internal indexing by `ObjectKind` for instant queries of all tables, columns, foreign keys, or namespaces.
5. **Workspace Scope Preservation**: Captures tenant or workspace scope from the construction context for multi-tenant isolation.

---

## 3. Public API Methods

### Registration
```python
registry = ObjectRegistry(workspace_id="ws_finance")

registry.register(object_id: str, obj: Any, kind: str) -> None
registry.register_database(db: CanonicalDatabase) -> None
registry.register_namespace(ns: CanonicalNamespace) -> None
registry.register_table(table: CanonicalTable) -> None
registry.register_column(col: CanonicalColumn) -> None
registry.register_constraint(constraint: CanonicalConstraint) -> None
registry.register_foreign_key(fk: CanonicalForeignKey) -> None
registry.register_index(index: CanonicalIndex) -> None
registry.register_view(view: CanonicalView) -> None
registry.register_trigger(trigger: CanonicalTrigger) -> None
```

### Generic & Typed Lookup
```python
registry.get_object(object_id: str) -> Any | None
registry.contains(object_id: str) -> bool

# Typed methods raise InvalidSchemaReferenceError if missing or wrong kind:
registry.get_database(object_id: str) -> CanonicalDatabase
registry.get_namespace(object_id: str) -> CanonicalNamespace
registry.get_table(object_id: str) -> CanonicalTable
registry.get_column(object_id: str) -> CanonicalColumn
registry.get_constraint(object_id: str) -> CanonicalConstraint
registry.get_foreign_key(object_id: str) -> CanonicalForeignKey
registry.get_index(object_id: str) -> CanonicalIndex
registry.get_view(object_id: str) -> CanonicalView
registry.get_trigger(object_id: str) -> CanonicalTrigger
```

### Kind Collections & Metrics
```python
registry.all_of_kind(kind: str) -> tuple[Any, ...]
registry.all_tables() -> tuple[CanonicalTable, ...]
registry.all_namespaces() -> tuple[CanonicalNamespace, ...]
registry.all_columns() -> tuple[CanonicalColumn, ...]
registry.all_foreign_keys() -> tuple[CanonicalForeignKey, ...]

registry.total_objects -> int
registry.workspace_id -> str | None
registry.object_count_by_kind() -> dict[str, int]
```

### Reference Resolution
```python
registry.resolve_ref(ref: TypedRef) -> TypedRef
```
Resolves a `TypedRef` against registered objects and returns an updated reference with status `RESOLVED`, `MISSING`, or `INVALID`.
