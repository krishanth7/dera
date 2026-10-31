# Diagnostic Dashboard Architecture

## Architectural Overview

The DERA Diagnostics Dashboard provides an interactive, accessible, and deterministic engineering control plane for database schema intelligence. It integrates all diagnostic capabilities delivered across Phase 8 (8.1 through 8.5) into the Next.js App Router frontend.

## Subsystem Pipeline

```text
Phase 8.1–8.4 Diagnostic Rules
           │
           ▼
Phase 8.5 Evaluator (Evidence, Conservative Severity, Recommendations, Suppressions, Prioritization)
           │
           ▼
Authorized FastAPI Diagnostic Services (/api/v1/reverse-engineering/schemas/{id}/diagnostics)
           │
           ▼
Typed API Client (@/lib/diagnostics/api.ts)
           │
           ▼
Next.js Diagnostic Dashboard (/app/diagnostics)
 ├── DiagnosticsOverview (KPI metrics, snapshot picker, re-evaluate trigger)
 ├── SeveritySummary (Accessible severity breakdown & distribution)
 ├── CategorySummary (Domain breakdown: Indexes, Constraints, Relationships, Maintainability)
 ├── RuleCoverage (Execution completeness accounting & formula explanation)
 ├── FindingsFilters (Multi-attribute search, severity/category/status filters, stable sorting)
 ├── FindingsExplorer (Sortable, paginated findings table with keyboard selection)
 ├── FindingDetails (Deep-dive drawer with rationale, evidence, and recommendations)
 ├── EvidenceInspector (Typed evidence records with links to Schema Explorer & Table Inspector)
 ├── RecommendationPanel (Advisory engineering actions, risk considerations, verification)
 └── SuppressionControls (Authorized exemption management & compliance audit trail)
```

## Information Architecture Principles

1. **Deterministic Display**: Metrics, findings, severity badges, and priority scores are derived solely from verified backend diagnostic reports. Client-side heuristic calculations or speculative scores are strictly prohibited.
2. **Deep-Link Traceability**: Diagnostic evidence links directly to verified schema elements in the Schema Explorer (`/app/schemas`) and Table Inspector (`/app/tables`).
3. **Multi-Tenancy Isolation**: Dashboard state and reports are strictly scoped to the active workspace (`useWorkspace`).
4. **Read-Only Safety**: The interface provides advisory recommendations and does not execute automatic database mutations.
