# DERA-IDX-001: Exact Duplicate Index Definitions

## 1. Specification
Rule `DERA-IDX-001` detects structurally identical index definitions created on the same table. Exact equivalence requires identical access methods, key columns/expressions, sort directions (ASC/DESC), NULL ordering (NULLS FIRST/LAST), uniqueness enforcement, and partial index predicates.

## 2. Evaluation Logic
1. **Grouping**: Group indexes by parent table. Tables with fewer than 2 indexes are skipped in $O(1)$.
2. **Signature Comparison**: Compute canonical `CanonicalIndexSignature` SHA-256 hash.
3. **Equivalence Evaluation**:
   - Access Method: Both must match (e.g. `BTREE` == `BTREE`).
   - Terms: Exact ordinal match for every column or expression, including direction and nulls.
   - Predicate: Normalized whitespace and case comparison of `WHERE` clause.
   - Uniqueness: Must both be unique or both non-unique.
4. **Constraint Ownership Check**: Inspect whether either index backs a declared `PRIMARY KEY` or `UNIQUE` constraint. Constraint-owned indexes carry warnings against direct dropping.

## 3. Severity & Remediation
- **Severity**: `DiagnosticSeverity.MEDIUM`
- **Remediation**: Safely drop one duplicate index after verifying no application queries rely explicitly on index hints or specific index names.
