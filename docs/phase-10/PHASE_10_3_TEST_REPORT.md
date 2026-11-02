# Phase 10.3 Verification Report

Baseline main: `5409284f38a388c0ae46bf2326b096200560935d`. Python 3.12.14, Node 24.22.1,
SQLGlot 30.27.0. Database format references are linked in the dialect capability document.
Controlled fixtures are synthetic; no live customer plans or query execution were used.

## Local evidence

| Check | Observed result |
|---|---|
| Full backend pytest run | 1,342 passed, 2 skipped, 407 subtests; 86.34 seconds |
| Focused imported-plan tests after numeric/logging additions | 68 passed; 9.98 seconds |
| SQL engineering corpus before final numeric/logging additions | 237 passed; 39.95 seconds |
| Frontend component/unit suites before benchmark addition | 114 passed, 14 files |
| New explorer component tests | 8 passed |
| New synthetic DOM benchmark | 1 passed, five iterations per size |
| TypeScript | Root and workspace typecheck passed |
| Production build | Contracts and Next.js build passed; execution-plans route generated |
| Ruff | Repository check and formatting passed, 760 Python files |
| Bandit | Exit 0, no medium/high findings; existing migration nosec warnings |
| OpenAPI | Generated snapshot updated; zero-drift validation performed |

The full backend run preceded a subsequent actual-metric summary correction and conservative
native-structure ordering refinement. Focused tests and CI on the delivered head are the final
qualification authority; final follow-up results are recorded below. The two existing local
PostgreSQL tests require a live server; hosted CI supplies its PostgreSQL service. No frontend
browser result is inferred from jsdom success.

Tests cover four dialects, operation mapping, cost units and inclusive ranking, average actual
rows/loops, zero/missing/parallel metrics, unknown operations, Unicode, malformed JSON, duplicate
keys, invalid/non-finite/overflow metrics, 1,000-node acceptance and node/depth rejection, SQLite
cycle/orphan/bytecode rejection, deterministic reports, recommendation evidence, optional shared
SQL diagnostics, real sessions/workspace/CSRF enforcement and connector-spy regression.

## Performance evidence

Run `python scripts/development/benchmark_execution_plans.py` for 20 iterations per fixture.
Raw evidence: [backend benchmark](PHASE_10_3_BENCHMARK.json). Decode, normalization,
diagnostics and serialization are measured separately; total measures complete analysis including
fingerprint construction. tracemalloc peak means traced Python allocations, not process RSS.

Run `DERA_PLAN_BENCHMARK_OUTPUT=/tmp/dera-dom-benchmark.json npm run test --workspace=apps/web -- tests/component/execution-plans-performance.test.tsx`
for the optional DOM evidence file. [Frontend benchmark](PHASE_10_3_FRONTEND_BENCHMARK.json)
records five iterations each: 10 nodes 12.380 ms, 100 nodes 58.281 ms, 1,000 nodes 245.503 ms
median React/jsdom rendering in the initial run. No timing threshold is asserted.

## Browser qualification limitations

Playwright Chromium installation was attempted; downloaded archives were invalid/truncated and
installation failed. Cloud Browser inspected the live repository and dependency PRs, but its
container could not reach the local production server (`ERR_CONNECTION_REFUSED`). Consequently
no real-browser E2E, paint/FPS, mobile viewport or automated accessibility scan is claimed.
This limitation keeps overall acceptance PARTIAL pending browser qualification.

## Final local follow-up

- Final SQL engineering corpus: 245 passed, 9 deprecation warnings, 39.47 seconds.
- Final frontend suites: 116 passed across 16 files, including workspace fetch-loop regression.
- Updated production build and TypeScript passed after workspace-provider integration correction.
- Two new Playwright tests were attempted: both failed at browser launch (missing Chromium
  executable), so neither test body executed. They are wired into hosted frontend CI, which installs
  its own browser runtime; hosted results will be recorded separately.
- Markdown lint, internal links/anchors, all 85 Mermaid diagrams, generated navigation and ten-language
  parity passed across 619 Markdown files. No medium/high Bandit findings; Ruff covered 762 files.

The workspace provider callback previously depended on the workspace value it updated, causing
repeated fetches when a real authorized workspace loaded. A stable callback and functional fallback
remove that loop; a dedicated test verifies a single request. Authentication behavior is unchanged.

## First hosted browser qualification

DERA CI run [41430491819](https://github.com/krishanth7/dera/actions/runs/41430491819),
frontend job 125227541059, head `9fef125`, successfully installed Chromium and passed both
browser tests (2 passed, 2.2 seconds), including desktop keyboard interactions and mobile overflow.
All 116 frontend unit/component tests, lint, typecheck and production build also passed in that job.
The local runtime limitation is therefore environment-specific and has a verified hosted fallback.

Final refinements preserve MySQL array-entry dependent/cacheable metadata and distinguish
PostgreSQL InitPlan children from Inner join inputs. Dedicated parser regressions: 54 passed.
A third hosted browser test measures five response-to-painted-plan observations each for
10/100/1,000-node and deep-25 synthetic imports, without treating them as execution cost.

Final pre-delivery follow-up: 247 SQL tests passed before the outer-envelope security addition;
77 focused plan/parser/API tests passed after that addition (13.29 seconds). The new request
pre-decoder test submits 2,000 nested containers and verifies a safe 422 instead of recursion failure.
