# Phase 10.2 Verification Report

Verified on 2026-11-02 in ChatGPT Work, Linux x86_64, Python 3.12.14.
SQLGlot 30.27.0 is inherited unchanged from Phase 10.1.

## Baseline and live inspection

Cloud Browser opened the repository, PR #76, its Checks tab and its source branch. GitHub
reads confirmed main `3419eaefd5ee790b35578a1dc25019f77102726c` and the unmerged Phase 10.1
head `d4492156f51bad318f997ea1ad86e2214613fb01`. The Phase 10.1 main CI, security, schema,
documentation and CodeQL workflows completed successfully. An earlier PR-title failure was
superseded by successful title checks. Phase 10.2 remains a dependent branch, not a main build.

## Local engineering checks

| Check | Result |
| --- | --- |
| First SQL-engineering corpus | 155 passed, 6 warnings; 29.76s |
| Expanded core diagnostics corpus | 48 passed; 0.45s |
| Full backend regression before final alias-case refinement | 1,266 passed, 2 skipped, 407 subtests; 69.80s |
| Full backend after alias-case refinement | 1,267 passed, 2 skipped, 407 subtests; 70.38s |
| Final SQL engineering, API contracts and architectural boundaries | 226 passed, 30 subtests; 30.33s |
| Ruff repository lint and format | PASS |
| Bandit medium/high security gate | PASS |
| Generated OpenAPI update and zero-drift check | PASS |
| Backend wheel production build | PASS, dera_core-0.1.0.dev1-py3-none-any.whl |

Two existing PostgreSQL tests skip because 127.0.0.1:5432 has no reachable PostgreSQL service
(test_postgres_live.py lines 168 and 254). No diagnostics test needs customer SQL execution.
The pytest CI step introduced by Phase 10.1 already collects this expanded corpus. No additional
workflow or frontend code changes are required. Frontend-specific rendering, accessibility,
TypeScript and browser UI tests are not run: no existing Phase 10.1 SQL UI was found to extend.
The established API contracts and backend architectural boundary suites are included in the full run.

## Qualification coverage

Tests cover every registered structural rule, all four dialects, simple/wildcard SELECTs,
joins and Cartesian joins, predicates, CTEs, nested and qualified correlated subqueries,
windows, aggregations, UNION/UNION ALL, batches, malformed and unsupported syntax, byte/depth
limits and invalid Unicode. Schema tests cover absent/incomplete context, known/unknown tables,
unknown/ambiguous columns, exact-case handling, types, recorded FK matches, leading BTREE
coverage, corrupt fingerprints, dialect mismatch and conservative derived/USING/NATURAL handling.

Determinism tests compare full normalized reports and fingerprints, stable ordering, exact
weighted factors and version-bound digests. A parser spy verifies exactly one SQLGlot parse
per request and equality with the Phase 10.1 response. Security tests use real platform sessions,
revoked/expired/forged tokens, workspace denial, client-role rejection, size limits, cross-tenant
snapshot denial (including a storage adapter that ignores tenancy), and patched customer
connection paths. Sensitive unsupported SQL is absent from captured logs and diagnostics text.

## Reproducible performance evidence

Run `python scripts/development/benchmark_sql_diagnostics.py`. Each fixture has one warm-up,
20 uninstrumented latency samples and a separate single-run tracemalloc peak measurement.
The fixtures are deterministic and committed in that script; measurements are host-dependent,
not a latency SLA or database performance estimate. No schema snapshot is used, so status is
PARTIAL because schema rules are NOT_EVALUATED. Tracemalloc measures Python allocations only,
excluding full process RSS, native allocations and prior allocations.

| Fixture | UTF-8 bytes | Median ms | Maximum ms | Python allocation peak bytes |
| --- | --- | --- | --- | --- |
| small | 36 | 0.658 | 1.857 | 31610 |
| medium | 105 | 1.865 | 19.021 | 50549 |
| large_multi_cte | 921 | 8.329 | 11.402 | 315356 |
| deeply_nested | 224 | 2.691 | 3.545 | 109807 |
| multiple_statements | 758 | 7.352 | 9.266 | 222855 |

Raw benchmark output is [PHASE_10_2_BENCHMARK.json](PHASE_10_2_BENCHMARK.json).
Input/resource limits are documented in [Security](PHASE_10_2_SECURITY.md).
No claims of measured query execution cost or speed improvements are made.

## Final verification and delivery

The final focused suite includes the conservative unqualified nested-correlation fix added after
the full regression run. Ruff, Bandit, zero-drift OpenAPI, Markdown, internal documentation,
Mermaid, navigation and multilingual checks pass. Backend wheel production build passes.
The standalone embedded Phase 9 migration suite is also verified separately.

The browser session is authenticated as the repository owner. The implementation branch was
created through the Cloud Browser from Phase 10.1. Source changes are prepared for browser upload;
the final user report separately records the verified upload outcome and remote commit SHA.
No new PR is created, following the user's opening directive. No merge or release is performed.
