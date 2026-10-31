# DERA-REL-002: Unresolved Foreign Key Relationship Target

## 1. Rule Definition
- **Rule ID**: `DERA-REL-002`
- **Rule Title**: Unresolved Foreign Key Relationship Target
- **Category**: `RELATIONSHIPS`
- **Default Severity**: `HIGH` (downgraded to `LOW` for catalog permission boundaries)
- **Applicability**: All relational database engines supporting foreign keys.

## 2. Rationale
Foreign key constraints declared in catalog metadata may point to tables that cannot be resolved in the inspected canonical schema. This occurs due to:
1. **Catalog Permissions**: The inspecting user does not have `SELECT`/metadata permissions on the target schema (e.g. `audit`, `security`).
2. **Partial Inspection Scope**: The caller restricted inspection to a subset of namespaces or tables.
3. **Broken Constraints / Dropped Tables**: Cross-table dependencies left dangling after manual table drops with disabled referential integrity.
4. **Unsupported Capabilities**: External database foreign keys or cross-instance links.

## 3. Provenance & Severity Nuance
Rather than assuming all unresolved targets are broken database constraints, `DERA-REL-002` categorizes by `UnresolvedReason`:
- `METADATA_RESTRICTED` or `METADATA_INCOMPLETE` or `UNSUPPORTED_CAPABILITY`:
  - Assigned severity `LOW`.
  - Rationale: Target entity omitted due to partial scope or catalog permission boundaries.
- `REFERENCED_TABLE_NOT_FOUND` or `REFERENCED_COLUMN_NOT_FOUND`:
  - Assigned severity `HIGH`.
  - Rationale: Declared foreign key target is missing from the canonical schema within inspected scope.
- `INVALID_METADATA`:
  - Assigned severity `HIGH`.
  - Rationale: Foreign key mapping metadata is structurally contradictory.

## 4. Evidence Structure
- `object_id`: Unresolved reference ID or declared foreign key ID.
- `field_name`: `unresolved_relationship_target`.
- `context_data`: Contains `source_table`, `referenced_table`, `reason`, `details`, and `declared_source_columns`.
