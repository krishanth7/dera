# DERA Phase 7.4 — Interactive ER Diagram Canvas & Relationship Visualization

## Executive Summary
This Pull Request delivers **Milestone 7.4** of DERA: the **Interactive Entity–Relationship Diagram Canvas & Relationship Visualization Studio**.

Building upon the Phase 7.1 frontend foundation, Phase 7.2 authentication & workspace isolation, Phase 7.3 database connections & schema explorer, and Phase 6.3 backend foreign key relationship graph, Phase 7.4 introduces an interactive visual engineering canvas for multi-table database relationships.

## Engineering Highlights
- **Interactive ER Canvas (`/relationships`)**: Pure SVG-based interactive canvas supporting smooth sub-pixel panning, zoom toward cursor, fit-to-view, reset-view, and drag-and-drop manual table positioning.
- **Table Node Cards (`TableNode.tsx`)**: High-fidelity SVG table cards rendering namespace badges, table names, column ordinals, types, `[PK]` indicators, and `[FK]` markers with overflow management.
- **Directed Relationship Edges (`RelationshipEdge.tsx`)**: Directional bezier curves pointing from referencing child tables to referenced parent tables, parallel edge offsets, and dedicated self-loop arcs.
- **Composite Foreign Keys**: Unified relationship paths with ordered column pair mappings `(source_col[i] -> target_col[i])` and `[N cols]` pill indicators.
- **Deterministic Layout Engine (`layout.ts`)**: Force-free, cycle-aware, layered topological algorithm guaranteeing identical node coordinates for identical schema inputs.
- **Relationship Details Drawer (`RelationshipDetails.tsx`)**: Sliding inspector panel for selected constraints (column pairs, `ON UPDATE`, `ON DELETE`) and selected entities (columns, incoming/outgoing foreign keys, link to schema explorer).
- **Search & Filters (`GraphFilters.tsx`)**: Real-time search across tables, columns, and constraint names, namespace selector, and isolated table culling.
- **WCAG 2.2 AA Accessible Alternative (`AccessibleGraphTable.tsx`)**: Semantic HTML table directory enabling screen-reader and keyboard-only engineers to inspect every relationship and table entity without visual geometry.
- **Strict Security & Zero-AI**: Zero AI/LLM dependencies, zero heuristic guessing, 100% untrusted text rendering preventing XSS, and workspace isolation headers.

## Verification & Quality Gates
- **TypeScript**: `npm run typecheck` passed with 0 errors across root and `@dera/web`.
- **Unit & Determinism Tests**: 9/9 tests passed in `apps/web/tests/unit/er_canvas.test.ts`.
- **Component Tests**: 8/8 tests passed in `apps/web/tests/component/er_canvas.test.tsx`.
- **Frontend Vitest Suite**: 6 test files, 40 tests passed.
- **Backend Tests**: 859/859 pytest tests passed.
- **Documentation**: All 398 markdown files passed `validate_docs.py` and `markdownlint-cli2`.
- **Mermaid Syntax**: All 81 diagrams passed `validate_mermaid.py`.
- **OpenAPI Snapshot**: 0 drift validated by `validate_openapi.py`.
- **Next.js Production Build**: `npm run build` passed with exit code 0 across all 16 static/dynamic routes.
- **Baseline & Acceptance Audits**:
  - `docs/audit/PHASE_7_4_ER_CANVAS_BASELINE.md`
  - `docs/audit/PHASE_7_4_ER_CANVAS_ACCEPTANCE.md`
  - 14 technical specification files in `docs/frontend/`

*Note: Per master directive, this PR is submitted for review and will not be automatically merged.*
