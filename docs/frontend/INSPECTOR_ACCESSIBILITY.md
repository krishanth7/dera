# Inspector & Dependency Accessibility (WCAG 2.2 AA)

**Modules**: `table-inspector`, `schema-search`, `dependency-explorer`  
**Phase**: 7.5 — Table Inspector, Advanced Search & Dependency Visualization  

---

## 1. Accessibility Standards & Targets

Phase 7.5 components are engineered to adhere to WCAG 2.2 Level AA requirements, ensuring that complex structural diagrams and database metadata tables are accessible to users relying on assistive technologies or keyboard-only navigation.

---

## 2. Accessible Tabular Alternatives for Graphs

Visual node-link dependency graphs can present barriers to screen reader users. DERA provides a full semantic HTML equivalent:

- **`AccessibleDependencyTable`**: Renders every node, its incoming dependents, outgoing prerequisites, topological level, and cycle membership in a standard HTML `<table>`.
- **Semantic Markup**: Uses proper `<caption>`, `<thead scope="col">`, and `<tbody scope="row">` tags.
- **Screen Reader Announcements**: Uses `aria-label`, `aria-describedby`, and ARIA live regions for dynamically loaded search results and graph filtering.

---

## 3. Keyboard Navigation & Focus Management

| Component | Keybinding / Focus Behavior |
| :--- | :--- |
| **Search Studio** | Global `/` shortcut activates search input; `Esc` clears query or closes filters; arrow keys navigate result list. |
| **Table Tabs** | Standard ARIA tabs (`role="tablist"`, `role="tab"`, `role="tabpanel"`); `ArrowLeft`/`ArrowRight` switches tabs. |
| **Column Drawer** | Expands with `Enter` or `Space`; focus is trapped within drawer if modal, or smoothly moves to inspection details. |
| **Reachability Filters** | Radio buttons group together with arrow-key toggling and keyboard focus indicators. |

---

## 4. Contrast & Color Invariants

- **Color Independence**: Status indicators (e.g., `COMPLETE`, `PARTIAL`, `RESTRICTED`) never rely on color alone; textual badges, icon shapes, and aria-labels accompany each state.
- **Contrast Ratios**: All foreground text against background meets or exceeds 4.5:1 for normal text and 3:1 for large text/badges.
- **Reduced Motion**: Respects `prefers-reduced-motion: reduce` by disabling canvas transition animations and smooth scrolls.
