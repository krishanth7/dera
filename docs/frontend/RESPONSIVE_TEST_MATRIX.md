# Responsive Viewport Test Matrix & Evidence

**Module**: `apps/web/`  
**Phase**: 7.6 — Accessibility, Responsive Design & Frontend Quality Assurance  

---

## 1. Viewport Test Matrix

All canonical routes were audited against representative viewport widths in Chromium and WebKit rendering engines:

| Target Viewport | Target Device Profile | Primary Layout State | Result |
| :--- | :--- | :--- | :--- |
| **320px x 568px** | iPhone SE (1st gen) / Compact Mobile | Single column, mobile drawer, responsive dialog | **PASS** |
| **375px x 667px** | iPhone SE (2nd/3rd gen) / Mobile Base | Header collapse, touch-friendly buttons | **PASS** |
| **390px x 844px** | iPhone 14/15/16 Base | Full mobile shell, sticky header | **PASS** |
| **768px x 1024px** | iPad Mini / Portrait Tablet | Two-column collapsible grid, tabbed inspector | **PASS** |
| **1024px x 768px** | iPad Landscape / Small Laptop | Persistent sidebar, multi-panel canvas | **PASS** |
| **1280px x 800px** | 13" MacBook / Corporate Laptop | Full studio view, search filter drawer | **PASS** |
| **1440px x 900px** | High-Res Desktop Standard | Split canvas + inspector side-by-side | **PASS** |
| **1920px x 1080px** | Full HD External Monitor | Max-width bounded container (1280px inner) | **PASS** |

---

## 2. Component Adaptation Verification

- **Navigation Shell**: Sidebar automatically collapses into a slide-over mobile drawer below 768px (`md:` breakpoint).
- **Table Inspector**: Stat cards wrap gracefully from 6 across on desktop to 2 columns on tablet and 1 column on mobile.
- **Search Studio**: Filter pill panel wraps into multiple rows; search input maintains full width on mobile viewports.
- **Dependency Explorer**: Metrics cards stack into 2x2 grid on mobile; cycle loop paths wrap table nodes cleanly without overflow.
