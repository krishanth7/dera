# Phase 6.4 Parallel Migration Levels (Generation Stratification)

## 1. Overview

While a linear creation order specifies a valid sequential execution path, modern migration engines and database restoration workers execute tasks concurrently.

The DERA dependency analyzer groups independent tables into deterministic **topological levels** (`parallel_levels`):
- All tables within a given level have zero intra-level dependencies.
- All dependencies of tables in level $k$ reside strictly in levels $0, 1, \dots, k-1$.
- Consequently, all tables in level $k$ can be migrated, created, or populated in parallel without race conditions or foreign key constraint violations.

---

## 2. Level Assignment Algorithm

1. **Level 0 (Root Tables)**: All tables with in-degree 0 in the dependency graph (tables with no outgoing foreign keys).
2. **Successive Levels ($k > 0$)**:
   $$\text{level}(v) = 1 + \max_{(u, v) \in E} \text{level}(u)$$
3. **Sorted Members**: Within each `TopologicalLevel`, table object IDs are sorted lexicographically to guarantee determinism.
4. **Validation**: The union of all table IDs across all levels must equal the set of all schema tables, with zero duplicates.
