# Database Adapter Development Guide

## Overview

This guide instructs engineers on developing new database-specific adapters for DERA (Phases 5.2 through 5.4).

## Step-by-Step Implementation

1. **Implement `DatabaseConnector`:**
   - Subclass or implement `DatabaseConnector` protocol methods.
   - Use async drivers (`asyncpg` for PostgreSQL, `aiosqlite` for SQLite, `asyncmy` for MySQL).
   - Use `ConnectionLifecycle` to manage states.

2. **Enforce Read-Only Connection Directives:**
   - Set connection read-only flags immediately upon connecting:
     - PostgreSQL: `await conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;")`
     - SQLite: `await conn.execute("PRAGMA query_only = ON;")`
     - MySQL: `await conn.execute("SET SESSION TRANSACTION READ ONLY;")`

3. **Map Internal Errors to `ConnectorError`:**
   - Catch driver-specific exceptions (`asyncpg.PostgresError`, `aiosqlite.OperationalError`) and raise corresponding DERA exceptions (`ConnectorUnavailableError`, `ConnectorPermissionDeniedError`, etc.).

4. **Register Adapter in `ConnectorRegistry`:**
   - In your adapter module:
     ```python
     default_connector_registry.register(DatabaseEngine.POSTGRESQL, PostgresConnector)
     ```

5. **Pass the Conformance Suite:**
   - Subclass `BaseConnectorConformanceTests` in your test file and ensure all tests pass.
