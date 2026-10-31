# DERA Phase 8.3 — Relationship & Dependency Security & Safety Controls

## 1. Zero Mutation Guarantee
All Phase 8.3 diagnostic rules evaluate exclusively against read-only canonical metadata, `ForeignKeyGraph` models, and immutable snapshots. Under no circumstances does the engine issue DDL statements, create temporary database tables, or execute mutations against customer databases.

## 2. Multi-Tenant Workspace Isolation
- Graph models carry `workspace_id` and `database_id` identifiers.
- Diagnostics are executed in workspace-scoped contexts; cross-workspace foreign key references (such as `UnresolvedReason.CROSS_WORKSPACE_REFERENCE`) are quarantined and audited without leaking metadata across tenants.

## 3. Algorithmic Resource Bounding
- **DFS / Traversal Limits**: Bounded depth (`max_depth = 10`) prevents stack overflow and infinite recursion on cyclic or dense multigraphs.
- **Node Visited Ceilings**: Reverse reachability exploration bounds discovered nodes at `max_nodes = 1000`.
- **Finding Ceilings**: Evaluations terminate findings generation once `max_findings` is reached.

## 4. Error Isolation
Each rule execution is isolated. An unexpected runtime error in one relationship rule emits an `EvaluationStatus.EVALUATION_ERROR` record for that specific rule without terminating or corrupting the evaluation of other rules.
