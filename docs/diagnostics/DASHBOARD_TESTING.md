# Dashboard Testing Specification

## Test Strategy

The dashboard testing suite guarantees correctness, visual fidelity, accessibility, and contract synchronization.

## Test Suites

1. **Unit Tests (`apps/web/tests/unit/diagnostics_dashboard.test.ts`)**:
   - Coverage computation, rounding, zero-denominator safety.
   - Severity, classification, and priority rank formatters.
   - Multi-attribute filter logic and deterministic sorting with tie-breakers.
2. **Component Tests (`apps/web/tests/component/diagnostics_dashboard.test.tsx`)**:
   - Render testing of `SeveritySummary`, `CategorySummary`, `RuleCoverage`, `FindingsFilters`, `FindingsExplorer`, `FindingDetails`, and `DiagnosticsOverview`.
   - Interaction testing (clicks, keyboard navigation, row activation).
3. **End-to-End Tests (`apps/web/tests/e2e/diagnostics.spec.ts`)**:
   - Navigation from sidebar to `/app/diagnostics`.
   - Search filtering and detail drawer inspection.

## Execution Command

```bash
npm run test --workspace=@dera/web
```
