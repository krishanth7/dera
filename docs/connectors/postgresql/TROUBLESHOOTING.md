# PostgreSQL Connector Troubleshooting Guide

## Common Diagnostics & Resolutions

### 1. `ConnectorAuthenticationFailedError: (28P01)`
- **Symptom:** Authentication failed for user.
- **Cause:** Incorrect username or password.
- **Resolution:**
  - Verify credentials with a direct test using `test_connection()`.
  - For Supabase connection poolers, ensure username includes the project ref (e.g. `postgres.[project_ref]`).

### 2. `ConnectorTimeoutError: (57014)`
- **Symptom:** Statement cancelled or timed out.
- **Cause:** Large database catalog or heavy lock contention in customer database exceeding `statement_timeout_ms`.
- **Resolution:**
  - Increase `statement_timeout_ms` in `PostgresConnectorConfig` (up to 600,000 ms).
  - Use `schema` parameter to narrow inspection scope to a single schema (e.g. `list_tables(schema="public")`).

### 3. Prepared Statement Failures on Supabase (PgBouncer)
- **Symptom:** `asyncpg.exceptions.InvalidSQLStatementNameError: prepared statement "__asyncpg_stmt_1__" does not exist`.
- **Cause:** Transaction-mode connection poolers (PgBouncer) do not support named prepared statements across pooled sessions.
- **Resolution:**
  - Set `supabase_pooler_mode=SupabasePoolerMode.TRANSACTION`.
  - This automatically configures `statement_cache_size=0`, executing queries in simple protocol mode.

### 4. `ConnectorTLSError: certificate verify failed`
- **Symptom:** SSL handshake fails during connection.
- **Cause:** Self-signed certificates, missing intermediate CA, or hostname mismatch.
- **Resolution:**
  - Provide path to root CA certificate in `tls.ca_cert_path`.
  - If using `verify-ca` or `verify-full`, ensure server certificate matches hostname.
  - In development environments, use `tls.ssl_mode = "require"` to encrypt transport without verifying hostname.

### 5. `SSRFSecurityViolationError`
- **Symptom:** Target resolves to link-local or loopback address.
- **Cause:** Connecting to loopback (`127.0.0.1`) without enabling `allow_loopback=True`, or attempting to target cloud metadata IP (`169.254.169.254`).
- **Resolution:**
  - Cloud metadata targets (`169.254.169.254`) are strictly forbidden.
  - In unit tests and local development environments, pass `allow_loopback=True` to permit localhost connections.
