# Read-Only Enforcement & Query Allowlist Policy

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Milestone:** Phase 5.6 — Read-Only Enforcement, Timeouts & Safety  
**Auditor:** Principal Application Security Architect & DevSecOps Engineering Team  

---

## 1. Principles of Read-Only Operations

DERA is designed to **understand every schema and engineer every change**, but it inspects customer databases in a strictly **read-only** capacity. DERA never modifies customer application data, never executes database migrations directly from inspection endpoints, and never invokes mutating stored procedures.

To enforce this invariant, DERA combines two independent layers:
1. **Static Lexical & Keyword Interception:** Real-time query analysis that detects and blocks mutation statements before they reach the database driver.
2. **Session-Level Engine Enforcement:** Driver connection parameters that configure the database server session into read-only transaction state.

---

## 2. Lexical & Comment-Aware Analysis

Static inspection is implemented in [`dera_connectors.security.readonly`](../../packages/connectors/src/dera_connectors/security/readonly.py):

```python
from dera_connectors.security import validate_read_only_sql, ReadOnlySecurityViolationError

try:
    validate_read_only_sql("DROP TABLE users;")
except ReadOnlySecurityViolationError as exc:
    print(f"Blocked: {exc}")
```

### Prohibited Mutation Tokens

The normalizer rejects any SQL statement containing the following keywords outside of quoted string literals:

```text
DROP, TRUNCATE, ALTER, CREATE, INSERT, UPDATE, DELETE,
GRANT, REVOKE, REPLACE, EXEC, EXECUTE, VACUUM, REINDEX,
LOCK, CALL, MERGE, UPSERT, RENAME, SHUTDOWN, LOAD, ATTACH, DETACH
```

### Dangerous Functions & Procedures

Administrative functions that could terminate backends, cancel sessions, or interact with server filesystems are prohibited:

```text
pg_terminate_backend, pg_cancel_backend, pg_read_file, pg_write_file,
load_extension, dblink_exec, xp_cmdshell, sys_eval, sys_exec
```

### File I/O Exfiltration

File import and export commands are intercepted:

```text
INTO OUTFILE, INTO DUMPFILE, COPY ... FROM
```

### Comment Stripping & String Literal Immunity

Attacking query parsers via SQL comments (`/* comment */`, `-- line`, `# line`) is neutralized by stripping comments before keyword analysis. Furthermore, single-quoted string literals (e.g. `'drop'`) are replaced with empty placeholders during lexical analysis, ensuring queries such as `SELECT * FROM tasks WHERE status = 'drop'` pass without false-positive rejections.

---

## 3. Approved Metadata Query Registry

All database queries executed by DERA connectors must be registered in the [`ApprovedMetadataQueryRegistry`](../../packages/connectors/src/dera_connectors/security/query_policy.py).

Every registered query defines:
- **`operation_id`:** Unique dot-delimited identifier (e.g. `postgres.catalog.tables`, `sqlite.catalog.columns`).
- **`supported_engines`:** Set of compatible engine names (`postgresql`, `supabase`, `sqlite`, `mysql`, `mariadb`).
- **`description`:** Human-readable summary of the inspection goal.
- **`allowed_parameters`:** Whitelist of allowed parameter keys (e.g. `schema_name`, `table_name`).
- **`max_result_rows`:** Maximum allowed rows returned by the query (default 50,000).
- **`timeout_seconds`:** Per-query execution timeout budget (default 30.0s).

Unregistered query operations or queries executed against incompatible engines are rejected immediately with `UnauthorizedQueryError`.
