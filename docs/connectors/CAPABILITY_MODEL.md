# Connector Capability Model

## Capability Taxonomy

The capability model (`packages/connectors/src/dera_connectors/capabilities.py`) provides fine-grained, typed discovery of metadata inspection features supported by a given database engine and credential set:

```python
class ConnectorCapability(StrEnum):
    SCHEMA_ENUMERATION = "schema_enumeration"
    TABLE_ENUMERATION = "table_enumeration"
    COLUMN_INSPECTION = "column_inspection"
    PRIMARY_KEY_INSPECTION = "primary_key_inspection"
    FOREIGN_KEY_INSPECTION = "foreign_key_inspection"
    UNIQUE_CONSTRAINT_INSPECTION = "unique_constraint_inspection"
    CHECK_CONSTRAINT_INSPECTION = "check_constraint_inspection"
    INDEX_INSPECTION = "index_inspection"
    VIEW_INSPECTION = "view_inspection"
    MATERIALIZED_VIEW_INSPECTION = "materialized_view_inspection"
    TRIGGER_INSPECTION = "trigger_inspection"
    SEQUENCE_INSPECTION = "sequence_inspection"
    FUNCTION_INSPECTION = "function_inspection"
    PROCEDURE_INSPECTION = "procedure_inspection"
    COMMENT_INSPECTION = "comment_inspection"
    PARTITION_INSPECTION = "partition_inspection"
    DEPENDENCY_INSPECTION = "dependency_inspection"
```

## Status Values

1. **`SUPPORTED`**: The engine, driver, and current credentials fully support this capability.
2. **`UNSUPPORTED`**: The database dialect or driver does not support this feature (e.g. `MATERIALIZED_VIEW_INSPECTION` on SQLite).
3. **`RESTRICTED`**: The engine supports this feature, but the current user role or credentials lack sufficient permissions (e.g. missing `pg_read_all_settings`).
4. **`UNKNOWN`**: Capability availability has not yet been probed.
