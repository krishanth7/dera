# MySQL Connector Metadata Inspection

## Overview

The DERA MySQL Connector deterministically inspects relational schema metadata from MySQL 8.0+ and 8.4 LTS catalogs. All inspection logic queries `INFORMATION_SCHEMA` with fixed parameters, deterministic sorting, and system schema exclusions.

---

## Catalog Queries & Extracted Metadata

### 1. Schema Enumeration (`list_schemas`)

Queries `INFORMATION_SCHEMA.SCHEMATA` excluding internal administrative schemas:

- Excluded schemas: `information_schema`, `performance_schema`, `mysql`, `sys`.
- Extracts: `SCHEMA_NAME`, default `CHARACTER_SET_NAME`, and default `COLLATION_NAME`.
- Ordering: `ORDER BY SCHEMA_NAME ASC`.

### 2. Table Enumeration (`list_tables`)

Queries `INFORMATION_SCHEMA.TABLES` within the target schema:

- Extracts: `TABLE_NAME`, `TABLE_TYPE` (`TABLE` vs `VIEW`), `ENGINE` (e.g. `InnoDB`), `TABLE_COMMENT`, `TABLE_COLLATION`, `AUTO_INCREMENT`.
- Ordering: `ORDER BY TABLE_SCHEMA ASC, TABLE_NAME ASC`.

### 3. Column Inspection (`list_columns`)

Queries `INFORMATION_SCHEMA.COLUMNS`:

- Extracts: `COLUMN_NAME`, `ORDINAL_POSITION`, `DATA_TYPE`, `COLUMN_TYPE`, `IS_NULLABLE`, `COLUMN_DEFAULT`, `EXTRA`, `GENERATION_EXPRESSION`, `CHARACTER_SET_NAME`, `COLLATION_NAME`, `COLUMN_COMMENT`.
- Identity handling: `EXTRA` containing `auto_increment` marks `is_identity=True`.
- Generated columns: `EXTRA` containing `VIRTUAL GENERATED` or `STORED GENERATED` marks `is_generated=True` and populates `generation_expression`.
- Attribute parsing: `parse_column_type_attributes` extracts `is_unsigned`, `is_zerofill`, `is_boolean_alias` (`tinyint(1)`), `enum_values`, and `set_members`.
- Ordering: `ORDER BY ORDINAL_POSITION ASC`.

### 4. Primary Key Inspection (`get_primary_key`)

Queries `INFORMATION_SCHEMA.KEY_COLUMN_USAGE`:

- Identifies constraints where `CONSTRAINT_NAME = 'PRIMARY'`.
- Returns `PrimaryKeyInfo` with columns ordered by `ORDINAL_POSITION ASC`.

### 5. Foreign Key Inspection (`list_foreign_keys`)

Queries `INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS` joined with `KEY_COLUMN_USAGE`:

- Extracts: `CONSTRAINT_NAME`, source columns, `REFERENCED_TABLE_SCHEMA`, `REFERENCED_TABLE_NAME`, referenced columns, `UPDATE_RULE`, `DELETE_RULE`.
- Ordering: `ORDER BY tc.CONSTRAINT_NAME ASC, kcu.ORDINAL_POSITION ASC`.

### 6. Unique Constraints (`list_unique_constraints`)

Queries `INFORMATION_SCHEMA.TABLE_CONSTRAINTS` joined with `KEY_COLUMN_USAGE`:

- Excludes primary key constraints (`CONSTRAINT_TYPE = 'UNIQUE'`).
- Grouped by constraint name and ordered deterministically.

### 7. Check Constraints (`list_check_constraints`)

Queries `INFORMATION_SCHEMA.CHECK_CONSTRAINTS` (MySQL 8.0.16+):

- Extracts constraint name and boolean `CHECK_CLAUSE` expression text.
- Never evaluates or executes check expressions.

### 8. Index Inspection (`list_indexes`)

Queries `INFORMATION_SCHEMA.STATISTICS`:

- In MySQL 8.0+, includes `EXPRESSION` (for functional indexes) and `IS_VISIBLE`.
- Grouped by `INDEX_NAME` with columns ordered by `SEQ_IN_INDEX ASC`.

### 9. View Inspection (`list_views`)

Queries `INFORMATION_SCHEMA.VIEWS`:

- Extracts `VIEW_DEFINITION`, `CHECK_OPTION`, `IS_UPDATABLE`, `DEFINER`, and `SECURITY_TYPE`.
- Treated strictly as untrusted metadata text; views are never executed.

### 10. Trigger Inspection (`list_triggers`)

Queries `INFORMATION_SCHEMA.TRIGGERS`:

- Extracts `TRIGGER_NAME`, `ACTION_TIMING` (`BEFORE` / `AFTER`), `EVENT_MANIPULATION` (`INSERT` / `UPDATE` / `DELETE`), and `ACTION_STATEMENT`.
- Never executes trigger bodies.
