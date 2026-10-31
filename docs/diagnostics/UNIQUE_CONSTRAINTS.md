# DERA-CON-003: Unique Constraint Structural Integrity

## 1. Specification
Rule `DERA-CON-003` audits table unique constraints for completeness, duplicate declarations, and redundancy with primary keys.

## 2. Evaluation Rules
1. **Empty Unique Constraints**: Identifies constraints defining zero columns (`DiagnosticSeverity.HIGH`).
2. **Primary Key Duplication**: Detects explicit unique constraints that cover the exact column set of the table's declared primary key (`DiagnosticSeverity.LOW`).
3. **Pairwise Duplicate Constraints**: Detects multiple unique constraints defined on the same table with identical column lists (`DiagnosticSeverity.MEDIUM`).
4. **Preservation of Unique Indexes vs Unique Constraints**: DERA treats explicit `UNIQUE` constraints and unique secondary indexes as distinct schema entities, preserving constraint names, ownership, and deferrability.
