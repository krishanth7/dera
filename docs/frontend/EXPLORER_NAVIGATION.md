# Explorer Navigation Specification

**Document Reference**: `docs/frontend/EXPLORER_NAVIGATION.md`  
**Milestone**: Phase 7.3 — Database Connection & Schema Explorer UI  

---

## 1. Tree View Hierarchy

The Schema Explorer navigation pane presents database assets in a strict hierarchical structure:

1. **Database / Schema Root**: Displays schema name, database engine badge, and metadata completeness indicator.
2. **Namespace Nodes**: Represent database schemas/namespaces (e.g., `public`, `auth`, `analytics`).
3. **Table & View Leaves**: Represent distinct database relation objects with badge indicators for views versus tables.

```text
Database Schema Root
  │
  ├── [Namespace: public] (Collapsible)
  │     ├── [Table: accounts] (PK: 1, FK: 0)
  │     ├── [Table: profiles] (PK: 1, FK: 1)
  │     └── [View: active_users] (VIEW)
  │
  └── [Namespace: audit] (Collapsible)
        └── [Table: logs] (PK: 1, FK: 0)
```

---

## 2. Selection & State Management

- **Stable Selection**: Clicking an object node updates the URL and internal state without reloading the navigation tree.
- **Root Overview Return**: Clicking the "Schema Overview" button returns the detail panel to top-level aggregate metrics.
- **Tree Expansion Memory**: Collapsed and expanded namespace states are tracked in local state to maintain context across table selections.
- **Responsive Drawer**: On mobile and tablet screens, the navigation pane collapses into a slide-out drawer accessible via the menu toggle.
