# ER Diagram Architecture

**Document Reference**: `docs/frontend/ER_DIAGRAM_ARCHITECTURE.md`  
**Milestone**: Phase 7.4 — Interactive ER Diagram Canvas & Relationship Visualization  
**Audience**: Database Engineers, Frontend Architects, DevSecOps  

---

## 1. Architectural Mission

The DERA Interactive Entity-Relationship (ER) diagram canvas provides visual exploration of verified database schemas and multi-table foreign key multigraphs. It consumes verified metadata reconstructed by the Phase 6.3 engine and served via Phase 6.6 REST endpoints.

```text
+-------------------------------------------------------------+
|                     DERA Web Studio                         |
|  (/relationships?schemaId={id})                             |
+------------------------------+------------------------------+
                               |
                               v
            +------------------------------------+
            |       ERCanvas Studio Host         |
            +-----------------+------------------+
                              |
       +----------------------+----------------------+
       |                      |                      |
       v                      v                      v
+--------------+       +--------------+       +--------------+
|  ERToolbar   |       | GraphFilters |       | GraphStatus  |
+--------------+       +--------------+       +--------------+
       |                      |                      |
       +----------------------+----------------------+
                              |
       +----------------------+----------------------+
       |                                             |
       v                                             v
+-------------------------------+             +-------------------------------+
|       Visual Canvas           |             |   Accessible Table View       |
|  - TableNode SVG cards        |             |  - Semantic HTML tables       |
|  - RelationshipEdge curves    |             |  - Screen-reader navigation   |
|  - Dual-layer composition     |             |  - 100% WCAG 2.2 AA           |
+---------------+---------------+             +---------------+---------------+
                |                                             |
                +----------------------+----------------------+
                                       |
                                       v
                        +-------------------------------+
                        |     RelationshipDetails       |
                        |  - Constraint metadata        |
                        |  - Column pair mapping        |
                        |  - Referential actions        |
                        +-------------------------------+
```

---

## 2. Core Subsystems

1. **Graph Adapters (`layout.ts`)**: Transforms raw backend payloads into typed `CanvasNode` and `CanvasEdge` structures.
2. **Deterministic Layout Engine (`layout.ts`)**: Applies a force-free, cycle-aware, layered topological algorithm ensuring identical layout coordinates for identical schemas.
3. **Interactive Viewport Layer (`ERCanvas.tsx`)**: Pure SVG engine with coordinate translation, zooming, and node dragging.
4. **Table Node Presentation (`TableNode.tsx`)**: SVG card with namespace, table name, column list, PK markers, and FK indicators.
5. **Relationship Edges (`RelationshipEdge.tsx`)**: Directed cubic bezier curves, parallel edge offsets, composite pill badges, and self-loop arcs.
6. **Accessible Alternative (`AccessibleGraphTable.tsx`)**: Semantic HTML table allowing non-visual navigation of foreign key constraints and tables.
7. **Inspector Drawer (`RelationshipDetails.tsx`)**: Side drawer displaying complete constraint definitions, ordered column pairs, and actions.
