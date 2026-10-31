# ER Search & Filtering

**Document Reference**: `docs/frontend/ER_SEARCH_FILTERS.md`  
**Milestone**: Phase 7.4 — Interactive ER Diagram Canvas & Relationship Visualization  

---

## 1. Real-Time Search

The search input (`apps/web/src/components/er-diagram/GraphFilters.tsx`) deterministically filters tables and relationships in real time.

Matches are evaluated across:
1. **Table Name**: Case-insensitive substring match against `node.name`.
2. **Namespace**: Substring match against `node.namespace`.
3. **Column Name**: Match against any column in `node.columns`.
4. **Constraint Name**: Match against any connected foreign key constraint in `edges`.

---

## 2. Namespace Scoping

In multi-schema databases (such as PostgreSQL with `public`, `auth`, `sales`), users can scope the diagram canvas to a specific namespace or view cross-namespace relationships under `All Namespaces`.

When a namespace filter is active:
- Tables outside the selected namespace are culled from the canvas.
- Edges that cross namespace boundaries are hidden unless both tables belong to the active filter set.
- Filter readout displays: `"N of Total tables visible"`.

---

## 3. Isolated Tables Toggle

Schemas often contain lookup, logging, or standalone tables that have zero foreign key relationships. The **"Hide isolated tables"** checkbox toggles visibility of disconnected nodes, allowing engineers to focus exclusively on interconnected relationship topologies.
