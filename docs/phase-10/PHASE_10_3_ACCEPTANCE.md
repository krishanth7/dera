# Phase 10.3 Acceptance

## Verdict: PARTIAL pending final hosted checks

Implemented imported-plan models, four explicit format contracts, bounded parsers, deterministic
cost/cardinality analysis, evidence findings/recommendations, workspace-authorized offline API,
OpenAPI and interactive explorer. No live acquisition, customer SQL execution, AI or automatic
remediation. Phase 10.1 and 10.2 are merged on the recorded baseline. Phase 10.3 is delivered as
a separate reviewable branch and PR; it is not merged or released.

| Acceptance area | Evidence/status |
|---|---|
| Foundation reuse | Phase 10.1 models/dialects; Phase 10.2 optional static SQL diagnostics |
| Canonical plans | Versioned flat typed nodes, nullable metrics, native metadata, provenance |
| Dialect support | PostgreSQL JSON, MySQL JSON v1, separate MariaDB JSON, SQLite EQP rows |
| Cost accuracy | Engine-specific units; no cumulative cost summation, runtime attribution or worker multiplication |
| Findings/recommendations | Eleven evidence rules with limitations and manual review |
| Explorer | Graph, native keyboard controls, structured table, selection, metrics and evidence; component tests pass |
| Authorization/security | Existing sessions/workspaces/CSRF, bounded input, no-store, no connector execution |
| Documentation/contracts | Ten milestone documents, raw benchmarks, OpenAPI and indexes |
| Browser/accessibility | First hosted Chromium run passed both desktop/mobile tests; local browser runtime remains blocked |
| Hosted CI | Must be reviewed on the delivered PR head; local evidence is not substituted for hosted results |

Known limitations: no live plans, MySQL JSON v2/TREE, SQLite VM bytecode, generalized exclusive
cost decomposition, cross-engine cost comparison, trusted imported provenance, guaranteed
plan/SQL correspondence, index prescriptions, join-order optimality or parallel overhead inference.
SQLite description formats and vendor extensions can remain UNKNOWN/PARTIAL. Hard runtime and
memory isolation require deployment controls. Final-head browser checks and manual assistive-technology qualification remain separate from
component tests. The first hosted desktop/mobile browser run passed.

See [test report](PHASE_10_3_TEST_REPORT.md) for exact results and skips.
