# ER Diagram Testing & Verification

**Document Reference**: `docs/frontend/ER_TESTING.md`  
**Milestone**: Phase 7.4 — Interactive ER Diagram Canvas & Relationship Visualization  

---

## 1. Test Suite Architecture

The Phase 7.4 testing strategy encompasses:
- **Unit & Determinism Tests** (`apps/web/tests/unit/er_canvas.test.ts`)
- **Component Tests** (`apps/web/tests/component/er_canvas.test.tsx`)
- **Type Checking** (`npm run typecheck`)
- **Production Build Verification** (`npm run build`)

---

## 2. Test Coverage Summary

### 2.1 Unit & Determinism Coverage

- **API Client**: Verifies `getSchemaRelationships` and `getTableRelationships` issue authorized requests with `X-Workspace-Id`.
- **Composite Mapping**: Verifies ordered column pair resolution `(source_col[i] -> target_col[i])` for composite foreign keys.
- **Parallel Edge Detection**: Verifies multiple distinct foreign keys between identical tables receive unique indices.
- **Self-Loops**: Verifies self-referencing foreign keys are marked for distinct arc routing.
- **Layout Determinism**: Verifies that permuting input arrays of nodes and edges produces 100% identical coordinates.
- **Cycle Safety**: Verifies cyclic relationship graphs execute without infinite loops or stack overflow.

### 2.2 Component Coverage

- **TableNode**: Verifies rendering of table cards, column ordinals, PK/FK indicators, click handlers, and XSS sanitization.
- **RelationshipEdge**: Verifies SVG bezier path rendering, composite badges, and selection handlers.
- **ERToolbar**: Verifies zoom in/out, fit-to-view, reset-view, and auto-layout buttons.
- **RelationshipDetails**: Verifies constraint metadata drawer, column pair tables, and referential actions.
- **AccessibleGraphTable**: Verifies full semantic HTML table rendering for accessibility.
