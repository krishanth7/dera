# DERA SQLite Capabilities Matrix

## Capability Declaration

The SQLite connector reports its supported features through the Phase 5.1 `ConnectorCapabilities` model in `packages/connectors/src/dera_connectors/sqlite/capabilities.py`.

---

## Detailed Capabilities Table

| Capability | Status | Notes |
|---|---|---|
| `SCHEMA_ENUMERATION` | **SUPPORTED** | Discovers database namespaces via `PRAGMA database_list`. |
| `TABLE_ENUMERATION` | **SUPPORTED** | Enumerates ordinary, virtual, `STRICT`, and `WITHOUT ROWID` tables. |
| `COLUMN_INSPECTION` | **SUPPORTED** | Discovers columns, ordinals, nullability, defaults, and affinities. |
| `PRIMARY_KEY_INSPECTION` | **SUPPORTED** | Inspects single-column, composite, and `WITHOUT ROWID` primary keys. |
| `FOREIGN_KEY_INSPECTION` | **SUPPORTED** | Inspects source/target tables, columns, `ON UPDATE`, and `ON DELETE`. |
| `UNIQUE_CONSTRAINT_INSPECTION` | **SUPPORTED** | Extracts unique constraints backed by unique indexes or DDL definitions. |
| `CHECK_CONSTRAINT_INSPECTION` | **SUPPORTED** | Deterministic DDL parsing of column and table `CHECK (...)` clauses. |
| `INDEX_INSPECTION` | **SUPPORTED** | Inspects standard, partial, and expression indexes via `index_xinfo`. |
| `VIEW_INSPECTION` | **SUPPORTED** | Discovers view definitions from `sqlite_schema` without execution. |
| `TRIGGER_INSPECTION` | **SUPPORTED** | Discovers trigger definitions from `sqlite_schema` without execution. |
| `GENERATED_COLUMNS` | **SUPPORTED** | Distinguishes `STORED` and `VIRTUAL` generated columns. |
| `MATERIALIZED_VIEW_INSPECTION` | **UNSUPPORTED** | SQLite does not support native materialized views. |
| `PROCEDURE_INSPECTION` | **UNSUPPORTED** | SQLite does not support stored procedures. |
| `SEQUENCE_INSPECTION` | **UNSUPPORTED** | SQLite does not have standalone sequence objects (`AUTOINCREMENT` is table-bound). |
| `FUNCTION_INSPECTION` | **UNSUPPORTED** | User-defined functions are registered in host application memory. |
| `PARTITION_INSPECTION` | **UNSUPPORTED** | SQLite does not provide native partitioned tables. |
