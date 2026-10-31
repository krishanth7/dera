# DERA Phase 8.3 — Relationship & Dependency Evidence Model

## 1. Overview
In accordance with DERA's strict auditability principles, every diagnostic finding produced by Phase 8.3 relationship and dependency rules contains structured, reproducible `DiagnosticEvidence` objects.

## 2. Evidence Contract
```python
class DiagnosticEvidence(BaseModel):
    object_id: str
    field_name: str
    observed_value: Any
    expected_value: Any | None
    message: str
    context_data: dict[str, Any]
```

## 3. Evidence Payload by Rule
- `DERA-REL-001` (Graph Integrity): Records `field_name="missing_node_endpoint"`, observed target ID, and edge constraint name.
- `DERA-REL-002` (Unresolved Targets): Records `field_name="unresolved_relationship_target"`, categorized `reason`, and source/target table identifiers.
- `DERA-REL-003` (Composite FK Mappings): Records `field_name="column_pairs"`, column mapping counts, and ordinal sequence details.
- `DERA-REL-004` (Cross-Namespace): Records `field_name="cross_namespace_foreign_key"`, source namespace, and referenced namespace.
- `DERA-DEP-001` (Circular Dependencies): Records `field_name="scc_cycle_membership"`, SCC identifier, member tables, and elementary cycles.
- `DERA-DEP-002` (Dependency Depth): Records `field_name="depth_level"`, observed integer depth, and configured depth threshold.
- `DERA-DEP-003` (Dependency Concentration): Records `field_name="fan_in_out_degree"`, observed degree count, and configured degree threshold.
- `DERA-DEP-004` (Structural Impact): Records `field_name="transitive_dependents_count"`, transitive dependent count, direct dependents count, and impact threshold.
