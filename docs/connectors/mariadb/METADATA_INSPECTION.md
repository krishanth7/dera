# MariaDB Connector Metadata Inspection

## Overview

The DERA MariaDB Connector deterministically inspects relational schema metadata from MariaDB 10.11+ and 11.4 LTS catalogs. All inspection logic queries `INFORMATION_SCHEMA` with fixed parameters, deterministic sorting, and system schema exclusions.

---

## Catalog Queries & Extracted Metadata

### 1. Schema Enumeration (`list_schemas`)

Queries `INFORMATION_SCHEMA.SCHEMATA` excluding internal administrative schemas:

- Excluded schemas: `information_schema`, `performance_schema`, `mysql`, `sys`.
- Extracts: `SCHEMA_NAME`, default `CHARACTER_SET_NAME`, and default `COLLATION_NAME`.
- Ordering: `ORDER BY SCHEMA_NAME ASC`.

### 2. Table Enumeration (`list_tables`)

Queries `INFORMATION_SCHEMA.TABLES` within the target schema:

- Extracts: `TABLE_NAME`, `TABLE_TYPE`, `ENGINE` (`InnoDB`, `Aria`, `MyISAM`), `TABLE_COMMENT`, `TABLE_COLLATION`, `AUTO_INCREMENT`.
- Storage engines: Correctly captures MariaDB-specific engines such as `Aria` in `engine_specific["storage_engine"]`.
- Ordering: `ORDER BY TABLE_SCHEMA ASC, TABLE_NAME ASC`.

### 3. Column Inspection (`list_columns`)

Queries `INFORMATION_SCHEMA.COLUMNS`:

- Extracts: `COLUMN_NAME`, `ORDINAL_POSITION`, `DATA_TYPE`, `COLUMN_TYPE`, `IS_NULLABLE`, `COLUMN_DEFAULT`, `EXTRA`, `GENERATION_EXPRESSION`, `CHARACTER_SET_NAME`, `COLLATION_NAME`, `COLUMN_COMMENT`.
- MariaDB generated columns: `EXTRA` containing `VIRTUAL` or `PERSISTENT` marks `is_generated=True`, with `generation_type` recorded as `VIRTUAL` or `STORED`.
- Ordering: `ORDER BY ORDINAL_POSITION ASC`.

### 4. Primary Key Inspection (`get_primary_key`)

Queries `INFORMATION_SCHEMA.KEY_COLUMN_USAGE`:

- Identifies constraints where `CONSTRAINT_NAME = 'PRIMARY'`.
- Returns `PrimaryKeyInfo` with columns ordered by `ORDINAL_POSITION ASC`.

### 5. Foreign Key Inspection (`list_foreign_keys`)

Queries `INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS` joined with `KEY_COLUMN_USAGE`:

- Extracts: `CONSTRAINT_NAME`, source columns, referenced table, referenced columns, update/delete actions.
- Ordering: `ORDER BY tc.CONSTRAINT_NAME ASC, kcu.ORDINAL_POSITION ASC`.

### 6. Unique Constraints (`list_unique_constraints`)

Queries `INFORMATION_SCHEMA.TABLE_CONSTRAINTS` joined with `KEY_COLUMN_USAGE`:

- Excludes primary key constraints (`CONSTRAINT_TYPE = 'UNIQUE'`).
- Grouped by constraint name and ordered deterministically.

### 7. Check Constraints (`list_check_constraints`)

Queries `INFORMATION_SCHEMA.CHECK_CONSTRAINTS` (MariaDB 10.2+):

- Extracts constraint name and boolean `CHECK_CLAUSE` expression text.
- Fallback queries handle dialect differences between MySQL 8.0 and MariaDB table schemas.

### 8. Index Inspection (`list_indexes`)

Queries `INFORMATION_SCHEMA.STATISTICS`:

- Uses MariaDB-compatible statistics query columns without requiring MySQL 8-specific expression extensions.
- Grouped by `INDEX_NAME` with columns ordered by `SEQ_IN_INDEX ASC`.

### 9. View Inspection (`list_views`)

Queries `INFORMATION_SCHEMA.VIEWS`:

- Extracts view definitions, check options, and definer metadata text without executing view definitions.

### 10. Trigger Inspection (`list_triggers`)

Queries `INFORMATION_SCHEMA.TRIGGERS`:

- Extracts trigger name, timing, event manipulation, and body text without executing triggers.
