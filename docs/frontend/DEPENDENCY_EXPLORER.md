# Dependency Explorer Architecture

**Module**: `apps/web/src/components/dependency-explorer/`  
**Route**: `/dependencies` (and `/app/dependencies`)  
**Phase**: 7.5 — Table Inspector, Advanced Search & Dependency Visualization  

---

## 1. Overview

The Dependency Explorer provides complete schema-wide and object-level structural dependency analysis. It visualizes execution orderings, transitive reachability blast radiuses, strongly connected components, and circular foreign key cycles computed by Phase 6.4 backend algorithms.

---

## 2. Explorer Sub-Views

1. **Reachability & Blast Radius** (`TransitiveReachabilityPanel.tsx`):
   - Computes upstream prerequisites (tables that must exist before the selected entity) and downstream blast radiuses (tables impacted if the entity is altered or dropped).
   - Traversal depth controls: 1 level, 2 levels, 3 levels, or Full Transitive reachability.
2. **Cycles & Strongly Connected Components** (`CycleAnalysisPanel.tsx`):
   - Displays elementary cycles discovered via Johnson's algorithm and SCC partitions from Tarjan's algorithm.
   - Shows breakability strategies (`DEFER_FOREIGN_KEY`, `NULLIFY_COLUMN`, `RESTRICT`).
3. **Topological Orderings** (`ExecutionOrderingPanel.tsx`):
   - Creation Order: Strict linear topological sequence.
   - Drop Order: Reverse topological safe teardown sequence.
   - Parallel Migration Levels: Concurrently executable migration batches.
4. **Accessible Table View** (`AccessibleDependencyTable.tsx`):
   - Full semantic HTML table representation for screen readers and keyboard users (100% WCAG 2.2 AA).
