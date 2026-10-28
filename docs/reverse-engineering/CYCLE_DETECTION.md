# Phase 6.4 Cycle Detection & Classification

## 1. Overview

Relational database schemas frequently contain cycles in their foreign key relationships:
- **Self-referencing tables** (e.g., employee managers, hierarchical categories).
- **Mutual cycles** (e.g., Table A references Table B, and Table B references Table A).
- **Indirect cycles** (e.g., Table A $\to$ Table B $\to$ Table C $\to$ Table A).
- **Complex SCCs** (interlocking cycles sharing nodes and edges).

The DERA cycle detection subsystem enumerates all elementary cycles deterministically while providing strict circuit breakers to protect system resources.

---

## 2. Cycle Classification (`CycleKind`)

Each detected cycle is classified into one of four deterministic categories:

| CycleKind | Length | Description | Example |
| :--- | :--- | :--- | :--- |
| `SELF_REFERENCING` | 1 | A table has a foreign key referencing its own primary key or unique key. | `employees.manager_id -> employees.id` |
| `MUTUAL` | 2 | Two tables reference each other directly. | `orders.invoice_id -> invoices.id` and `invoices.order_id -> orders.id` |
| `INDIRECT` | $\ge 3$ | Three or more tables form a simple closed dependency path. | `A -> B -> C -> A` |
| `COMPLEX` | Multi-path | An SCC containing multiple overlapping cycles or cross-cycle edges. | A clique or figure-8 graph of tables. |

---

## 3. Canonical Cycle Representation

To ensure determinism and eliminate representation divergence:
1. Every cycle is represented as a tuple of table object IDs: $(v_0, v_1, \dots, v_{k-1})$.
2. The cycle is **canonically rotated** such that the minimum `ObjectId` string appears at index 0.
3. If two directions are possible, the lexicographically smaller second element is chosen.
4. Duplicate representations of the same underlying cycle are deduplicated.
5. All cycle instances in the `CycleReport` are sorted by `(length, nodes[0], nodes[1], ...)`.

---

## 4. Circuit Breakers & Resource Bounds

In dense or complete graphs, the number of elementary cycles grows asymptotically up to $O(e \cdot n!)$. To prevent exponential resource exhaustion:
- **`max_cycles`** (default: 1,000): Hard cap on the number of enumerated elementary cycles.
- When `found_cycles >= max_cycles`, the traversal stops immediately and sets `is_truncated = True`.
- `DependencyResourceLimits.max_recursion_depth` prevents stack overflow during deep DFS sweeps.
