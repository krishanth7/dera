# DERA-DEP-004: Structural Change Impact Radius

## 1. Rule Definition
- **Rule ID**: `DERA-DEP-004`
- **Rule Title**: Structural Change Impact Radius (Blast Radius)
- **Category**: `DEPENDENCIES`
- **Default Severity**: `LOW` (escalated to `MEDIUM` at $2\times$ threshold)
- **Default Threshold**: 10 transitive dependents (configurable via `DiagnosticEngineConfig.rule_thresholds["max_impact_radius"]`).

## 2. Concept of Reverse Reachability
When a database engineer modifies or refactors a parent table (e.g. renaming a primary key, dropping a column, or migrating to UUIDs), all downstream child tables that transitively reference that parent table constitute the structural blast radius:
- **Direct Dependents**: Child tables with direct foreign keys to the target parent.
- **Transitive Dependents**: Children of children reachable by traversing foreign keys in reverse direction (Parent $\to$ referencing Child).

## 3. Evaluation & Guardrails
- **Direction**: Reverse traversal along incoming edges (incoming to parent).
- **Resource Limits**: Depth capped at `max_depth` (default 10); visited node set bounded at `max_nodes` (default 1000) to prevent unbounded memory consumption.
- **Explainable Findings**: Identifies exact downstream table counts, direct dependent counts, and migration review recommendations.
