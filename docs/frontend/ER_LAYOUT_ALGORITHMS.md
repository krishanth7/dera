# Deterministic ER Layout Algorithms

**Document Reference**: `docs/frontend/ER_LAYOUT_ALGORITHMS.md`  
**Milestone**: Phase 7.4 — Interactive ER Diagram Canvas & Relationship Visualization  

---

## 1. Algorithm Overview

DERA uses a **deterministic layered topological ranking layout** (`apps/web/src/components/er-diagram/layout.ts`).

Unlike force-directed simulation algorithms which introduce random particle jitter and non-reproducible coordinates, DERA's layout guarantees that:
$$\text{Identical Schema Input} \implies \text{Identical Node Coordinates}$$

---

## 2. Execution Phases

### Phase 1: Canonical Ordering

Raw nodes and edges are sorted deterministically before any graph traversal begins:
- Nodes: sorted by `(namespace, name, table_id)`
- Edges: sorted by `(source_table_id, target_table_id, constraint_name, edge_id)`

### Phase 2: Cycle-Safe Topological Ranking

1. Disregard self-loops during rank computation.
2. Build directed adjacency graph from referencing tables to referenced tables (`source -> target`).
3. Compute in-degrees across all nodes.
4. Nodes with in-degree 0 are assigned to `rank 0`.
5. Traverse neighbors using longest-path BFS:
   $$\text{rank}(v) = \max(\text{rank}(v), \text{rank}(u) + 1)$$
6. In cyclic graphs (mutual foreign keys or cycles), unranked nodes are deterministically assigned based on canonical ID precedence without infinite loops.

### Phase 3: Rank Sorting & Coordinate Assignment

1. Nodes are grouped into rank buckets.
2. Nodes within each rank are sorted canonically by `(namespace, name, id)`.
3. Coordinates are assigned:
   - **Horizontal (`LR`)**:
     $$x = \text{CANVAS\_PADDING} + \text{rank} \times (\text{NODE\_WIDTH} + \text{rankSeparation})$$
     $$y = \text{CANVAS\_PADDING} + \sum (\text{node.height} + \text{nodeSeparation})$$
   - **Vertical (`TB`)**:
     $$y = \text{CANVAS\_PADDING} + \text{rank} \times (\text{maxRankHeight} + \text{rankSeparation})$$
     $$x = \text{CANVAS\_PADDING} + \sum (\text{node.width} + \text{nodeSeparation})$$
