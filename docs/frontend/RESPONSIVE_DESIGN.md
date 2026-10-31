# Responsive Design Architecture & Breakpoint Strategy

**Module**: `apps/web/`  
**Phase**: 7.6 — Accessibility, Responsive Design & Frontend Quality Assurance  

---

## 1. Overview & Strategy

DERA supports engineers across a wide variety of hardware form factors—from on-call mobile triage (320px–414px) and field tablets (768px–1024px) to dual-monitor desktop engineering setups (1440px–1920px+).

```text
+--------------------------------------------------------------------------+
| Viewport Tier      | Width Range  | Primary Layout Behavior             |
+--------------------+--------------+-------------------------------------+
| Small Mobile (xs)  | 320px - 639px| Collapsible drawer, single-column,  |
|                    |              | horizontal-scroll tables, dialog fix|
| Tablet (sm / md)   | 640px - 1023px| Compact sidebar, stacked panels,   |
|                    |              | tabbed multi-inspector views        |
| Desktop (lg / xl)  | 1024px - 1535px| Persistent sidebar, multi-panel    |
|                    |              | side-by-side studio layout          |
| Ultra-wide (2xl)   | 1536px+      | Bounded max-width (max-w-7xl),      |
|                    |              | centered layout preventing stretch  |
+--------------------------------------------------------------------------+
```

---

## 2. Core Responsive Principles

1. **Content-Driven Breakpoints**: Adapts naturally to data density rather than targeting specific device brands.
2. **Mobile First Utility Scale**: Leverages Tailwind CSS breakpoint prefixes (`sm:`, `md:`, `lg:`, `xl:`, `2xl:`).
3. **Reflow & Scroll Isolation**:
   - Page-level horizontal scroll is strictly prohibited.
   - Genuinely wide data structures (e.g., column lists with 15 attributes) are isolated in scrollable `<div role="region" tabIndex={0}>` wrappers with visual boundary cues.
4. **Touch Target Dimensions**: Interactive elements maintain a minimum target size of $24\text{px} \times 24\text{px}$ adhering to WCAG 2.2 SC 2.5.8 Target Size (Minimum), with primary controls sized at $32\text{px}$ to $44\text{px}$ for comfortable touch interactions.
5. **Dialog Viewport Constraints**: All modals enforce `max-h-[85vh]` and `overflow-y-auto` with responsive width `w-[calc(100vw-2rem)] sm:max-w-lg`, preventing modals from bleeding beyond viewport edges on mobile devices.
