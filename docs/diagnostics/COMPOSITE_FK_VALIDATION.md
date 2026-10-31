# DERA-REL-003: Composite Foreign Key Mapping Integrity

## 1. Rule Definition
- **Rule ID**: `DERA-REL-003`
- **Rule Title**: Composite Foreign Key Mapping Integrity
- **Category**: `RELATIONSHIPS`
- **Default Severity**: `HIGH`
- **Applicability**: Relational engines supporting composite foreign keys (PostgreSQL, SQLite, MySQL, MariaDB).

## 2. Rationale
Composite foreign keys link multi-column primary or unique keys between child and parent tables (e.g., `tenant_id, user_id`). To be valid and enforceable:
1. The number of source columns must exactly equal the number of referenced columns.
2. Every column mapping must have non-empty source and referenced column identifiers.
3. Ordinal positions must form a continuous 1-based sequence without gaps or duplicates.

A mismatch in column count or ordinal gaps prevents the database engine from enforcing the relational constraint and corrupts dependency analysis.

## 3. Evaluation Logic
1. Iterate over all `ForeignKeyEdge` models in the graph where `is_composite` is True or `len(column_pairs) > 1`.
2. Extract source column names and referenced column names.
3. Verify `len(source_columns) == len(referenced_columns)`.
4. Verify all column names are non-empty strings.
5. Verify ordinal positions are $[1, 2, \dots, N]$.
6. Emit `DiagnosticFinding` with severity `HIGH` if any condition is violated.
