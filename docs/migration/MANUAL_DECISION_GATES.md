# Phase 9.3 Manual Decision Gates & Preconditions

## Manual Decision Gates
Certain database schema modifications carry operational, locking, or data loss hazards that cannot be resolved safely without human engineering sign-off.
Phase 9.3 attaches explicit `ManualDecisionGate` instances to affected operations.

### Gate Categories
1. **`DATA_PRESERVATION`**:
   - Triggered on destructive operations (`DROP_TABLE`, `DROP_COLUMN`, `DROP_NAMESPACE`, `DROP_PRIMARY_KEY`).
   - Requires verification that tables or columns are backed up, archived, or snapshot-persisted before execution.
2. **`BACKFILL_STRATEGY` / `DATA_VALIDATION`**:
   - Triggered on constraint additions and narrowing column modifications (`ALTER_COLUMN_TYPE`, `ALTER_COLUMN_NULLABILITY`, `ADD_FOREIGN_KEY`, `ADD_UNIQUE_CONSTRAINT`, `ADD_PRIMARY_KEY`).
   - Requires pre-flight validation that existing table rows do not contain violations (e.g., null values in non-nullable column, duplicate keys, orphaned foreign keys).
3. **`ENGINE_SPECIFIC_TECHNIQUE`**:
   - Triggered when an operation is classified as `CONDITIONAL` on the target database engine (e.g., SQLite table rebuild, MySQL online DDL locking modes).

## Preconditions
Every abstract migration operation defines preconditions verified against canonical metadata prior to planning:
- `OBJECT_EXISTENCE`: Verifies that parent table/column exists before applying modification or drop.
- `OBJECT_ABSENCE`: Verifies that the target identifier does not already exist before creation.
- `DEPENDENCY_RESOLUTION`: Verifies that referenced parent tables/columns exist before constraint or view creation.
- `PERMISSION_VERIFICATION`: Verifies administrative permissions for namespace creation or drop.
- `DATA_VALIDATION_REQUIRED`: Flags required data verification queries.
