## Summary

DERA Phase 7.4 delivers the **Interactive Entity–Relationship Diagram Canvas & Relationship Visualization Studio**.
Building upon the Phase 7.1 frontend foundation, Phase 7.2 authentication & workspace isolation, Phase 7.3 database connections & schema explorer, and Phase 6.3 backend foreign key relationship graph, Phase 7.4 introduces an interactive visual engineering canvas for multi-table database relationships.

## Change Type

- [x] Feature (`feat`)
- [ ] Bug fix (`fix`)
- [x] Documentation (`docs`)
- [ ] Refactor (`refactor`)
- [x] Performance (`perf`)
- [x] Test improvement (`test`)
- [ ] CI/CD or Build (`ci`, `build`)
- [ ] Security enhancement (`security`)
- [ ] Breaking change (`!`)

## Related Issues

Closes #57

## Implementation Details

- **Interactive ER Canvas (`/relationships`)**: Pure SVG-based interactive canvas supporting smooth sub-pixel panning, zoom toward cursor, fit-to-view, reset-view, and drag-and-drop manual table positioning.
- **Table Node Cards (`TableNode.tsx`)**: High-fidelity SVG table cards rendering namespace badges, table names, column ordinals, types, `[PK]` indicators, and `[FK]` markers with overflow management.
- **Directed Relationship Edges (`RelationshipEdge.tsx`)**: Directional bezier curves pointing from referencing child tables to referenced parent tables, parallel edge offsets, and dedicated self-loop arcs.
- **Composite Foreign Keys**: Unified relationship paths with ordered column pair mappings `(source_col[i] -> target_col[i])` and `[N cols]` pill indicators.
- **Deterministic Layout Engine (`layout.ts`)**: Force-free, cycle-aware, layered topological algorithm guaranteeing identical node coordinates for identical schema inputs.
- **Relationship Details Drawer (`RelationshipDetails.tsx`)**: Sliding inspector panel for selected constraints (column pairs, `ON UPDATE`, `ON DELETE`) and selected entities (columns, incoming/outgoing foreign keys, link to schema explorer).
- **Search & Filters (`GraphFilters.tsx`)**: Real-time search across tables, columns, and constraint names, namespace selector, and isolated table culling.
- **WCAG 2.2 AA Accessible Alternative (`AccessibleGraphTable.tsx`)**: Semantic HTML table directory enabling screen-reader and keyboard-only engineers to inspect every relationship and table entity without visual geometry.
- **Strict Security & Zero-AI**: Zero AI/LLM dependencies, zero heuristic guessing, 100% untrusted text rendering preventing XSS, and workspace isolation headers.

## Testing

- [x] Relevant tests passed (`python scripts/development/dev.py all` or `test`)
- [ ] Tests not applicable — explanation below (e.g., documentation, typo fix, governance)
- [ ] Tests not run / blocked — explanation below

**Test evidence & notes:**
- **TypeScript**: `npm run typecheck` passed with 0 errors across root and `@dera/web`.
- **Unit & Determinism Tests**: 9/9 tests passed in `apps/web/tests/unit/er_canvas.test.ts`.
- **Component Tests**: 8/8 tests passed in `apps/web/tests/component/er_canvas.test.tsx`.
- **Frontend Vitest Suite**: 6 test files, 40 tests passed.
- **Backend Tests**: 859/859 pytest tests passed.
- **Documentation**: All 398 markdown files passed `validate_docs.py` and `markdownlint-cli2`.
- **Mermaid Syntax**: All 81 diagrams passed `validate_mermaid.py`.
- **OpenAPI Snapshot**: 0 drift validated by `validate_openapi.py`.
- **Next.js Production Build**: `npm run build` passed with exit code 0 across all 16 static/dynamic routes.

## Documentation Impact

- [x] Documentation in `docs/` updated or verified where required
- [x] Documentation validation passed (`npm run docs:check`)
- [ ] No documentation updates required for this change

Includes 14 comprehensive markdown specification documents in `docs/frontend/` and baseline/acceptance audits in `docs/audit/`.

## Security Impact & Deterministic Engineering

- [x] **Strict Non-AI Policy:** Verified zero generative AI, LLM, or external inference APIs are introduced.
- [x] **Database Safety:** Verified all database connector operations enforce read-only introspection without data modification.
- [x] **Credential Protection:** Confirmed that no production credentials, passwords, or `.env` secrets are committed.
- [x] **Least Privilege:** Validated that permissions and access boundaries are minimized.
- [x] **No Security Impact:** Change does not affect database connections, security boundaries, or credentials.

## Breaking Changes

- [x] No breaking changes.
- [ ] Breaking change introduced (detailed explanation and migration path below):

## Contributor Checklist

- [x] My code adheres to the project's coding standards (PEP 8, TypeScript strict mode).
- [x] My branch is rebased on the latest `main` branch.
- [x] The PR title follows [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat(web): implement Phase 7.4 interactive ER diagram canvas`).
- [x] No unrelated changes or accidental files are included.
