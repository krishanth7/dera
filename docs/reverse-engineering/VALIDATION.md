# Referential Integrity & Structural Validation (Phase 6.1)

## 1. Overview

`validate_schema_representation` enforces structural consistency and referential integrity across all objects in a `SchemaRepresentation`. It executes during schema construction and can be invoked on demand.

```python
from dera.reverse_engineering.validation import validate_schema_representation
```

---

## 2. Integrity Rules Checked

| Check Category | Verification Performed | Strict Failure Mode |
|---|---|---|
| **Database Root** | Validates `id` format begins with `dera:database:`. | `SchemaValidationError` |
| **Namespace Ownership** | Every namespace in database is registered in `ObjectRegistry`. | `SchemaValidationError` |
| **Table Parent Namespace** | Every table's `namespace_id` matches its containing namespace. | `MissingParentError` |
| **Column Parent Table** | Every column's `parent_table_id` matches its containing table. | `MissingParentError` |
| **Ordinal Integrity** | Detects duplicate ordinal positions within the same table. | Diagnostic issue |
| **Constraint Columns** | All columns participating in PK/UNIQUE/CHECK exist on table. | `SchemaValidationError` |
| **Index Columns** | Non-expression index terms refer to declared table columns. | `SchemaValidationError` |
| **Trigger Parent** | Trigger's `parent_table_id` references a registered table. | `MissingParentError` |
| **Foreign Key Source** | Foreign key source table exists; referencing columns exist. | `MissingParentError` / `SchemaValidationError` |
| **Foreign Key Target** | If resolved, target table exists; referenced columns exist. | `SchemaValidationError` |

---

## 3. Strict vs Lenient Modes

```python
# Lenient mode: collects all diagnostic issues without raising exceptions
issues = validate_schema_representation(schema, strict=False)
if len(issues) > 0:
    print(f"Validation warnings found: {issues}")

# Strict mode: raises MissingParentError or SchemaValidationError on first violation
validate_schema_representation(schema, strict=True)

# Strict foreign keys mode: requires all FK target tables to be resolved in registry
validate_schema_representation(schema, strict=True, strict_foreign_keys=True)
```
