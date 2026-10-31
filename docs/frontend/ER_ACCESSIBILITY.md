# ER Diagram Accessibility (WCAG 2.2 AA)

**Document Reference**: `docs/frontend/ER_ACCESSIBILITY.md`  
**Milestone**: Phase 7.4 — Interactive ER Diagram Canvas & Relationship Visualization  

---

## 1. Dual-View Architecture

Graphical canvas elements present inherent accessibility barriers for screen-reader users and keyboard-only engineers. DERA resolves this by delivering a **built-in accessible tabular view** alongside the visual canvas:

```text
[Visual Canvas]  <==== Accessible Toggle ====>  [Accessible Table]
```

---

## 2. Accessible Table Alternative (`AccessibleGraphTable.tsx`)

Users can instantly switch between the visual canvas and the accessible table directory via the toolbar toggle or keyboard shortcut.

The accessible view renders:
1. **Foreign Key Constraints Table**:
   - Semantic `<table>` with `<caption>` and column headers (`scope="col"`).
   - Lists constraint name, referencing child table, referencing columns, arrow direction, referenced parent table, referenced columns, and referential actions (`ON UPDATE`, `ON DELETE`).
2. **Database Entities (Tables) Table**:
   - Semantic table listing namespace, table name, column count, primary key column names, outgoing foreign key count, and incoming foreign key count.
   - Interactive rows trigger selection and inspection details.

---

## 3. SVG Canvas Accessibility Features

For engineers using the visual canvas:
- **ARIA Roles**: Table cards declare `role="button"`, `tabIndex={0}`, and descriptive `aria-label` tags (e.g., `"Table public.orders, 4 columns"`).
- **Keyboard Navigation**: Pressing `Enter` or `Space` selects focused tables and edges.
- **Color Contrast**: All text nodes adhere to minimum 4.5:1 contrast ratios on dark backgrounds (Slate-900 / Slate-950).
- **Tooltips**: All SVG paths feature `<title>` elements for native browser hover descriptions.
- **Shortcuts**: `+`/`-` for zoom, `f` for fit, `r` for reset, `Escape` to clear selection.
