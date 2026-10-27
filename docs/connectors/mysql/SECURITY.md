# MySQL Connector Security Architecture

## Overview

The DERA MySQL Connector enforces a defense-in-depth security architecture designed to prevent unauthorized mutations, SSRF egress exploits, credential leakage, and privilege escalation.

---

## 1. Read-Only Enforcement Policy

The connector operates under a strict read-only mandate. Defense-in-depth enforcement comprises:

1. **Session-Level Locking:** Immediately after establishing the database session, the connector issues:
   - `SET SESSION TRANSACTION READ ONLY;` (prevents data modification transactions)
   - `SET SESSION max_execution_time = {timeout_ms};` (enforces query execution deadline)
   - `SET SESSION sql_safe_updates = 1;` (prevents unqualified modifications)
2. **Read-Only API Contract:** The `DatabaseConnector` interface provides metadata query methods (`list_tables`, `list_columns`, etc.) and does not expose `execute_statement`, `cursor_write`, or transaction mutation hooks.
3. **Query Allowlist:** Introspection queries are pre-approved, parameterized constants in `queries.py`. Dynamic user SQL generation or interpolation is strictly prohibited.
4. **Least-Privilege Verification:** Validated via automated test suites confirming `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `ALTER`, `DROP`, `TRUNCATE`, `GRANT`, and `REVOKE` attempts are rejected.

---

## 2. Network & SSRF Defenses

Network-attached database connectors introduce Server-Side Request Forgery (SSRF) risks. DERA enforces:

- **Cloud Metadata Protection:** Outbound connection attempts to `169.254.169.254`, `metadata.google.internal`, and link-local ranges are blocked before socket creation.
- **Loopback Isolation:** Access to `127.0.0.1`, `localhost`, or `::1` is prohibited in multi-tenant SaaS mode, only permitted in local development when `allow_loopback=True` is explicitly passed.
- **Port Boundaries:** Target ports must fall strictly within valid TCP range (1–65535).
- **DNS Resolution Checks:** Destination hosts are evaluated before connection establishment.

---

## 3. TLS / Transport Encryption

The connector supports end-to-end encrypted database connections using Python's native `ssl.SSLContext`:

| Mode | Verification | Hostname Check | Description |
|---|---|---|---|
| `disable` | None | No | Plaintext transport (prohibited in production). |
| `require` | None | No | TLS encryption without verifying server certificate. |
| `verify-ca` | `CERT_REQUIRED` | No | Verifies server certificate against trusted CA bundle. |
| `verify-full` | `CERT_REQUIRED` | Yes | Verifies certificate chain and server hostname matching. |

Mutual TLS (mTLS) is supported via `client_cert_path` and `client_key_path`.

---

## 4. Credential & Diagnostic Isolation

To protect credentials:

- Passwords are typed as `pydantic.SecretStr` and excluded from `repr()`, logs, and serialization.
- Exception messages are processed through `mask_sensitive_strings` to strip passwords, API keys, and connection URIs before returning diagnostic errors.
- Internal IP addresses and system table contents are filtered from output.
