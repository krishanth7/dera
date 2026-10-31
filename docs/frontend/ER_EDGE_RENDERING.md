# ER Relationship Edge Rendering

**Document Reference**: `docs/frontend/ER_EDGE_RENDERING.md`  
**Milestone**: Phase 7.4 — Interactive ER Diagram Canvas & Relationship Visualization  

---

## 1. Directed Edge Semantics

Foreign key edges in DERA originate at the referencing child table and point to the referenced parent table (`source -> target`). Arrowheads indicate target direction.

```text
+----------------+                             +----------------+
|     orders     |------- cubic bezier ------->|   customers    |
| (child/source) |                             | (parent/target)|
+----------------+                             +----------------+
```

---

## 2. Path Geometry & Routing

1. **Horizontal Layering (`orientation === "LR"`)**:
   - Exit point: Right edge of source node `(x1 = source.x + source.width, y1 = source.y + height/2)`
   - Entry point: Left edge of target node `(x2 = target.x, y2 = target.y + height/2)`
   - Control points: Smooth S-curves at midpoint: `C ((x1+x2)/2, y1), ((x1+x2)/2, y2), (x2, y2)`
2. **Parallel Relationships**:
   - Multiple foreign keys connecting the same table pair are grouped.
   - Each edge receives an index `parallel_index` and total count `parallel_total`.
   - Control points are displaced perpendicularly by `(idx - (total-1)/2) * 28px` to prevent overlapping paths.
3. **Self-Referencing Foreign Keys**:
   - Edges where `source_table_id === target_table_id` loop on the right side of the table card:
     `M (x + width, y + 24) C (x + width + offset, y + 9), (x + width + offset, y + 65), (x + width, y + 50)`
4. **Hit Targets**:
   - An invisible path with `strokeWidth={18}` surrounds each edge to guarantee effortless mouse picking and pointer interactions.

---

## 3. Visual States

- **Default**: `#64748b` (slate-500), 1.5px stroke, default arrowhead marker.
- **Highlighted**: `#06b6d4` (cyan-500), 2.5px stroke, cyan arrowhead marker.
- **Selected**: `#3b82f6` (blue-500), 3px stroke, blue arrowhead marker.
- **Composite**: Dashed stroke (`strokeDasharray="5,3"`) with pill badge showing `[N cols]`.
