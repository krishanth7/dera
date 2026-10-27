# Hierarchical Navigation (Phase 6.1)

## 1. Overview

`SchemaHierarchy` provides stable, deterministic navigation over the schema registry, traversing the relational database hierarchy:

```
Database
   │
   └── Namespaces (Schemas)
            │
            ├── Tables
            │     ├── Columns (Ordered by ordinal position)
            │     ├── Primary Key
            │     ├── Unique Constraints
            │     ├── Check Constraints
            │     ├── Foreign Keys
            │     ├── Secondary Indexes
            │     └── Triggers
            │
            └── Views (Regular & Materialized)
```

```python
from dera.reverse_engineering.hierarchy import SchemaHierarchy
```

---

## 2. Navigation API

All methods return deterministically sorted immutable tuples:

### Database Level
```python
hierarchy = schema.hierarchy

hierarchy.database(database_id: str) -> CanonicalDatabase
hierarchy.namespaces(database_id: str) -> tuple[CanonicalNamespace, ...]
```

### Namespace Level
```python
hierarchy.tables(namespace_id: str) -> tuple[CanonicalTable, ...]
hierarchy.views(namespace_id: str) -> tuple[CanonicalView, ...]
```

### Table Level
```python
hierarchy.columns(table_id: str) -> tuple[CanonicalColumn, ...] # By ordinal_position
hierarchy.primary_key(table_id: str) -> CanonicalConstraint | None
hierarchy.unique_constraints(table_id: str) -> tuple[CanonicalConstraint, ...]
hierarchy.check_constraints(table_id: str) -> tuple[CanonicalConstraint, ...]
hierarchy.all_constraints(table_id: str) -> tuple[CanonicalConstraint, ...]
hierarchy.foreign_keys(table_id: str) -> tuple[CanonicalForeignKey, ...]
hierarchy.indexes(table_id: str) -> tuple[CanonicalIndex, ...]
hierarchy.triggers(table_id: str) -> tuple[CanonicalTrigger, ...]
```

### Cross-Database Queries
```python
hierarchy.all_tables_in_database(database_id: str) -> tuple[CanonicalTable, ...]
hierarchy.all_views_in_database(database_id: str) -> tuple[CanonicalView, ...]
hierarchy.all_foreign_keys_in_database(database_id: str) -> tuple[CanonicalForeignKey, ...]
```

---

## 3. Deterministic Guarantees

- **Namespaces**: Alphabetically sorted by name (`ns.name.lower(), ns.name`).
- **Tables**: Alphabetically sorted by name (`tbl.name.lower(), tbl.name`).
- **Columns**: Strictly ordered by 1-based `ordinal_position`, then name.
- **Constraints**: Alphabetically sorted by name (`c.name.lower(), c.name`).
- **Indexes**: Sorted by `is_primary DESC`, `is_unique DESC`, then name.
- **Foreign Keys**: Sorted by `name ASC`, then referenced table name.
- **Triggers & Views**: Alphabetically sorted by name.
