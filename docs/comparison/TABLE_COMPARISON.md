# Table & Child Object Comparison Semantics

**Phase:** 9.1 — Deterministic Schema Snapshot Comparison Engine  

---

## 1. Table Change Granularity

To prevent false alarms, modifying a single column, index, or constraint does **not** cause the entire table to be reported as replaced or modified.
- **Table-Level Modifications:** Reported only if table-level metadata changed (e.g. `table_type` or `comment`).
- **Child-Level Modifications:** Contained columns, primary keys, foreign keys, unique constraints, check constraints, and indexes produce their own granular `SchemaChange` records scoped with `parent_canonical_id` and `parent_name`.

## 2. Supported Object Types
- `TABLE`: Existence, type, and documentation changes.
- `COLUMN`: Type, nullability, defaults, ordinals, length, precision, scale, documentation.
- `PRIMARY_KEY`: Column membership and column ordering.
- `FOREIGN_KEY`: Source columns, target namespace/table/columns, on_update/on_delete actions, deferrability.
- `UNIQUE_CONSTRAINT`: Constrained column sequence.
- `CHECK_CONSTRAINT`: Inert boolean expression comparison.
- `INDEX`: Method, columns, uniqueness, predicates.
- `VIEW`: Definition, materialized flag.
- `RELATIONSHIP`: Directed FK multigraph edges (child table -> parent table).
