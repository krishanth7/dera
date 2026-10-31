# DERA-CON-002: Foreign Key Referential Mapping Integrity

## 1. Specification
Rule `DERA-CON-002` evaluates the referential integrity of table foreign keys without executing database queries or touching customer data.

## 2. Integrity Validations
1. **Child Column Integrity**: Verifies all child referencing columns exist on the declaring table.
2. **Composite Mapping Cardinality**: Ensures the count of source columns exactly matches the count of referenced parent columns. Composite keys are evaluated as a single relational unit and never split into separate relationships.
3. **Parent Column Integrity**: When the target table is present in the schema snapshot, verifies that all referenced target columns exist in the target table.
4. **Unresolved Target Tables**: When a foreign key references a table outside the inspected schema (e.g. cross-database reference or uninspected catalog), reports `DiagnosticSeverity.LOW` with classification `INSPECTION_LIMITATION`, avoiding false positives.
5. **Self-Referencing Keys**: Correctly recognizes self-referencing foreign keys (e.g., `employees.manager_id -> employees.id`) without classifying them as invalid cycles.
