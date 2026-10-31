# Dashboard Responsive Layout Specification

## Responsive Breakpoint Support

The dashboard adapts fluidly across mobile, tablet, laptop, and ultra-wide displays using Tailwind CSS breakpoints:

| Viewport | Screen Width | Layout Strategy |
| :--- | :--- | :--- |
| **Mobile** | `< 640px` | Single-column stacked KPI cards, compact table, modal detail sheets. |
| **Tablet** | `640px - 1024px` | 2-to-4 column KPI cards, collapsible filters, full-width findings table. |
| **Desktop** | `1024px - 1280px` | Multi-panel split: 7-column findings table and 5-column detail inspection drawer. |
| **Large Desktop**| `> 1280px` | 8-column KPI grid, side-by-side distribution charts, and persistent detail panels. |
