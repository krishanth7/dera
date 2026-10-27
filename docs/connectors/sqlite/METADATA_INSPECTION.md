# DERA SQLite Metadata Inspection

## Overview

The SQLite metadata engine (`packages/connectors/src/dera_connectors/sqlite/catalog.py`) uses documented SQLite 3 catalog mechanisms to inspect relational structures without executing customer tables, views, or triggers.

---

## Catalog Queries & PRAGMAs

| Object Type | Primary Source | Fallback Source | Deterministic Sorting |
|---|---|---|---|
| **Schemas** | `PRAGMA database_list;` | — | `schema_name ASC` |
| **Tables** | `SELECT name, type, sql FROM sqlite_schema WHERE type='table';` | — | `schema_name ASC, table_name ASC` |
| **Columns** | `PRAGMA table_xinfo("tbl");` | `PRAGMA table_info("tbl");` | `ordinal_position ASC` |
| **Primary Keys** | Filtered from `table_xinfo` (ordered by `pk` column) | — | Primary key column order |
| **Foreign Keys** | `PRAGMA foreign_key_list("tbl");` | — | Source column sequence |
| **Unique Constraints** | `PRAGMA index_list("tbl");` (`origin='u'`) | — | `constraint_name ASC` |
| **Check Constraints** | Deterministic DDL parsing of `sql` | — | `constraint_name ASC` |
| **Indexes** | `PRAGMA index_list("tbl");` + `PRAGMA index_xinfo("idx");` | `PRAGMA index_info("idx");` | `index_name ASC` |
| **Views** | `SELECT name, sql FROM sqlite_schema WHERE type='view';` | — | `view_name ASC` |
| **Triggers** | `SELECT name, tbl_name, sql FROM sqlite_schema WHERE type='trigger';` | — | `trigger_name ASC` |

---

## Special Structure Extraction

### `STRICT` & `WITHOUT ROWID` Tables

The connector parses trailing table options from the `CREATE TABLE` definition in `sqlite_schema.sql`:
- Detects `STRICT` keyword and sets `TableInfo.engine_specific["is_strict"] = True`.
- Detects `WITHOUT ROWID` clause and sets `TableInfo.engine_specific["without_rowid"] = True`.

### Generated & Hidden Columns

`PRAGMA table_xinfo` returns a `hidden` integer flag:
- `0`: Normal column.
- `1`: Hidden column in a virtual table.
- `2`: Stored generated column (`GENERATED ALWAYS AS (...) STORED`).
- `3`: Virtual generated column (`GENERATED ALWAYS AS (...) VIRTUAL`).

`ColumnInfo.is_generated` is set to `True` for flags 2 and 3.

### Check Constraint Extraction

Because SQLite does not maintain an internal `information_schema.check_constraints` catalog, DERA implements a deterministic SQL tokenizer:
1. Locates column-level and table-level `CHECK (...)` clauses in `sqlite_schema.sql`.
2. Resolves explicit constraint names if prefixed by `CONSTRAINT name CHECK (...)`.
3. Preserves nested parenthesis structures without executing expressions.
