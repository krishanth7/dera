## Summary

DERA Phase 7.5 delivers the **Table Inspector, Advanced Search & Dependency Visualization Studio**.
Building upon the Phase 7.1 frontend foundation, Phase 7.2 authentication & workspace isolation, Phase 7.3 database connections & schema explorer, Phase 7.4 ER canvas, and Phase 6.1–6.6 canonical backend APIs, Phase 7.5 introduces a comprehensive, deterministic database object inspection and structural dependency analysis suite.

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

## Implementation Details

- **Table Inspector (`/tables/[tableId]`)**:
  - `TableMetadataHeader`: Displays native table identity, namespace, engine badge (`postgresql`, `sqlite`, `mysql`, `mariadb`), completeness status (`COMPLETE`, `PARTIAL`, `RESTRICTED`), snapshot indicator, and action links to the ER Canvas, Dependency Explorer, and Schema Explorer.
  - `TableSummaryCards`: Stat counters for columns, primary keys, foreign keys, unique constraints, check constraints, and indexes. Clicking any card switches the active tab.
  - `ColumnsTab`: Ordinal column table with client-side sorting, text filtering, primary/foreign key badges, and expandable column inspection rows.
  - `ConstraintsTab`: Constraint inspection supporting multi-column composite primary keys, composite foreign key mappings, referential actions (`ON UPDATE`, `ON DELETE`), unique constraints, and inert check constraint expressions.
  - `IndexesTab`: Index inspection displaying indexed columns, uniqueness, and primary status.
  - `DependenciesTab`: Immediate upstream and downstream dependencies with cycle status detection and direct link to the Dependency Explorer.
  - `RawMetadataTab`: Formatted JSON representation of the canonical table object with clipboard copy action.
- **Advanced Schema Search (`/search`)**:
  - `SchemaSearchStudio`: Cross-schema search coordinator with 300ms debouncing, in-flight cancellation via `AbortController`, and keyboard shortcut (`/`).
  - `SearchFiltersPanel`: Object type pills (tables, views, columns, constraints, indexes, namespaces), schema selector, namespace selector, constraint category filter, active filter badges with reset.
  - `SearchResultsList`: Paginated results with object badges, matched field/snippet, keyboard accessibility, rows-per-page selector (10, 25, 50).
- **Dependency Explorer (`/dependencies` & `/dependencies/[objectId]`)**:
  - `DependencySummaryBanner`: High-level metrics for tables, edges, cycles, SCC count, cyclic SCCs, parallel levels.
  - `CycleAnalysisPanel`: Elementary cycles with table loops and breakability strategies (`DEFER_FOREIGN_KEY`, `NULLIFY_COLUMN`, `RESTRICT`), SCC component lists, database cycle educational guidance.
  - `ExecutionOrderingPanel`: Parallel migration levels, strict topological creation order, reverse topological drop order.
  - `TransitiveReachabilityPanel`: Focus table selector, depth controls (1, 2, 3, Transitive), upstream prerequisites vs. downstream blast radius lists.
  - `AccessibleDependencyTable`: Semantic HTML table for 100% WCAG 2.2 AA non-visual dependency inspection.
- **Universal Object Inspector Abstraction**:
  - `InspectorObjectKind` (`table`, `view`, `materialized_view`, `collection`, `document_type`, `database_resource`) and `InspectorObject` model for future NoSQL/Cloud resource extensibility without misrepresenting document collections as relational tables.
- **Strict Security & Zero-AI**:
  - Zero AI/LLM dependencies, zero heuristic guessing, 100% untrusted text rendering preventing XSS, and workspace isolation headers.

## Testing

- [x] Relevant tests passed (`python scripts/development/dev.py all` or `test`)
- [ ] Tests not applicable — explanation below (e.g., documentation, typo fix, governance)
- [ ] Tests not run / blocked — explanation below

**Test evidence & notes:**
- **TypeScript**: `npm run typecheck` passed with 0 errors across root monorepo and `@dera/web`.
- **Unit & Component Tests**: 57/57 tests passed in Vitest (`apps/web`).
  - 11 unit tests in `apps/web/tests/unit/inspector_and_dependencies.test.ts`.
  - 10 component tests in `apps/web/tests/component/inspector_and_dependencies.test.tsx`.
- **Documentation**: All 413 markdown files passed `validate_docs.py`, `validate_mermaid.py`, `generate_language_navigation.py`, and `markdownlint-cli2`.
- **Next.js Production Build**: `npm run build` passed with exit code 0 across all 17 static and dynamic routes.

## Documentation Impact

- [x] Documentation in `docs/` updated or verified where required
- [x] Documentation validation passed (`npm run docs:check`)
- [ ] No documentation updates required for this change

Includes comprehensive specification documents in `docs/frontend/` and baseline/acceptance audits in `docs/audit/`:
- `docs/audit/PHASE_7_5_INSPECTOR_BASELINE.md`
- `docs/audit/PHASE_7_5_INSPECTOR_ACCEPTANCE.md`
- `docs/frontend/TABLE_INSPECTOR.md`
- `docs/frontend/COLUMN_INSPECTION.md`
- `docs/frontend/CONSTRAINT_INSPECTION.md`
- `docs/frontend/INDEX_INSPECTION.md`
- `docs/frontend/SCHEMA_SEARCH.md`
- `docs/frontend/SEARCH_FILTERS.md`
- `docs/frontend/DEPENDENCY_EXPLORER.md`
- `docs/frontend/DEPENDENCY_DIRECTION.md`
- `docs/frontend/TRANSITIVE_DEPENDENCIES.md`
- `docs/frontend/CYCLE_VISUALIZATION.md`
- `docs/frontend/DEPENDENCY_IMPACT.md`
- `docs/frontend/INSPECTOR_ACCESSIBILITY.md`
- `docs/frontend/INSPECTOR_SECURITY.md`
- `docs/frontend/INSPECTOR_PERFORMANCE.md`
- `docs/frontend/INSPECTOR_TESTING.md`
- `docs/frontend/FUTURE_NOSQL_INSPECTION.md`
