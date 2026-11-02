# Phase 10.3 Verification Report

## Baseline and delivered implementation

Main baseline: `5409284f38a388c0ae46bf2326b096200560935d` containing merged PRs #75, #76 and #77.
Branch: `feat/phase-10-3-execution-plan-intelligence`. Reviewable [PR #78](https://github.com/krishanth7/dera/pull/78)
is open and unmerged. First fully hosted-qualified executable head: `b0ad97b45efdb203b1a596451543ddc64b17b211`.
A final security refinement moves pre-decoder envelope scanning into the thread pool; its
251-test SQL regression passed. Current PR checks identify the delivery head.

Local Python 3.12.14 and Node 24.22.1; hosted Python 3.12/3.13 and Node 22. SQLGlot 30.27.0
is unchanged. Fixtures are controlled synthetic plans and documented vendor shapes, not live
customer captures or certification across every database/server version.

## Exact local results

| Check | Result |
|---|---|
| Full backend `python -m pytest -q` | 1,353 passed, 2 skipped, 411 subtests, 25 warnings; 91.34 seconds |
| SQL engineering corpus | 250 included in full run; final off-loop refinement: 251 passed, 40.11 seconds |
| Focused parser tests | 55 passed, 0.61 seconds |
| Plan API tests | 24 passed in focused run; final 25 included in the 251-test SQL regression |
| Escaped near-limit import after formatting refinement | 1 passed, 23 deselected, 2.20 seconds |
| Frontend unit/component suites | 116 passed across 16 files; 11.43 seconds |
| TypeScript and production build | Root/workspace checks and contracts/Next.js build passed |
| Repository lint/format | Ruff and configured ESLint passed; 760 Python files formatted |
| Bandit medium/high gate | Passed; existing migration nosec warnings only |
| OpenAPI | Zero drift |
| Documentation | Markdown lint, links, anchors and fences passed across 619 files |
| Mermaid/i18n/navigation | 85 diagrams, 10 languages and 12 navigation documents passed |

The two existing PostgreSQL tests skip locally without a live service. Hosted CI's PostgreSQL
job passed both live tests. Existing deprecation warnings were retained, not suppressed. Existing
ESLint configuration excludes TS/TSX; strict TypeScript and behavioral suites qualify the added
TypeScript. No new type-lint coverage is claimed.

Tests cover four dialects, estimates/imported actuals, decimal-string MySQL filtering, distinct
MariaDB counters, SQLite EQP, Unicode, zero/missing/parallel/overflow metrics, inclusive costs,
stable fingerprints/recommendations, unknown operations, malformed JSON, duplicate keys,
non-finite numbers, 1,000-node acceptance, size/depth rejection, cycles/orphans, VM rejection and
shared SQL diagnostics. Tests preserve wrapper flags and distinguish Inner from auxiliary plans.

Security tests use real sessions/workspaces: anonymous/forged/revoked/expired sessions, foreign/
suspended workspaces, foreign members, CSRF, forbidden identity/connection fields, safe errors,
no-store, sensitive-plan logs, connector and low-level SQLite connection spies. A 2,000-container
outer envelope is rejected before framework decoding. A near-1-MiB plan with over 6 MB of outer
Unicode escapes succeeds while decoded plan limits remain unchanged.

## Hosted qualification

[DERA CI run 41432016461](https://github.com/krishanth7/dera/actions/runs/41432016461), executable
head `b0ad97b`, completed successfully. All seven jobs passed:

- Python 3.12, job 125232634852: repository regression/build checks and 250 SQL tests (37.20 seconds).
- Python 3.13, job 125232634974: same mandatory SQL corpus and repository regression/build checks.
- Frontend, job 125232634881: 116 tests, typecheck, lint, build and 3 Chromium cases.
- PostgreSQL/SQLite, job 125232634998: all integration suites, including 2 live PostgreSQL tests.
- Contracts/architecture, job 125232634515.
- Documentation, job 125232635129.
- Qualification Gate, job 125233769162.

Separate security, CodeQL, schema, multilingual, title and readiness checks were inspected.
Review findings for discarded wrapper metadata, Inner versus auxiliary children, MySQL filtered
strings, encoded-body overhead and event-loop blocking were fixed and regression-tested. Human approval
and merging remain separate.

## Performance evidence

`python scripts/development/benchmark_execution_plans.py`: 20 iterations per backend fixture.
[Raw backend measurements](PHASE_10_3_BENCHMARK.json) include independent decode, normalization,
diagnostics and serialization timings plus full-engine timing and peak traced allocations.

| Fixture | Nodes | Input bytes | Full-analysis median ms | Peak traced bytes |
|---|---:|---:|---:|---:|
| Small | 10 | 1,026 | 0.664 | 124,743 |
| Medium | 100 | 10,745 | 5.358 | 1,227,537 |
| Large | 1,000 | 108,844 | 59.440 | 12,259,385 |
| Deep | 25 | 897 | 1.235 | 276,960 |
| Large imported metadata | 1,000 | 708,244 | 81.343 | 14,697,757 |

Tracemalloc is not process RSS or an enforced memory quota. These are offline synthetic imports,
not query execution benchmarks or latency SLAs.

[Hosted Chromium measurements](PHASE_10_3_BROWSER_BENCHMARK.json), five observations per fixture:
10 nodes 96.6 ms, 100 nodes 128.8 ms, 1,000 nodes 585.4 ms, deep-25 96.9 ms medians.
Timing spans click-to-report plus two animation frames, including mocked transport/test-driver
overhead; it is not isolated React CPU time or FPS. All 3 browser cases passed in 7.2 seconds,
covering keyboard selection, collapse, zoom, table access, mobile overflow and bounded rendering.
The component benchmark also verifies fit-to-screen for 1,000 nodes. Initial
[jsdom measurements](PHASE_10_3_FRONTEND_BENCHMARK.json) remain separate.

## Environment limits and follow-up

Local Playwright archives were invalid/truncated; 2 initial E2E cases failed at launch without
executing assertions. Cloud Browser verified repository/PR state but could not reach localhost.
Hosted Chromium supplied successful browser qualification; these local failures are not hidden
or counted as passing local tests.

No manual screen-reader certification, automated axe scan, cross-browser matrix, production load/
concurrency qualification or exhaustive server-version compatibility is claimed. Deployment-level
resource controls remain necessary. These limits do not authorize live query execution.

Final security review: bounded outer-envelope scanning now uses the thread pool before framework
JSON decoding. A dedicated test records a different thread identity for both valid and forged-session
requests, preserving 200/401 behavior. The full 251-test SQL corpus passed after this change.
This moves CPU work off the event loop; it does not claim process isolation or deployment-level
rate limiting. The 1,353-test full-suite result predates this scheduling-only refinement.
