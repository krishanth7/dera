# MySQL Connector Troubleshooting Guide

## Common Diagnostics & Resolutions

### 1. `ConnectorAuthenticationFailedError` (Error 1045)

- **Symptom:** `Access denied for user 'username'@'host' (using password: YES)`.
- **Cause:** Incorrect username or password, or user account restricted to a different host subnet.
- **Resolution:**
  1. Confirm the credentials using standard MySQL client CLI: `mysql -u <user> -p -h <host> -P <port>`.
  2. Verify the MySQL user grant allows connection from the DERA worker IP: `SELECT user, host FROM mysql.user WHERE user = '<user>';`.
  3. Ensure the password has not expired (`password_expired = 'Y'`).

### 2. `ConnectorPermissionDeniedError` (Error 1044 / 1142)

- **Symptom:** `Access denied for user 'username'@'%' to database 'dbname'`.
- **Cause:** Insufficient schema or object permissions.
- **Resolution:**
  Grant least-privilege metadata read access:
  ```sql
  GRANT SELECT, SHOW VIEW ON `dbname`.* TO 'dera_user'@'%';
  FLUSH PRIVILEGES;
  ```

### 3. `ConnectorTLSError` (Error 2026)

- **Symptom:** `SSL connection error: certificate verify failed`.
- **Cause:** CA certificate mismatch, expired server certificate, or hostname mismatch.
- **Resolution:**
  1. For self-signed certificates or internal corporate CAs, specify `ca_cert_path` pointing to the trusted PEM bundle.
  2. If connecting via internal IP rather than hostname, use `ssl_mode='verify-ca'` instead of `verify-full`.

### 4. `ConnectorTimeoutError` (Error 3024)

- **Symptom:** `MySQL query execution exceeded timeout`.
- **Cause:** Large database metadata catalogs or network latency exceeding `query_timeout_seconds`.
- **Resolution:**
  Increase query timeout in configuration:
  ```python
  from dera_connectors.configuration import TimeoutSettings

  config = MySqlConnectorConfig(
      database="large_db",
      host="db.example.com",
      timeouts=TimeoutSettings(query_timeout_seconds=60.0),
  )
  ```

### 5. `ConnectorSecurityViolationError` (SSRF Violation)

- **Symptom:** `Connection target '169.254.169.254' rejected by SSRF egress policy`.
- **Cause:** Target address points to prohibited cloud metadata or loopback services.
- **Resolution:** Provide an authorized external or VPC database endpoint.
