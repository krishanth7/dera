# Phase 10.3 Execution Plan Architecture

## Verified baseline and scope

Implementation branch: `feat/phase-10-3-execution-plan-intelligence`.
Baseline: `5409284f38a388c0ae46bf2326b096200560935d` on main, after PRs #75, #76 and #77
were merged under the preceding merge authorization. PR #75's vulnerable re2js dependency
was patched and its audit passed. PR #77's three correctness findings were fixed with regressions.
Cloud Browser verified both Phase 10 dependency PRs as merged. The Phase 10.3 PR remains open.

The official [roadmap](../roadmap/README.md) calls for execution-plan visualization and cost
analysis. No separate existing 10.3 specification was found. This milestone follows the supplied
brief, with an explicit string-based import contract to bound JSON nesting before decoding.
No live plan acquisition is implemented. No parser dependency or connector contract changes.

## Boundaries

`packages/core/src/dera/sql_engineering/execution_plans/` separates immutable models, format and
operation registries, bounded JSON decoding, dialect normalization, evidence rules and report
construction. Flat node records carry explicit parent and ordered child identifiers; this avoids
recursive API serialization. Native metadata is retained as canonical JSON strings.

Phase 10.1's dialect resolver and immutable base model are reused. Associated SQL invokes the
Phase 10.2 engine once, preserving its bounded AST parser, versioned scoring and recommendation
contracts. Plan parsing never uses a SQL parser. Phase 8 severity values are reused. Fingerprints
use domain-separated SHA-256 and sorted, finite JSON, consistent with deterministic Phase 9 design.

FastAPI uses existing session, workspace membership, permission, CSRF and Problem Details
machinery. Analysis runs in the existing threadpool pattern. No plan state is persisted or shared
between workspaces. No database connection is accepted by the request.

The frontend extends the existing API client, workspace provider, application shell and sidebar.
A stable workspace refresh callback removes an existing fetch loop exposed by plan integration;
a dedicated regression verifies one initial authorized workspace request.
The existing ER canvas was inspected: its schema-specific node contracts are unsuitable for plan
metrics. The explorer follows its SVG/HTML pattern without adding a graph dependency. Accessible
native buttons and a paginated structured table complement the scrollable graph.

## Flow

1. Authoritative workspace authorization and CSRF validation.
2. Bounded raw body, then bounded imported JSON string decoding.
3. Dialect-specific normalization and tree/reference validation.
4. Deterministic summaries, evidence rules and optional static SQL diagnostics.
5. Canonical report fingerprint and no-store response.
6. Workspace-local visual exploration; stale requests abort on workspace changes.

See [models](PHASE_10_3_PLAN_MODELS.md), [API](PHASE_10_3_API_CONTRACT.md),
[security](PHASE_10_3_SECURITY.md) and [acceptance](PHASE_10_3_ACCEPTANCE.md).
