# PostgreSQL Connector Testing Guide

## Test Architecture

The PostgreSQL connector test suite comprises four testing tiers:

1. **Configuration & Pooler Tests (`tests/connectors/postgresql/test_configuration.py`):**
   - Validates `PostgresConnectorConfig` defaults.
   - Tests automatic domain detection for Supabase hosts (`*.supabase.co`, `*.pooler.supabase.com`).
   - Verifies statement cache disabling (`statement_cache_size=0`) in transaction pooler mode.
2. **Error Classification Tests (`tests/connectors/postgresql/test_errors.py`):**
   - Tests SQLSTATE error mapping (`28P01` -> `ConnectorAuthenticationFailedError`, `42501` -> `ConnectorPermissionDeniedError`, `57014` -> `ConnectorTimeoutError`, `25006` -> `ConnectorSecurityViolationError`).
   - Verifies credential masking and SSL/TLS error categorization.
3. **Catalog Query & Unit Tests (`tests/connectors/postgresql/test_catalog_queries.py`):**
   - Asserts all catalog queries are read-only using `validate_read_only_sql`.
   - Tests extraction of schemas, tables, columns, primary keys, foreign keys, unique constraints, check constraints, indexes, views, sequences, and partitions.
4. **Adapter Conformance Tests (`tests/connectors/postgresql/test_postgres_adapter.py`):**
   - Executes the Phase 5.1 `BaseConnectorConformanceTests` suite verifying protocol adherence, async lifecycle states, cancellation handling, and determinism.
5. **Security Qualification Tests (`tests/connectors/postgresql/test_postgres_security.py`):**
   - Tests SSRF defenses (blocking `169.254.169.254` and loopbacks by default).
   - Tests session read-only transaction command execution.
   - Verifies mutation query rejection.
6. **Live Integration Tests (`tests/integration/postgresql/test_postgres_live.py`):**
   - End-to-end integration tests executing against real PostgreSQL (e.g. CI PostgreSQL 16 container).
   - Tests multi-schema fixtures, composite primary keys, composite foreign keys, partial indexes, views, materialized views, sequences, partitions, and unicode table names.

---

## Running the Tests Locally

```bash
# Run PostgreSQL connector unit and conformance tests
python -m unittest discover -s tests/connectors/postgresql -p "test_*.py"

# Run PostgreSQL live integration suite (requires running local PostgreSQL on port 5432)
python -m unittest tests/integration/postgresql/test_postgres_live.py

# Run full project test runner
python scripts/ci/test_reporter.py --test-dir tests/
```
