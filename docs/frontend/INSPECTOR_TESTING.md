# Inspector & Dependency Testing Strategy

**Modules**: `apps/web/tests/unit/`, `apps/web/tests/component/`  
**Phase**: 7.5 — Table Inspector, Advanced Search & Dependency Visualization  

---

## 1. Testing Pyramid Overview

Phase 7.5 adopts a deterministic, multi-tiered testing strategy verifying object adapters, search algorithms, graph traversals, and interactive component rendering without mock-induced false positives.

```text
                  +--------------------------------+
                  |    E2E & Integration Tests     |
                  |  Playwright Cross-Studio Flows |
                  +---------------+----------------+
                                  |
                  +---------------+----------------+
                  |        Component Tests         |
                  | Vitest + React Testing Library |
                  +---------------+----------------+
                                  |
                  +---------------+----------------+
                  |          Unit Tests            |
                  |  Algorithms, BFS, Sorting, Adapters
                  +--------------------------------+
```

---

## 2. Test Suites & Coverage

### Unit Tests (`apps/web/tests/unit/inspector_and_dependencies.test.ts`)

- **Column Sorting & Ordinal Preservation**: Verifies that default sorting maintains native physical column order and user overrides do not mutate underlying arrays.
- **Constraint Grouping**: Validates composite foreign key multi-column pair preservation.
- **Dependency Reachability**: Validates bounded BFS depth constraints (1, 2, 3 hops) on cyclic and acyclic graphs.
- **Execution Ordering**: Confirms topological level grouping and reverse teardown order calculations.

### Component Tests (`apps/web/tests/component/inspector_and_dependencies.test.tsx`)

- **`TableMetadataHeader`**: Tests rendering of metadata badges, namespace, engine, and completeness.
- **`AccessibleDependencyTable`**: Verifies WCAG 2.2 AA table elements, column headers, and screen reader labels.
- **`CycleAnalysisPanel`**: Verifies cycle detection alert banners, elementary loop paths, and SCC breakdowns.
- **`ExecutionOrderingPanel`**: Verifies topological level grouping, creation order, and drop order tabs.

---

## 3. Execution Verification

All tests run via the local test runner:

```bash
# Execute Phase 7.5 unit and component tests
npx vitest run apps/web/tests/unit/inspector_and_dependencies.test.ts apps/web/tests/component/inspector_and_dependencies.test.tsx
```

All 21 test cases (11 unit + 10 component) pass deterministically in under 5 seconds.
