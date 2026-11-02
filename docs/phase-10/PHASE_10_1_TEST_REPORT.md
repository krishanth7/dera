# Phase 10.1 Test Report

Verified 2026-11-02 in ChatGPT Work on Linux, Python 3.12.
Baseline: main `3419eaefd5ee790b35578a1dc25019f77102726c`.
Runtime: SQLGlot 30.27.0, FastAPI 0.162.0, Pydantic 2.14.1.

## Results

| Command | Result |
| --- | --- |
| `python -m pytest tests -q -rs` | 1,191 passed, 2 skipped, 407 subtests passed; 59.08s |
| `python -m pytest tests/sql_engineering tests/contracts -q` | 149 passed, 30 subtests passed; 19.77s (final API contract) |
| `python -m pytest packages/core/src/dera/migration -q` | 33 passed; 0.34s |
| `python -m ruff check packages/ apps/ tests/ scripts/` | PASS |
| `python -m ruff format --check packages/ apps/ tests/ scripts/` | PASS |
| `python scripts/ci/validate_openapi.py --check` | PASS, zero drift |
| `python scripts/ci/validate_docs.py` | PASS |
| `python scripts/ci/validate_i18n.py` | PASS, 10 languages |
| `python scripts/ci/validate_mermaid.py` | PASS, 85 diagrams |
| `python scripts/docs/generate_language_navigation.py --check` | PASS, 12 navigation documents |
| `npx --yes markdownlint-cli2 'docs/phase-10/*.md'` | PASS, zero issues |
| `python -m bandit -r packages/core/src/ apps/api/src/ -ll -q` | PASS, no medium/high findings; existing nosec warnings |
| `git diff --check` | PASS |

The final API-only change adds the documented 413 OpenAPI response; the SQL engineering
and contract suites were rerun after regenerating the snapshot. Full-suite verification
preceded that response-description-only change. CI explicitly runs the pytest milestone
corpus because the existing unittest reporter does not collect standalone pytest functions.

## Coverage and skips

The milestone corpus covers all four dialects, joins, predicates, parameters, CTEs, Unicode,
comments, subqueries, batches, mutations, DDL, transaction/admin statements, SELECT INTO,
locks, variable assignments, unknown functions, unsupported syntax, malformed SQL, byte/token/
nesting/AST limits, malformed Unicode, deterministic results and no customer execution.
API regressions use real platform sessions and an isolated SQLite platform database.
They cover anonymous/forged/expired/revoked authentication, cross-workspace access,
client role spoofing, cookie CSRF and streamed request limits.

Two existing live PostgreSQL tests are skipped: no server is reachable at 127.0.0.1:5432
(`tests/integration/postgresql/test_postgres_live.py`, lines 168 and 254). CI service containers
are expected to supply this infrastructure. SQL analysis itself never requires a live database.
Frontend checks are not run because no frontend code changed. Deprecation warnings originate
from existing Starlette/HTTPX/Alembic usage. No production load test or external deployment
verification is claimed. GitHub CI status must be checked independently after PR creation.
