# Phase 6.4 Dependency Metrics & Structural Analysis

## 1. Overview

To support database architecture audits, performance tuning, and refactoring decisions, the dependency engine calculates rich structural metrics for every table in the schema (`DependencyNodeMetrics`).

---

## 2. Metric Definitions

| Metric | Field | Description | Architectural Significance |
| :--- | :--- | :--- | :--- |
| **In-Degree** | `in_degree` | Number of parent tables this table depends on (number of outgoing FK constraints). | Indicates table complexity and coupling to upstream entities. |
| **Out-Degree** | `out_degree` | Number of child tables that depend on this table (number of incoming FK constraints). | Indicates upstream centrality and cascade blast radius. |
| **Max Depth** | `depth` | Longest dependency path from any root table down to this table. | Migration generation level. |
| **Transitive Ancestors** | `ancestor_count` | Total count of all upstream tables this table directly or indirectly depends on. | Full upstream dependency tree size. |
| **Transitive Descendants** | `descendant_count`| Total count of all downstream tables directly or indirectly depending on this table. | Total downstream impact surface. |
| **Root Table** | `is_root` | `True` if `in_degree == 0` (no foreign keys to other tables). | Standalone reference or dimension table. |
| **Leaf Table** | `is_leaf` | `True` if `out_degree == 0` (no other tables reference this table). | End-consumer or event/audit table. |
| **Isolated Table** | `is_isolated`| `True` if `in_degree == 0` and `out_degree == 0`. | Completely decoupled table. |
