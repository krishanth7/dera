# Phase 6.4 Dependency Analysis & Cycle Detection Overview

## 1. Executive Summary

Milestone 6.4 of the DERA Reverse Engineering Core Engine introduces the **Dependency Analysis & Cycle Detection Subsystem** (`dera.reverse_engineering.dependencies`), a strongly typed, deterministic, immutable dependency evaluation engine.

Building upon Phase 6.1 Canonical Schema Representation (`SchemaRepresentation`) and Phase 6.3 Foreign Key Relationship Graph (`ForeignKeyGraph`), the dependency analysis engine analyzes table dependency hierarchies, enumerates elementary cycles, computes strongly connected components (SCCs), evaluates cycle breakability strategies, determines deterministic creation/drop execution orderings via Kahn's algorithm and Condensation DAGs, and stratifies parallel migration levels.

```text
┌────────────────────────────────────────────────────────┐
│ Phase 6.1 Canonical Schema Representation              │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 6.3 Foreign Key Relationship Graph (Multigraph)  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 6.4 Dependency Analysis & Cycle Detection Engine │
│  - Tarjan Deterministic SCC Decomposition              │
│  - Johnson Bounded Elementary Cycle Enumeration        │
│  - Cycle Breakability & Remediation Classification     │
│  - Kahn's Topological Sort with Level Stratification   │
│  - Condensation DAG for Cyclic Schemas                 │
│  - Transitive Dependency Metrics (Roots, Leaves)       │
│  - Multi-severity Integrity Validation                 │
│  - RFC 8785 Canonical JSON & SHA-256 Fingerprinting    │
└────────────────────────────────────────────────────────┘
```

---

## 2. Core Tenets

1. **Strict Dependency Directionality**: A child table declaring a foreign key constraint to a parent table *depends on* that parent table. Therefore, parent tables must be created before child tables, and child tables must be dropped before parent tables.
2. **Deterministic Evaluation**: Identical schema inputs produce identical SCC orderings, cycle rotations, topological orderings, level stratifications, validation findings, and SHA-256 fingerprint hashes across all environments.
3. **Immutability & Type Safety**: Every data contract (`DependencyEdge`, `CycleInstance`, `StronglyConnectedComponent`, `DependencyOrdering`, `DependencyAnalysisResult`, etc.) is a frozen Pydantic v2 model with strict validation (`extra="forbid"`).
4. **Resilience & Bounded Complexity**: Configurable resource limits (`DependencyResourceLimits`) bound nodes, edges, cycle enumeration, recursion depth, levels, and serialized payload sizes to prevent Denial of Service on exponential cycle topologies.
5. **Zero Customer Mutation**: All dependency analysis is executed purely in-memory. Zero database mutations or queries are executed.
6. **Zero AI/ML Dependencies**: 100% deterministic graph theory algorithms (Tarjan's SCC, Johnson's cycle finder, Kahn's topological sort, transitive closures). AI and machine learning inference are strictly prohibited.

---

## 3. Package Structure

The Phase 6.4 implementation is housed under `packages/core/src/dera/reverse_engineering/dependencies/`:

| Module | Description |
| :--- | :--- |
| [`models.py`](file:///packages/core/src/dera/reverse_engineering/dependencies/models.py) | Pydantic v2 frozen models and enums (`DependencyKind`, `CycleKind`, `BreakabilityStrategy`, `CycleInstance`, `DependencyOrdering`, `DependencyAnalysisResult`). |
| [`errors.py`](file:///packages/core/src/dera/reverse_engineering/dependencies/errors.py) | Structured exception hierarchy (`DependencyAnalysisError`, `CyclicDependencyError`, `DependencyResourceLimitError`, `DependencyValidationError`). |
| [`limits.py`](file:///packages/core/src/dera/reverse_engineering/dependencies/limits.py) | Configurable resource limits (`DependencyResourceLimits`) enforcing algorithmic boundaries. |
| [`ordering.py`](file:///packages/core/src/dera/reverse_engineering/dependencies/ordering.py) | Deterministic canonical tie-breaking and sorting utilities for nodes, edges, cycles, SCCs, and findings. |
| [`analyzer.py`](file:///packages/core/src/dera/reverse_engineering/dependencies/analyzer.py) | Main `DependencyAnalyzer` orchestrator pipeline. |
| [`validation.py`](file:///packages/core/src/dera/reverse_engineering/dependencies/validation.py) | Deterministic multi-severity validation engine (`validate_dependency_analysis`). |
| [`serialization.py`](file:///packages/core/src/dera/reverse_engineering/dependencies/serialization.py) | RFC 8785 canonical JSON serializer, deserializer, and SHA-256 fingerprint hasher. |
| `algorithms/` | Specialized deterministic graph algorithm implementations. |
| [`algorithms/tarjan.py`](file:///packages/core/src/dera/reverse_engineering/dependencies/algorithms/tarjan.py) | Tarjan's Strongly Connected Components algorithm with stable tie-breaking. |
| [`algorithms/johnson.py`](file:///packages/core/src/dera/reverse_engineering/dependencies/algorithms/johnson.py) | Bounded elementary cycle enumeration and breakability analysis. |
| [`algorithms/topological_sort.py`](file:///packages/core/src/dera/reverse_engineering/dependencies/algorithms/topological_sort.py) | Kahn's algorithm with priority queue level stratification and Condensation DAG builder. |
| [`algorithms/metrics.py`](file:///packages/core/src/dera/reverse_engineering/dependencies/algorithms/metrics.py) | Transitive closure reachability, depth metrics, and root/leaf/isolated table identification. |
| [`algorithms/cycle_analysis.py`](file:///packages/core/src/dera/reverse_engineering/dependencies/algorithms/cycle_analysis.py) | Cycle report compilation and classification. |

---

## 4. Contract Hierarchy & Versioning

The root container is `DependencyAnalysisResult` (`contract_version = "6.4.0"`):

- **`schema_id`**: Identifier of the source `SchemaRepresentation`.
- **`graph_id`**: Identifier of the source `ForeignKeyGraph`.
- **`nodes`**: Tuple of canonical table object IDs analyzed.
- **`edges`**: Tuple of directed `DependencyEdge`s (`dependent_node_id` $\to$ `dependency_node_id`).
- **`cycle_report`**: Summary of cycle metrics, classified `CycleInstance`s, and `StronglyConnectedComponent`s.
- **`ordering`**: `DependencyOrdering` containing linear creation/drop orders, parallel migration levels, and Condensation DAG for cyclic graphs.
- **`metrics`**: Map of `table_id` to `DependencyNodeMetrics` (degrees, depths, ancestor/descendant counts, root/leaf status).
- **`validation_findings`**: Tuple of `DependencyValidationFinding`s (`ERROR`, `WARNING`, `INFO`).
- **`limits`**: `DependencyResourceLimits` applied during analysis.
