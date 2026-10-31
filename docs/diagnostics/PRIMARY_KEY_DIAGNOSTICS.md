# DERA-CON-001: Primary Key Structural Integrity Diagnostics

## 1. Specification
Rule `DERA-CON-001` evaluates declared primary keys across canonical tables for structural consistency and validity.

## 2. Checks Enforced
1. **Empty Key Declarations**: Identifies primary keys declared with zero participating columns (`DiagnosticSeverity.HIGH`).
2. **Duplicate Key Columns**: Identifies composite primary keys containing repeated column entries (e.g. `PRIMARY KEY (tenant_id, tenant_id)`) (`DiagnosticSeverity.MEDIUM`).
3. **Column Reference Integrity**: Verifies that every column in the primary key exists in the table's canonical column list (`DiagnosticSeverity.HIGH`).

## 3. Preservation of Tables Without Primary Keys
Per prompt rule 38, DERA does NOT classify a table lacking a primary key as an error in Phase 8.2. Certain staging tables, logging tables, and read-only event buffers legitimately omit primary keys.
