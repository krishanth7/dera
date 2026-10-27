# MariaDB Connector Troubleshooting Guide

## Common Diagnostics & Resolutions

### 1. `ConnectorAuthenticationFailedError` (Error 1045)

- **Symptom:** `Access denied for user 'username'@'host' (using password: YES)`.
- **Cause:** Authentication credentials incorrect or MariaDB user account restricted to a different host.
- **Resolution:**
  Verify MariaDB grants:
  ```sql
  SELECT user, host, plugin FROM mysql.user WHERE user = 'dera_user';
  ```
  Ensure the user authentication plugin is compatible with client capabilities (e.g. `mysql_native_password` or `ed25519`).

### 2. `ConnectorPermissionDeniedError` (Error 1044 / 1142)

- **Symptom:** `Access denied for user 'username'@'%' to database 'inventory'`.
- **Cause:** Account lacks `SELECT` privileges on the target schema.
- **Resolution:**
  Grant minimal inspection privileges:
  ```sql
  GRANT SELECT, SHOW VIEW ON `inventory`.* TO 'dera_user'@'%';
  FLUSH PRIVILEGES;
  ```

### 3. `ConnectorTLSError` (Error 2026)

- **Symptom:** `SSL connection error: certificate verify failed`.
- **Cause:** CA certificate mismatch or self-signed cert on MariaDB node.
- **Resolution:**
  Configure `ca_cert_path` in `TLSSettings` to trust the MariaDB server certificate.

### 4. `ConnectorTimeoutError` (Error 3024 / Max Statement Time Exceeded)

- **Symptom:** `Query execution exceeded timeout: max_statement_time exceeded`.
- **Cause:** Complex catalog queries or high server load on MariaDB.
- **Resolution:**
  Increase query timeout in `MariaDbConnectorConfig`:
  ```python
  from dera_connectors.configuration import TimeoutSettings

  config = MariaDbConnectorConfig(
      database="inventory",
      host="mariadb.example.com",
      timeouts=TimeoutSettings(query_timeout_seconds=45.0),
  )
  ```
