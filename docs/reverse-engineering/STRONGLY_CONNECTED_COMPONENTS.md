# Phase 6.4 Strongly Connected Components (Tarjan's Algorithm)

## 1. Overview

A Strongly Connected Component (SCC) is a maximal subgraph where every table node in the component is reachable from every other table node in the component.

Tarjan's algorithm runs in $O(|V| + |E|)$ time and provides the mathematical foundation for:
1. Detecting whether a schema is an acyclic DAG or contains cycles.
2. Grouping cyclic dependencies into isolated components.
3. Constructing the Condensation DAG (supernode graph) for cyclic schemas.

---

## 2. Deterministic Implementation

Standard Tarjan implementations depend on dictionary or set iteration orders, leading to non-deterministic node sequences across different runs or Python processes.

DERA guarantees determinism by:
1. **Sorted Initial Traversal**: Nodes are visited in canonical sorted order of their string `ObjectId`.
2. **Sorted Edge Traversal**: Adjacency lists are sorted lexicographically before processing outgoing edges.
3. **Canonical Component ID**: Each SCC is assigned a deterministic ID based on its member nodes:
   `scc-` followed by the first 12 characters of each member `ObjectId` joined by underscores.
4. **Stable SCC Sorting**: The tuple of computed SCCs is sorted by:
   - Size (descending)
   - Minimum member `ObjectId` (ascending)
5. **Self-Loop Handling**: Single-node SCCs with self-referencing foreign keys are correctly flagged as cyclic (`is_trivial=False`).
