# DERA-DEP-003: Dependency Concentration Analysis

## 1. Rule Definition
- **Rule ID**: `DERA-DEP-003`
- **Rule Title**: High Dependency Concentration (Fan-In Hubs & Fan-Out Consumers)
- **Category**: `DEPENDENCIES`
- **Default Severity**: `LOW` (escalated to `MEDIUM` at $2\times$ threshold)
- **Default Threshold**: 8 relationships (configurable via `DiagnosticEngineConfig.rule_thresholds["max_dependency_degree"]`).

## 2. Structural Patterns
Dependency concentration measures direct degree centrality in the relational graph:
1. **High Fan-In Hubs (`out_degree >= threshold`)**:
   - In DERA's convention (child $\to$ parent), a parent table referenced by many child tables has high *out-degree* from the child perspective, representing a centralized entity (e.g., `users`, `accounts`, `tenants`).
   - Structural risk: Modifications, lock contention, or schema alterations to this hub create contention across many distinct business services.
2. **High Fan-Out Consumers (`in_degree >= threshold`)**:
   - A child table referencing many parent tables has high *in-degree* (e.g., `audit_events`, `data_warehouse_facts`).
   - Structural risk: Inserting a row requires foreign key checks against numerous distinct parent tables, multiplying read lock overhead.

## 3. Evaluation
1. Evaluates `metrics.out_degree` (fan-in hub) and `metrics.in_degree` (fan-out consumer) for each table node.
2. Configurable via `max_dependency_degree`.
3. Records degree counts, direct relationship names, and mitigation guidance.
