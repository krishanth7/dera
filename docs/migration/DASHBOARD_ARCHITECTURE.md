# Phase 9.6: Migration Engineering Dashboard Architecture

## Executive Architectural Summary
The Migration Engineering Dashboard serves as the unified qualification and interactive engineering workspace for DERA Phase 9. It brings together the five deterministic engines into an integrated user journey:

1. **Phase 9.1 — Schema Snapshot Comparison**: Pairwise diffing of canonical snapshot representations across PostgreSQL, SQLite, MySQL, and MariaDB.
2. **Phase 9.2 — Schema Change Risk Analysis**: Deterministic classification of backwards compatibility, destructive drops, and data loss risks (P1–P5 priorities).
3. **Phase 9.3 — Deterministic Migration Planning**: Topological ordering of abstract migration operations into dependency-safe execution stages with manual gates.
4. **Phase 9.4 — Dialect-Aware SQL Generation**: Review-only DDL compilation with safe quoting, transaction boundary enforcement, and offline AST validation.
5. **Phase 9.5 — Governance Review & Safety Controls**: Four-eyes principle (Separation of Duties), quorum approvals, tamper-evident audit hash chaining, and controlled export eligibility.

## Safety & Non-Negotiable Tenet
**DERA IS REVIEW-ONLY. MUTATIONS AGAINST CUSTOMER DATABASES ARE STRICTLY PROHIBITED.**
The workspace prominently displays:
> `GENERATED FOR REVIEW — NOT EXECUTED`

All generated SQL artifacts, comparison diffs, and migration plans are advisory artifacts designed for human engineering peer review and controlled CI/CD export. No execution or mutation triggers exist in the frontend or backend API.

## Frontend Directory & Component Layout
```
apps/web/src/
├── app/(app)/
│   └── migrations/
│       └── page.tsx                         # Next.js App Router entrypoint
├── components/migrations/
│   ├── MigrationDashboard.tsx               # Orchestrates workflow stages & metrics
│   ├── SnapshotSelector.tsx                 # Snapshot selector with dialect compatibility checks
│   ├── SchemaDiffExplorer.tsx               # Phase 9.1 diff table & property-level changes
│   ├── RiskDetailPanel.tsx                  # Phase 9.2 risk findings & blast radius analysis
│   ├── MigrationPlanViewer.tsx              # Phase 9.3 DAG stages & manual decision gates
│   ├── SqlArtifactViewer.tsx                # Phase 9.4 formatted DDL & AST validation
│   ├── GovernanceReviewPanel.tsx            # Phase 9.5 SoD enforcement & peer sign-off
│   └── AuditEvidencePanel.tsx               # Phase 9.5 tamper-evident audit log & export
├── lib/migrations/
│   ├── types.ts                             # TypeScript contracts & DTO schemas
│   └── fixtures.ts                          # Deterministic demo fixtures for isolated verification
└── tests/component/
    └── migration_dashboard.test.tsx         # Vitest component test suite (8 tests)
```

## Accessibility & Responsive Design Target
- **WCAG 2.2 AA Compliance**: Semantic HTML, distinct text badges alongside color indicators (P1-P5, ADDED, REMOVED, MODIFIED), full keyboard navigability with proper focus states.
- **Responsive Layout**: Fluid CSS Grid and Flexbox layouts supporting desktop, laptop, tablet, and mobile viewports with horizontal scrolling data tables.
