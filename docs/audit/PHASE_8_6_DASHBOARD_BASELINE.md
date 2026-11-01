# Phase 8.6 Diagnostics Dashboard & Quality Audit Baseline

## 1. Executive Summary

- **Project**: DERA — Database Engineering & Reverse Analysis
- **Milestone**: 8.6 — Diagnostic Dashboard, Testing & Phase 8 Completion Audit
- **Base Commit SHA**: `694712a82c9a691849338563f1d6c8aba5f70c5a`
- **Branch**: `feat/phase-8.6-diagnostics-dashboard-quality`
- **PR Title**: `feat(diagnostics): complete Phase 8.6 dashboard and quality audit`
- **Audit Date**: 2026-10-31

---

## 2. Verification of Prerequisites (Phases 8.1–8.5)

| Subsystem | Baseline State | Verified Capabilities |
| :--- | :--- | :--- |
| **Phase 8.1 Rules Engine** | Intact & Verified | Rule registry, `DiagnosticContext`, `DiagnosticEvaluator`, rule protocol, base models. |
| **Phase 8.2 Index & Constraints** | Intact & Verified | Duplicate/redundant indexes, missing FK indexes, PK nullability, check constraints. |
| **Phase 8.3 Relationships** | Intact & Verified | FK graph integrity, unresolved FKs, composite FKs, cycles/SCCs, dependency depth, fan-in/fan-out. |
| **Phase 8.4 Maintainability** | Intact & Verified | Wide tables, naming conventions, namespace sprawl, coupling metrics. |
| **Phase 8.5 Severity & Recommendations** | Intact & Verified | Conservative severity policy (`1.0.0`), typed evidence validation, structured recommendations, prioritization, suppressions, explainability summaries. |
| **Phase 7 Frontend Foundation** | Intact & Verified | Next.js App Router, Tailwind CSS, Radix UI primitives, Lucide icons, `WorkspaceProvider`, `AppShell`, schema explorer, table inspector, ER canvas. |

---

## 3. Existing API & Data Contracts

- **Diagnostic Endpoints**:
  - `GET /api/v1/reverse-engineering/diagnostics/rules`: Deterministic list of registered rules with metadata.
  - `GET /api/v1/reverse-engineering/diagnostics/rules/{rule_id}`: Single rule metadata lookup.
  - `POST /api/v1/reverse-engineering/schemas/{schema_id}/diagnostics`: Executes evaluation on authorized schema and returns enriched `DiagnosticReportResponse` containing:
    - `summary`: High-level metrics and counts.
    - `findings`: List of enriched findings with fingerprints, severity, rationale, classification, structured recommendations, evidence, lifecycle state, priority scores.
    - `explainability`: Comprehensive rule accounting, coverage, and breakdown.
- **Frontend Contract**:
  - `@dera/contracts` exports `DiagnosticFinding`, `DiagnosticReport`, `DiagnosticSummary`, `TypedEvidence`, `StructuredRecommendation`.
  - Initial accessible badges in `apps/web/src/components/diagnostics/`: `SeverityBadge`, `ClassificationBadge`, `EvidencePanel`, `RecommendationPanel`, `FindingDetailCard`.

---

## 4. Missing Prerequisites & Gaps for Phase 8.6

1. **Dashboard Route**: No dedicated `/app/diagnostics` route exists in Next.js `apps/web/src/app/(app)/`.
2. **Navigation Integration**: Sidebar navigation in `sidebar.tsx` lacks an active link to Diagnostics.
3. **Overview & Summary Cards**: Overview dashboard cards aggregating severity distributions and rule coverage are not yet composed into a unified dashboard view.
4. **Interactive Findings Explorer**: Filtering (by severity, category, rule, object, search query), sorting, and pagination controls for findings need complete interactive implementation.
5. **Evidence & Recommendation Inspector**: Deep-dive inspection panels allowing navigation to schema tables or ER canvas elements from diagnostic evidence.
6. **Suppression Controls & Governance UI**: Controls to inspect active suppressions, view audit history, or apply temporary exemptions.
7. **Snapshot Selection**: UI component allowing users to choose between the live schema and historical snapshots for comparative diagnostic evaluation.
8. **Automated Testing**: Need Vitest unit and component tests for the dashboard, accessibility tests (WCAG 2.2 AA), and Playwright E2E coverage.
9. **Documentation & Final Audits**: 15 dedicated guides in `docs/diagnostics/`, `docs/audit/PHASE_8_6_DASHBOARD_ACCEPTANCE.md`, and the overarching `docs/audit/PHASE_8_COMPLETION.md`.

---

## 5. Implementation Plan

1. **Information Architecture & Types**: Define frontend client types, API bindings, and mock report fixtures for reliable offline and client-side testing.
2. **Dashboard Route**: Create `apps/web/src/app/(app)/diagnostics/page.tsx`, `loading.tsx`, and `error.tsx`. Add sidebar navigation in `sidebar.tsx`.
3. **Dashboard Components**:
   - `DiagnosticsOverview`: Header, metric cards, evaluate action, snapshot picker.
   - `SeveritySummary`: Accessible severity distribution with percentage bars and data table.
   - `CategorySummary`: Breakdown across indexes, constraints, relationships, dependencies, maintainability.
   - `RuleCoverage`: Explicit coverage formula, executed vs skipped vs unsupported rules.
   - `FindingsFilters`: Multi-attribute filtering (severity, category, status, search text).
   - `FindingsExplorer`: Accessible, sortable, paginated findings table.
   - `FindingDetails`: Drawer/panel with full finding details, priority rank, and links to schema objects.
   - `EvidenceInspector`: Typed evidence breakdown with provenance and completeness indicators.
   - `RecommendationPanel`: Actionable advisory guidance with preconditions, risks, and verification steps.
   - `SuppressionControls`: Suppression modal and audit trail viewer.
   - `SnapshotSelector`: Dropdown to evaluate against current schema or Phase 6 snapshots.
4. **Testing Suite**:
   - Unit tests (`tests/unit/diagnostics_dashboard.test.ts`): Formatter, coverage math, filter logic, sort stability.
   - Component tests (`tests/component/diagnostics_dashboard.test.tsx`): Overview, summary cards, findings explorer, detail drawer, accessibility.
   - E2E tests (`tests/e2e/diagnostics.spec.ts`): Navigation, filtering, finding selection, drawer interaction.
5. **Technical Documentation**: 15 guides in `docs/diagnostics/`.
6. **Audits**:
   - `docs/audit/PHASE_8_6_DASHBOARD_ACCEPTANCE.md`
   - `docs/audit/PHASE_8_COMPLETION.md`
7. **Quality Assurance & Verification**: Full Vitest test suite, typecheck, linting, Python tests, docs check, PR creation.
