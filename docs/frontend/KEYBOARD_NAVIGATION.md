# Keyboard Navigation & Focus Management

**Module**: `apps/web/`  
**Phase**: 7.6 — Accessibility, Responsive Design & Frontend Quality Assurance  

---

## 1. Overview & General Principles

Every user journey in DERA is designed for complete keyboard operability without requiring mouse or pointer interaction. Keyboard navigation adheres to WAI-ARIA Authoring Practices:

- **Predictable Tab Order**: Logical DOM ordering matching visual reading direction.
- **Skip Navigation**: Top-level skip link to immediately bypass header and sidebar navigation directly to `#main-content`.
- **High-Visibility Focus Indicators**: Enforced via `:focus-visible` dual-contrast outlines across both light and dark themes.
- **Escape Key Handling**: Uniformly dismisses modals, drawers, search dropdowns, and expandable inspectors.

---

## 2. Global Shortcut Matrix

| Key / Shortcut | Context | Action |
| :--- | :--- | :--- |
| `Tab` | Global | Move focus to next interactive element |
| `Shift + Tab` | Global | Move focus to previous interactive element |
| `Enter` / `Space` | Global | Activate button, expand accordion, toggle checkbox |
| `Escape` | Global | Close active dialog, dismiss mobile drawer |
| `/` | Global / Studio | Focus cross-schema search input |
| `F` | ER Canvas | Fit entire diagram to view |
| `R` | ER Canvas | Reset pan and zoom coordinates |
| `+` / `-` | ER Canvas | Zoom in / zoom out |
| `ArrowUp` / `ArrowDown` | Result Lists / Tables | Navigate list items or table rows |

---

## 3. Focus Trapping & Restoration

- **Modals & Dialogs**: Managed via Radix UI primitives with focus trapped inside `<DialogContent role="dialog">`. Focus automatically returns to the triggering button upon dismissal.
- **Mobile Drawer**: Focus is trapped inside the mobile navigation drawer when open. Pressing `Escape` or activating any route closes the drawer and restores focus.
- **Table Inspector Column Details**: Keyboard users can press `Enter` or `Space` on individual column rows to toggle inline attribute details.
