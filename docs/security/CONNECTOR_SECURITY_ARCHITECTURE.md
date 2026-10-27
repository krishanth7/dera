# Connector Security Architecture

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Milestone:** Phase 5.6 — Read-Only Enforcement, Timeouts & Safety  
**Auditor:** Principal Application Security Architect & DevSecOps Engineering Team  

---

## 1. Architectural Philosophy

DERA's connector subsystem operates on the principle of **defense in depth**: no single security boundary is assumed to be infallible. Security invariants are enforced symmetrically at the API gateway, the connector security orchestrator, the driver connection manager, and the target database session.

```text
+---------------------------------------------------------------------------------+
|                                 Layer 1: API Gateway                            |
|             Authentication (JWT), Workspace RBAC, Context Creation              |
+---------------------------------------------------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------+
|                         Layer 2: Connector Security Policy                      |
|  - Tenant Authorization (Caller Workspace == Target Workspace)                  |
|  - Destination Validation (SSRF, Cloud Metadata, Private Egress, Port Blocks)   |
|  - Credential Protection (Encapsulation, Redaction, Zero Log Leakage)           |
|  - Timeout & Deadline Management (Central Budget, Monotonic Sub-Budgets)        |
|  - Cooperative Cancellation (Parent-Child Tokens, Socket Aborts)                |
+---------------------------------------------------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------+
|                        Layer 3: Query Allowlist & Lexical Analysis              |
|  - Approved Metadata Query Registry (Pre-registered Catalog Operations)         |
|  - Read-Only Lexical Guard (Comment Stripping, DDL/DML Keyword Blocker)         |
|  - Parameter Sanitization & Safe Identifier Quoting                             |
|  - Resource Limits (Row Bounds, Identifier Bounds, Definition Size Bounds)      |
+---------------------------------------------------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------+
|                        Layer 4: Engine-Specific Connection Hardening            |
|  - PostgreSQL: asyncpg, Read-Only Transaction Mode, statement_timeout           |
|  - Supabase: Session/Transaction Pooler Compatibility, Read-Only Enforcement    |
|  - SQLite: Canonical Root Containment, Symlink Escapes, mode=ro URI Parameter   |
|  - MySQL/MariaDB: PyMySQL Thread Pool, Read-Only Session, Execution Limits      |
+---------------------------------------------------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------+
|                        Layer 5: Structured Security Audit Logging               |
|  - Zero Plaintext Credentials, Masked Diagnostics, JSON Security Events         |
+---------------------------------------------------------------------------------+
```

---

## 2. Order of Operations

To prevent time-of-check to time-of-use (TOCTOU) vulnerabilities and ensure secrets are never resolved prior to tenant authorization, connector operations must strictly follow the mandatory execution sequence:

1. **Authenticate Caller:** Verify user identity via JWT token and check account active status.
2. **Authorize Workspace:** Verify that caller's active `workspace_id` matches the owning workspace of the connection. Reject immediately with `TenantIsolationViolationError` if mismatched.
3. **Authorize Connection Reference:** Retrieve connector configuration and verify configuration schema.
4. **Validate Operation & Parameters:** Verify requested catalog operation against `ApprovedMetadataQueryRegistry`.
5. **Resolve Credentials:** Decrypt or resolve database credentials into encapsulated `DatabaseCredentials` in ephemeral memory.
6. **Validate Destination & SSRF:** Validate target host, IP literal, and port against network egress boundaries and cloud metadata blocks.
7. **Execute Approved Metadata Query:** Open socket connection with read-only session flags, enforce statement timeouts, and stream results within resource row caps.
8. **Audit Log Decision:** Record structured `SecurityAuditEvent` with duration and status (`ALLOW` or `VIOLATION`).

---

## 3. Engine-Specific Hardening Matrix

| Engine | Primary Driver | Session Security Directives | TLS Configuration | Isolation Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **PostgreSQL** | `asyncpg` | `SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;`<br>`SET statement_timeout = 30000;` | `ssl.SSLContext` with `CERT_REQUIRED` (verify-full/verify-ca) or `CERT_NONE` (require) | Catalog-only schema isolation via search path and query registry |
| **Supabase** | `asyncpg` via PgBouncer | Read-only transaction per connection; statement timeouts | TLS SNI hostname validation with Supabase root CA bundle | Workspace-scoped pool isolation |
| **SQLite** | `aiosqlite` | Forced read-only URI: `file://...?mode=ro`<br>Optional `immutable=1` | Not applicable (in-process IPC) | Canonical `realpath` containment to approved workspace storage root |
| **MySQL** | `pymysql` (async threadpool) | `SET SESSION TRANSACTION READ ONLY;`<br>`SET max_execution_time = 30000;` | `ssl.SSLContext` with TLS 1.2+ minimum; verify CA bundle | Catalog introspection restricted to `information_schema` |
| **MariaDB** | `pymysql` (async threadpool) | `SET SESSION TRANSACTION READ ONLY;`<br>`SET max_statement_time = 30;` | `ssl.SSLContext` with TLS 1.2+ minimum; verify CA bundle | Catalog introspection restricted to `information_schema` |
