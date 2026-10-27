# PostgreSQL Connector Capability Matrix

## Supported Capabilities

The PostgreSQL connector reports support across the DERA Phase 5 capability taxonomy:

| Capability | Status | Implementation Details |
|---|---|---|
| `SCHEMA_ENUMERATION` | **SUPPORTED** | User and application namespaces in `pg_namespace`. |
| `TABLE_ENUMERATION` | **SUPPORTED** | Ordinary (`r`), partitioned (`p`), and foreign (`f`) tables. |
| `COLUMN_INSPECTION` | **SUPPORTED** | Native types, nullability, default expressions, identity, generated columns. |
| `PRIMARY_KEY_INSPECTION` | **SUPPORTED** | Single and composite primary key constraints with key ordering. |
| `FOREIGN_KEY_INSPECTION` | **SUPPORTED** | Multi-column foreign keys, deferrability, referential cascade actions. |
| `UNIQUE_CONSTRAINT_INSPECTION` | **SUPPORTED** | Unique constraints differentiated from secondary unique indexes. |
| `CHECK_CONSTRAINT_INSPECTION` | **SUPPORTED** | Check expressions safely extracted as untrusted text. |
| `INDEX_INSPECTION` | **SUPPORTED** | BTREE, HASH, GIN, GIST, BRIN, partial indexes, expression indexes. |
| `VIEW_INSPECTION` | **SUPPORTED** | Standard view definitions via `pg_get_viewdef`. |
| `MATERIALIZED_VIEW_INSPECTION` | **SUPPORTED** | Materialized views differentiated from regular views. |
| `SEQUENCE_INSPECTION` | **SUPPORTED** | Start, min, max, increment, and cycling flags from `pg_sequence`. |
| `PARTITION_INSPECTION` | **SUPPORTED** | RANGE, LIST, and HASH partition hierarchies and bound expressions. |
| `COMMENT_INSPECTION` | **SUPPORTED** | Documentation comments from `pg_description`. |
| `TRIGGER_INSPECTION` | **SUPPORTED** | Event trigger definitions without executing function bodies. |
| `FUNCTION_INSPECTION` | **RESTRICTED** | Deferred to Phase 5.5 to avoid arbitrary procedural code analysis. |
| `PROCEDURE_INSPECTION` | **RESTRICTED** | Deferred to Phase 5.5. |
| `DEPENDENCY_INSPECTION` | **UNSUPPORTED** | Reserved for Phase 6 reverse-engineering dependency graph engine. |
