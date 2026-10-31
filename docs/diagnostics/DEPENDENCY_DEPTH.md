# DERA-DEP-002: Dependency Depth Analysis

## 1. Rule Definition
- **Rule ID**: `DERA-DEP-002`
- **Rule Title**: Deep Dependency Chains
- **Category**: `DEPENDENCIES`
- **Default Severity**: `LOW` (escalated to `MEDIUM` at $2\times$ threshold)
- **Default Threshold**: 5 levels (configurable via `DiagnosticEngineConfig.rule_thresholds["max_dependency_depth"]`).

## 2. Engineering Context
Dependency depth measures the longest chain of direct foreign key references leading from a root table to the target table:
$$T_k \to T_{k-1} \to \dots \to T_1 \to T_{\text{root}}$$
Deep foreign key chains create operational challenges:
- **Cascade Overhead**: An update or delete on the root cascades through multiple levels of dependent tables, locking tables across transactions.
- **Join Complexity**: Queries fetching entity aggregates often require cascading multi-table joins matching the foreign key depth.
- **Migration Latency**: Initial data loads and schema seeding require serialized staging across all layers.

## 3. Evaluation & Bounded Traversal
1. Node depth levels are retrieved from the precomputed Phase 6.4 `DependencyAnalysisResult.node_metrics`.
2. For acyclic graphs and condensation DAGs, `depth_level` represents the longest path from any root node.
3. If a table's `depth_level` $\ge$ threshold, a finding is emitted detailing the exact path depth, threshold, and cascade implications.
