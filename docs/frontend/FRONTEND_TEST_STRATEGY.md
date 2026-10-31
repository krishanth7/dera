# Frontend Test Strategy & Automation Architecture

**Module**: `apps/web/tests/`  
**Phase**: 7.6 — Accessibility, Responsive Design & Frontend Quality Assurance  

---

## 1. Test Pyramid & Automation Layers

Phase 7.6 employs a multi-tiered test pyramid ensuring high test reliability without flaky mock chains:

```text
                  +--------------------------------+
                  |    E2E & Integration Tests     |
                  |  Multi-studio user flows       |
                  +---------------+----------------+
                                  |
                  +---------------+----------------+
                  |        Component Tests         |
                  | Vitest + React Testing Library |
                  | UI rendering, a11y roles, DOM  |
                  +---------------+----------------+
                                  |
                  +---------------+----------------+
                  |          Unit Tests            |
                  | Fast, deterministic logic      |
                  | Graph algorithms, contrast, BFS|
                  +--------------------------------+
```

---

## 2. Test Suite Breakdown

| Suite | File Path | Focus Area | Test Count |
| :--- | :--- | :--- | :--- |
| **Unit** | `apps/web/tests/unit/utils.test.ts` | Tailwind class merging & string utilities | 4 |
| **Unit** | `apps/web/tests/unit/connections_explorer.test.ts` | Connector config validation & adapters | 5 |
| **Unit** | `apps/web/tests/unit/er_canvas.test.ts` | Deterministic auto-layout & graph permutation | 9 |
| **Unit** | `apps/web/tests/unit/inspector_and_dependencies.test.ts` | Column sorting, BFS reachability, SCCs | 11 |
| **Unit** | `apps/web/tests/unit/accessibility_and_responsive.test.ts` | Contrast ratios, breakpoints, sanitization | 5 |
| **Component** | `apps/web/tests/component/primitives.test.tsx` | Buttons, badges, cards, states | 6 |
| **Component** | `apps/web/tests/component/connections_explorer.test.tsx` | Connection tabs, status banners | 3 |
| **Component** | `apps/web/tests/component/er_canvas.test.tsx` | SVG nodes, edges, toolbar, selection | 9 |
| **Component** | `apps/web/tests/component/inspector_and_dependencies.test.tsx` | Table inspector tabs, search studio, cycles | 10 |
| **Component** | `apps/web/tests/component/accessibility_and_responsive.test.tsx` | Skip link, mobile drawer, dialog, a11y | 6 |
| **Total** | **10 Test Files** | **Comprehensive Frontend Verification** | **68 Tests** |

All 68 tests execute deterministically in Vitest in under 20 seconds.
