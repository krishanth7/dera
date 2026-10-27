# DERA SQLite Connector Troubleshooting Guide

## Diagnostic Taxonomy

The SQLite connector maps errors into Phase 5.1 `ConnectorError` subclasses. Below are common error scenarios, their root causes, and resolutions.

---

## Common Scenarios & Resolutions

### 1. `ConnectorSecurityViolationError`: Path Escapes Approved Storage Roots
- **Message:** `"Database path '...' escapes approved storage roots: ['...']"`
- **Cause:** The target file path resolved outside the authorized directory, or contained traversal characters (`..`).
- **Resolution:** Verify that `approved_storage_roots` contains the directory hosting the SQLite database.

### 2. `ConnectorUnavailableError`: Target Database Not Found
- **Message:** `"Database file does not exist: [REDACTED_PATH]"`
- **Cause:** The target file does not exist at the resolved filesystem path.
- **Resolution:** Verify file existence and that the running process has filesystem read permissions.

### 3. `sqlite3.OperationalError: attempt to write a readonly database`
- **Cause:** An operation attempted to execute a write transaction (e.g. `INSERT`, `CREATE TABLE`).
- **Resolution:** The connector is strictly read-only by design. DERA never performs schema mutations or data writes.

### 4. `ConnectorTimeoutError`: Busy Timeout Expired
- **Message:** `"SQLite operation timed out: database is locked"`
- **Cause:** Another external process holds an exclusive write lock on the SQLite database in `DELETE` journal mode.
- **Resolution:** Switch the source database to `WAL` journal mode (`PRAGMA journal_mode = WAL;`) or increase `busy_timeout_ms`.
