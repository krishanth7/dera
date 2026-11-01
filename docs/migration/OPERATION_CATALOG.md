# Phase 9.3 Operation Catalog

## Catalog Version: 1.0.0

The Operation Catalog defines supported abstract database migration operations, their prerequisite semantics, engine support state, and data validation requirements.

| Operation Type | Description | Preconditions | Engine Support (PG/Supabase/SQLite/MySQL/MariaDB) | Data Validation Required |
|---|---|---|---|---|
| `CREATE_NAMESPACE` | Create schema/namespace | `OBJECT_ABSENCE`, `PERMISSION_VERIFICATION` | Supported / Supported / Unsupported / Supported / Supported | No |
| `DROP_NAMESPACE` | Drop schema/namespace | `OBJECT_EXISTENCE`, `BACKUP_PRESERVATION_REVIEW` | Supported / Supported / Unsupported / Supported / Supported | No |
| `CREATE_TABLE` | Create table structure | `OBJECT_ABSENCE`, `DEPENDENCY_RESOLUTION` | Supported across all engines | No |
| `DROP_TABLE` | Drop table and data | `OBJECT_EXISTENCE`, `BACKUP_PRESERVATION_REVIEW` | Supported across all engines | No |
| `ADD_COLUMN` | Add column to table | `OBJECT_EXISTENCE` | Supported (Conditional on SQLite) | No |
| `DROP_COLUMN` | Drop column from table | `OBJECT_EXISTENCE`, `BACKUP_PRESERVATION_REVIEW` | Supported (Conditional on SQLite) | No |
| `ALTER_COLUMN_TYPE` | Alter column data type | `OBJECT_EXISTENCE`, `DATA_VALIDATION_REQUIRED` | Supported / Supported / Unsupported (SQLite requires rebuild) / Supported / Supported | **Yes** |
| `ALTER_COLUMN_NULLABILITY`| Alter nullability constraint | `OBJECT_EXISTENCE`, `DATA_VALIDATION_REQUIRED` | Supported / Supported / Unsupported (SQLite requires rebuild) / Supported / Supported | **Yes** |
| `ALTER_COLUMN_DEFAULT` | Alter default value | `OBJECT_EXISTENCE` | Supported / Supported / Unsupported (SQLite requires rebuild) / Supported / Supported | No |
| `ADD_PRIMARY_KEY` | Add primary key | `OBJECT_EXISTENCE`, `DATA_VALIDATION_REQUIRED` | Supported / Supported / Unsupported (SQLite requires rebuild) / Supported / Supported | **Yes** |
| `DROP_PRIMARY_KEY` | Drop primary key | `OBJECT_EXISTENCE`, `BACKUP_PRESERVATION_REVIEW` | Supported / Supported / Unsupported (SQLite requires rebuild) / Supported / Supported | No |
| `ADD_UNIQUE_CONSTRAINT` | Add unique constraint | `OBJECT_EXISTENCE`, `DATA_VALIDATION_REQUIRED` | Supported across all engines (SQLite via unique index) | **Yes** |
| `DROP_UNIQUE_CONSTRAINT` | Drop unique constraint | `OBJECT_EXISTENCE` | Supported across all engines | No |
| `ADD_FOREIGN_KEY` | Add foreign key constraint | `OBJECT_EXISTENCE`, `DATA_VALIDATION_REQUIRED`, `DEPENDENCY_RESOLUTION` | Supported / Supported / Unsupported (SQLite requires rebuild) / Supported / Supported | **Yes** |
| `DROP_FOREIGN_KEY` | Drop foreign key constraint | `OBJECT_EXISTENCE` | Supported / Supported / Unsupported (SQLite requires rebuild) / Supported / Supported | No |
| `ADD_CHECK_CONSTRAINT` | Add check constraint | `OBJECT_EXISTENCE`, `DATA_VALIDATION_REQUIRED` | Supported / Supported / Unsupported (SQLite requires rebuild) / Supported / Supported | **Yes** |
| `DROP_CHECK_CONSTRAINT` | Drop check constraint | `OBJECT_EXISTENCE` | Supported / Supported / Unsupported (SQLite requires rebuild) / Supported / Supported | No |
| `CREATE_INDEX` | Create index | `OBJECT_EXISTENCE`, `OBJECT_ABSENCE` | Supported across all engines | No |
| `DROP_INDEX` | Drop index | `OBJECT_EXISTENCE` | Supported across all engines | No |
| `MODIFY_INDEX` | Modify index definition | `OBJECT_EXISTENCE` | Conditional across all engines (Drop then Create) | No |
| `CREATE_VIEW` | Create view definition | `DEPENDENCY_RESOLUTION`, `OBJECT_ABSENCE` | Supported across all engines | No |
| `DROP_VIEW` | Drop view definition | `OBJECT_EXISTENCE` | Supported across all engines | No |
| `MODIFY_VIEW` | Modify/replace view | `OBJECT_EXISTENCE`, `DEPENDENCY_RESOLUTION` | Supported (Conditional on SQLite) | No |
