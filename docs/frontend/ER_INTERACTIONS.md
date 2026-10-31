# ER Diagram Interactions & Controls

**Document Reference**: `docs/frontend/ER_INTERACTIONS.md`  
**Milestone**: Phase 7.4 — Interactive ER Diagram Canvas & Relationship Visualization  

---

## 1. Interaction Primitives

| Action | Pointer Interaction | Keyboard Shortcut | Toolbar Button |
| :--- | :--- | :--- | :--- |
| **Pan Canvas** | Click & drag on background | N/A | Mouse drag |
| **Zoom In** | Mouse wheel forward | `+` or `=` | Zoom In button |
| **Zoom Out** | Mouse wheel backward | `-` or `_` | Zoom Out button |
| **Fit to View** | N/A | `f` or `F` | Maximize icon |
| **Reset View** | N/A | `r` or `R` | Reset icon |
| **Auto-Layout** | N/A | N/A | "Auto-Layout" button |
| **Select Node** | Click table card | `Enter` / `Space` on focus | Table card |
| **Select Edge** | Click relationship curve | `Enter` / `Space` on focus | Curve / Badge |
| **Deselect All** | Click background | `Escape` | Background |
| **Move Table** | Click & drag table card | N/A | Card header |

---

## 2. Selection & Highlighting Logic

- **Node Selection**:
  - Highlights selected node with a vibrant blue glow.
  - Highlights all direct incoming foreign key edges (tables referencing this node) in cyan.
  - Highlights all direct outgoing foreign key edges (tables referenced by this node) in cyan.
  - Highlights connected neighboring tables in cyan.
  - Opens `RelationshipDetails` panel with entity summary and relationship listings.
- **Edge Selection**:
  - Highlights selected edge with blue 3px stroke and blue arrowhead.
  - Highlights source (child) and target (parent) tables in blue/cyan.
  - Opens `RelationshipDetails` panel with foreign key constraint name, column pairs, and referential actions (`ON UPDATE`, `ON DELETE`).

---

## 3. Manual Positioning

Users can freely reposition table cards on the canvas by dragging. Manual coordinates are managed in frontend session state and do not mutate database schema definitions. Users can restore deterministic auto-layout at any time via the "Auto-Layout" toolbar control.
