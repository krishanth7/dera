## Summary

Phase 4.3 delivers DERA's authoritative internal platform PostgreSQL persistence foundation, establishing asynchronous PostgreSQL 16+ persistence via SQLAlchemy 2.x, connection pooling (`AsyncAdaptedQueuePool`), typed declarative models (`Base`), request-scoped session lifecycle (`get_db_session`), explicit transaction boundaries (`transaction_scope`), Alembic migrations with async runner, database health and readiness probe integration (`/health/ready`), credential masking, and comprehensive operational documentation.

> **CRITICAL ARCHITECTURAL SEPARATION INVARIANT**:
> The internal platform database (`dera_platform`) is strictly separated from externally inspected customer databases. No Phase 4.3 migration may execute against customer databases, and no customer connection is shared with the platform database.
> **ZERO AI INVARIANT**:
> Pure deterministic persistence without LLMs, GenAI models, or probabilistic inference.

## Change Type

- [x] Feature (`feat`)
- [ ] Bug fix (`fix`)
- [x] Documentation (`docs`)
- [ ] Refactor (`refactor`)
- [ ] Performance (`perf`)
- [x] Test improvement (`test`)
- [x] CI/CD or Build (`ci`, `build`)
- [x] Security enhancement (`security`)
- [ ] Breaking change (`!`)

## Related Issues

Closes #39

## Implementation Details

- **SQLAlchemy 2.x Base**: `Base(DeclarativeBase)` with explicit, deterministic PostgreSQL naming conventions (`POSTGRES_NAMING_CONVENTION`) for PKs, FKs, unique constraints, check constraints, and indexes.
- **Async Engine Factory**: `create_database_engine` with `AsyncAdaptedQueuePool`, configurable pool parameters (`pool_size`, `max_overflow`, `pool_timeout`, `pool_recycle`), socket timeouts, and safe lifecycle disposal.
- **Session & Transaction Lifecycle**: `create_session_factory` and `transaction_scope` ensuring atomic commits and automatic rollback on failure without connection leaks.
- **FastAPI Dependency Injection**: `get_db_session` provides request-scoped session injection with guaranteed disposal.
- **Initial Schema**: `PlatformMetadata` ORM model (`dera_platform_metadata`) and typed `PlatformMetadataRepository`.
- **Alembic Migrations**: Async environment (`migrations/env.py`, `alembic.ini`) with initial revision `001_platform_metadata`.
- **Health Integration**: Bounded `SELECT 1;` connectivity check wired into `/health/ready` probe.
- **Security & Sanitization**: Masked connection URLs and sanitized database error messages preventing credential/parameter leakage.
- **Local Dev Setup**: Added `docker-compose.db.yml` for PostgreSQL 16 local development.
- **CI Enhancements**: Added PostgreSQL 16 service container tests and migration re-upgrade verification in `.github/workflows/ci.yml`.

## Testing

- [x] Relevant tests passed (`python scripts/development/dev.py all` or `test`)
- [ ] Tests not applicable — explanation below (e.g., documentation, typo fix, governance)
- [ ] Tests not run / blocked — explanation below

**Test evidence & notes:**
```text
==================================================
DERA Test Execution Telemetry
==================================================
Total Tests Executed: 260
Passed:               260
Failures:             0
Errors:               0
Skipped:              0
Execution Duration:   5.956s
JUnit XML Report:     reports/test-results.xml
JSON Summary:         reports/test-summary.json
==================================================
```
- Executed 260/260 tests across engine, session, transaction, constraint, health, error handling, repository, migration, and integration test suites.
- Verified Ruff linting (`ruff check`) and formatting (`ruff format --check`).
- Verified bytecode compilation (`compileall`).
- Verified Bandit SAST security scan (0 findings).
- Verified OpenAPI zero-drift validation (`validate_openapi.py --check`).
- Verified TypeScript compilation (`tsc --noEmit`).

## Documentation Impact

- [x] Documentation in `docs/` updated or verified where required
- [x] Documentation validation passed (`npm run docs:check`)
- [ ] No documentation updates required for this change

**Documentation updates:**
- Authored 10 authoritative database guides in `docs/database/`:
  `README.md`, `ARCHITECTURE.md`, `CONFIGURATION.md`, `LOCAL_POSTGRESQL.md`, `SQLALCHEMY_GUIDE.md`, `MIGRATION_POLICY.md`, `TRANSACTION_POLICY.md`, `SECURITY_AND_ROLES.md`, `TESTING.md`, `RECOVERY.md`.
- Authored baseline audit `docs/audit/PHASE_4_3_DATABASE_BASELINE.md` and acceptance report `docs/audit/PHASE_4_3_DATABASE_ACCEPTANCE.md`.
- Updated `docs/README.md` and `docs/audit/README.md`.
- Passed documentation validation across 176 markdown files and 70 Mermaid diagrams.

## Security Impact & Deterministic Engineering

- [x] **Strict Non-AI Policy:** Verified zero generative AI, LLM, or external inference APIs are introduced.
- [x] **Database Safety:** Verified all database connector operations enforce read-only introspection without data modification.
- [x] **Credential Protection:** Confirmed that no production credentials, passwords, or `.env` secrets are committed.
- [x] **Least Privilege:** Validated that permissions and access boundaries are minimized.
- [ ] **No Security Impact:** Change does not affect database connections, security boundaries, or credentials.

## Breaking Changes

- [x] No breaking changes.
- [ ] Breaking change introduced (detailed explanation and migration path below):

## Contributor Checklist

- [x] My code adheres to the project's coding standards (PEP 8, TypeScript strict mode).
- [x] My branch is rebased on the latest `main` branch.
- [x] The PR title follows [Conventional Commits](https://www.conventionalcommits.org/) (`feat(database): complete Phase 4.3 PostgreSQL and migration foundation`).
- [x] No unrelated changes or accidental files are included.
