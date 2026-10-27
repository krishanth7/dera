# Universal Metadata Contracts

## Relational Models

The metadata layer (`packages/connectors/src/dera_connectors/metadata.py`) standardizes relational objects across PostgreSQL, SQLite, MySQL, and MariaDB:

| Model | Key Fields | Description |
|---|---|---|
| `SchemaInfo` | `schema_name`, `comment` | Schema or database namespace |
| `TableInfo` | `schema_name`, `table_name`, `object_type`, `comment` | Relational table or partition |
| `ColumnInfo` | `schema_name`, `table_name`, `column_name`, `ordinal_position`, `data_type`, `is_nullable`, `default_expression` | Table column descriptor |
| `PrimaryKeyInfo` | `constraint_name`, `schema_name`, `table_name`, `column_names` | Primary key constraint |
| `ForeignKeyInfo` | `constraint_name`, `column_names`, `referenced_schema`, `referenced_table`, `referenced_columns`, `on_update`, `on_delete` | Referential foreign key relationship |
| `UniqueConstraintInfo` | `constraint_name`, `column_names` | Unique constraint |
| `CheckConstraintInfo` | `constraint_name`, `check_clause` | Check constraint expression |
| `IndexInfo` | `index_name`, `column_names`, `is_unique`, `index_type`, `predicate` | Secondary index metadata |
| `ViewInfo` | `view_name`, `is_materialized`, `view_definition` | View definition statement |

## Invariants

- **Default Expressions are Untrusted Text:** Default expressions and view definitions are stored as raw strings and never evaluated as executable code.
- **Identifier Spelling:** Case and quoting formatting from the original database are preserved.
- **Deterministic Ordering:** Results are deterministically sorted (e.g. columns by `ordinal_position`, tables by schema and name).
