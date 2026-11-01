# DERA-REL-001: Relationship Graph Structural Integrity

## 1. Rule Definition
- **Rule ID**: `DERA-REL-001`
- **Rule Title**: Relationship Graph Structural Integrity
- **Category**: `RELATIONSHIPS`
- **Default Severity**: `HIGH`
- **Applicability**: All relational database engines supporting foreign keys.

## 2. Rationale
A `ForeignKeyGraph` model must maintain strict internal structural integrity:
1. Every directed edge must reference an existing source table node.
2. Every directed edge must reference an existing target table node (unless explicitly categorized as unresolved).
3. Every edge must define at least one non-empty column pair mapping.

When an edge references a missing node or contains empty column pairs, it indicates internal graph corruption, schema reconstruction failure, or missing canonical table metadata.

## 3. Evaluation Logic
1. Resolve canonical `ForeignKeyGraph` via `DiagnosticContext`.
2. Map all valid table nodes by `object_id`.
3. For each `ForeignKeyEdge`:
   - Verify `edge.source_table_id` is present in the table node map.
   - Verify `edge.referenced_table_id` is present in the table node map.
   - Verify `len(edge.column_pairs) > 0`.
   - Verify `all(p.source_column_name and p.referenced_column_name for p in edge.column_pairs)`.
4. Emit `DiagnosticFinding` with severity `HIGH` for any defect detected.

## 4. Evidence Structure
- `object_id`: Canonical edge identifier.
- `field_name`: `source_table_id`, `referenced_table_id`, or `column_pairs`.
- `observed_value`: Missing node ID or empty column mappings.
- `expected_value`: Canonical table node reference and non-empty column pair tuples.
