# PostgreSQL System Catalog Inspection Engine

## Catalog Tables Queried

The connector targets PostgreSQL system catalogs (`pg_catalog`) to extract structural metadata without performing table scans:

| Metadata Type | Source Catalogs | Primary Columns & Joins |
|---|---|---|
| **Identity** | `version()`, `current_setting('server_version_num')`, `current_database()` | Full version string, major/minor version number, active database. |
| **Schemas** | `pg_namespace`, `pg_description` | `nspname`, schema documentation comments. Excludes `pg_toast*` and `pg_temp*`. |
| **Tables** | `pg_class`, `pg_namespace`, `pg_description` | `c.relkind IN ('r', 'p', 'f')`, unlogged status, partition status, comments. |
| **Columns** | `pg_attribute`, `pg_class`, `pg_namespace`, `pg_attrdef`, `pg_description`, `pg_collation` | Ordinal position, native datatype via `format_type()`, NOT NULL, default expressions via `pg_get_expr()`, `attidentity`, `attgenerated`, collation. |
| **Primary Keys** | `pg_constraint`, `pg_class`, `pg_namespace`, `pg_attribute` | `con.contype = 'p'`, column array ordered by `unnest(con.conkey) WITH ORDINALITY`. |
| **Foreign Keys** | `pg_constraint`, referencing & referenced `pg_class` and `pg_namespace` | `con.contype = 'f'`, referencing and referenced column arrays, `confupdtype`, `confdeltype`. |
| **Unique Constraints** | `pg_constraint`, `pg_class`, `pg_namespace` | `con.contype = 'u'`, constraint name, column names array. |
| **Check Constraints** | `pg_constraint`, `pg_class`, `pg_namespace` | `con.contype = 'c'`, check condition clause via `pg_get_constraintdef()`. |
| **Indexes** | `pg_index`, `pg_class`, `pg_am`, `pg_namespace` | Index name, uniqueness, primary backing flag, access method (`am.amname`: BTREE, GIN, GIST, BRIN, HASH), partial filter predicate via `pg_get_expr()`, column list via `pg_get_indexdef()`. |
| **Views & Matviews** | `pg_class`, `pg_namespace`, `pg_description` | `c.relkind IN ('v', 'm')`, view definition SQL text via `pg_get_viewdef()`, comments. |
| **Sequences** | `pg_sequence`, `pg_class`, `pg_namespace`, `pg_description` | Sequence name, data type via `format_type()`, start value, min, max, increment, cycling flag. |
| **Partitions** | `pg_partitioned_table`, `pg_inherits`, `pg_class`, `pg_namespace` | Partition strategy (`RANGE`, `LIST`, `HASH`), partition key columns, partition bound expression via `pg_get_expr(relpartbound)`. |

---

## Safe Expression Handling

Check constraint clauses and default expressions retrieved from PostgreSQL catalogs are treated as untrusted metadata text. They are never parsed with `eval()`, never executed, and never passed directly into DDL without sanitization.
