## Database Connector Summary

<!-- Describe the new database connector or dialect adapter implemented in packages/connectors. -->

## Target Engine & Version Coverage

- **Database Engine:** PostgreSQL | Supabase | SQLite | MySQL | MariaDB | SQL Server | Other
- **Tested Engine Versions:** (e.g., PostgreSQL 16.2, SQLite 3.45)
- **Driver / Client Library Used:** 

## Metadata Introspection Scope

<!-- Select all structural objects supported by this connector: -->
- [ ] Tables & Columns (Name, Data Type, Nullability, Default Value)
- [ ] Primary Keys & Unique Constraints
- [ ] Foreign Keys & Referential Actions (`CASCADE`, `SET NULL`, `RESTRICT`)
- [ ] Indexes (B-Tree, Multi-Column, Unique)
- [ ] Views & Materialized Views
- [ ] Schema Namespaces & Partitions

## Security & Read-Only Guarantees

- [ ] **Strict Read-Only Enforcement:** Connector queries system catalogs exclusively (`information_schema`, `pg_catalog`, `sqlite_master`).
- [ ] **Zero Table Data Extraction:** Verified that `SELECT *` is never executed against application data tables.
- [ ] **Static Mutation Guard:** AST inspection rejects mutating statements (`DROP`, `TRUNCATE`, `ALTER`, `INSERT`, `UPDATE`, `DELETE`).
- [ ] **Credential Protection:** Connection strings and passwords are never logged, stored in plaintext, or leaked in error messages.
- [ ] **No Committed Secrets:** Test fixtures use synthetic schemas and ephemeral in-memory or container databases.

## Testing Performed

- [ ] Unit tests for metadata normalization (`tests/unit/test_connectors_*.py`)
- [ ] Integration tests against local or containerized instance (`tests/integration/test_connector_*.py`)
- [ ] Full baseline suite passed (`python scripts/development/dev.py all`)
- [ ] PR title follows Conventional Commits: `feat(connectors): implement <engine> metadata adapter`
