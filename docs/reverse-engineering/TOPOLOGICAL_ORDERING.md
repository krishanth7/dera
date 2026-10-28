# Phase 6.4 Topological Ordering & Condensation DAG

## 1. Overview

Topological ordering establishes the execution sequence for database DDL and DML operations:
- **Creation Order**: Tables must be created and populated in an order where dependencies precede dependents.
- **Drop Order**: Dependent child tables must be dropped before their referenced parent tables.

---

## 2. Kahn's Algorithm with Priority Queue

For Directed Acyclic Graphs (zero cycles), DERA implements Kahn's algorithm augmented with a priority queue (min-heap):
1. **In-Degree Computation**: Compute the in-degree of all nodes in the dependency graph. (Note: in-degree 0 in the dependency graph means the table has no dependencies — it is a root/parent table).
2. **Min-Heap Initialization**: Push all tables with in-degree 0 onto a min-heap ordered lexicographically by `ObjectId`.
3. **Deterministic Pop & Decrement**:
   - Pop the minimum table $u$.
   - Append $u$ to `creation_order`.
   - For all dependents $v$ of $u$, decrement $in\_degree[v]$.
   - If $in\_degree[v] == 0$, push $v$ onto the min-heap.
4. **Drop Order Generation**: The drop order is the exact reversal of the creation order (`creation_order[::-1]`).

---

## 3. Condensation DAG for Cyclic Schemas

When cycles exist, a global linear topological sort of individual tables is mathematically impossible. In this scenario:
1. Every SCC is collapsed into a single `CondensationNode` (supernode).
2. Single tables that do not participate in cycles form trivial supernodes of size 1.
3. Edges between tables in different SCCs become directed edges between supernodes.
4. The resulting condensation graph is guaranteed to be a Directed Acyclic Graph (Condensation DAG).
5. Kahn's algorithm is applied across the condensation supernodes to yield `condensation_topological_order`.
