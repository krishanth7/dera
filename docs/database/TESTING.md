# DERA Database Testing Guide

## 1. Test Architecture

The DERA database test suite is divided into focused layers in `tests/database/` and `tests/integration/`:

| Test Suite | File Path | Focus |
| :--- | :--- | :--- |
| **Engine Tests** | `tests/database/test_engine.py` | Factory validation, pool settings, URL parsing, credential masking. |
| **Session Tests** | `tests/database/test_sessions.py` | Session creation, dependency injection lifecycle, isolation. |
| **Transaction Tests** | `tests/database/test_transactions.py` | `transaction_scope`, atomic commit, rollback on exception, savepoints. |
| **Constraint Tests** | `tests/database/test_constraints.py` | Primary key uniqueness, NOT NULL enforcement, timestamps. |
| **Health Probe Tests** | `tests/database/test_database_health.py` | `SELECT 1;` health check, timeouts, `/health/ready` probe integration. |
| **Error Handling Tests** | `tests/database/test_error_handling.py` | Sanitization of credentials, parameter redaction, error mapping. |
| **Repository Tests** | `tests/database/test_repositories.py` | `PlatformMetadataRepository` CRUD, upserts, ordered listing. |
| **Migration Tests** | `tests/database/test_migrations.py` | Alembic revision heads, script syntax, offline SQL generation. |
| **Integration Tests** | `tests/integration/test_platform_database.py` | End-to-end integration against live PostgreSQL (or async engine). |

---

## 2. Running Database Tests

Run all database unit and integration tests:

```bash
python scripts/ci/test_reporter.py --test-dir tests/database/
```

Run tests against a local PostgreSQL instance:

```bash
DERA_PLATFORM_DATABASE_URL="postgresql+asyncpg://dera_user:dera_password@127.0.0.1:5432/dera_platform" python -m unittest tests/integration/test_platform_database.py
```
