# Connector Security Threat Model

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Milestone:** Phase 5.6 — Read-Only Enforcement, Timeouts & Safety  
**Auditor:** Principal Application Security Architect & DevSecOps Engineering Team  

---

## 1. Overview & Trust Boundaries

DERA's connector subsystem establishes direct network and in-process connections to customer database instances (PostgreSQL, Supabase PostgreSQL, SQLite, MySQL, and MariaDB) to introspect database catalogs, schema definitions, and table structures.

Because connectors bridge the DERA application gateway with external customer database infrastructure, strict trust boundaries must be maintained:

```text
+-------------------------------------------------------------------------------+
|                            Untrusted API Client / Web UI                      |
+-------------------------------------------------------------------------------+
                                        | (HTTPS / Bearer JWT)
                                        v
+-------------------------------------------------------------------------------+
| [Trust Boundary 1: API Gateway & Workspace Authorization]                     |
| - Authentication & Token Verification (Phase 4.4)                             |
| - Workspace Membership & RBAC Enforcement (Phase 4.4)                         |
| - Request Context Creation (workspace_id, user_id, correlation_id)            |
+-------------------------------------------------------------------------------+
                                        | (Internal Authorized Context)
                                        v
+-------------------------------------------------------------------------------+
| [Trust Boundary 2: Connector Security Policy]                                 |
| - Destination & SSRF Pre-flight Validation (destinations.py)                  |
| - Encapsulated Credential Resolution (credentials.py)                         |
| - Monotonic Deadline Allocation & Timeout Budget (timeouts.py)                |
| - Cooperative Cancellation Propagation (cancellation.py)                      |
| - Metadata Query Allowlist & Lexical Analysis (readonly.py, query_policy.py)   |
| - Resource Limit Caps (resource_limits.py)                                    |
+-------------------------------------------------------------------------------+
                                        | (Hardened, Parameterized TCP / IPC)
                                        v
+-------------------------------------------------------------------------------+
| [Trust Boundary 3: External Customer Database Engine]                         |
| - PostgreSQL / Supabase / SQLite / MySQL / MariaDB                            |
| - Catalog Introspection Tables (information_schema, pg_catalog, sqlite_master)|
+-------------------------------------------------------------------------------+
```

---

## 2. Threat Classification & Mitigation Matrix

The connector threat model evaluates 18 threat vectors across STRIDE categories:

| Threat ID | Threat Category | Threat Description | Inherent Risk | Mitigating Security Controls | Residual Risk | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **THREAT-01** | **Tampering** | Unauthorized customer database writes (DDL/DML injection via catalog query endpoints). | **CRITICAL** | Static lexical inspection (`validate_read_only_sql`), comment stripping, session read-only mode (`SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY`). | **LOW** | `test_read_only_enforcement.py` (8/8 pass). |
| **THREAT-02** | **Elevation** | Arbitrary SQL injection through unvalidated table/column/schema filters. | **CRITICAL** | Parameter binding for all values, identifier quoting/unquoting via `identifiers.py`, query allowlist registry (`ApprovedMetadataQueryRegistry`). | **LOW** | `test_query_allowlist.py` (6/6 pass). |
| **THREAT-03** | **Information Disclosure** | Database credential exposure in structured application logs, error messages, or diagnostic dumps. | **CRITICAL** | Recursive redaction (`sanitize_diagnostics`), regex masking (`mask_sensitive_strings`), opaque `DatabaseCredentials` repr. | **LOW** | `test_credential_handling.py` (4/4 pass). |
| **THREAT-04** | **Tampering** | Server-Side Request Forgery (SSRF) targeting internal VPC services or cloud metadata endpoints (`169.254.169.254`). | **CRITICAL** | Destination validation (`validate_network_target`), link-local/loopback rejection, cloud metadata hostname blocking, dangerous port blocking. | **LOW** | `test_ssrf_egress_protection.py` (6/6 pass). |
| **THREAT-05** | **Tampering** | DNS Rebinding attack shifting target IP from public validation IP to internal private IP during connection. | **HIGH** | DNS resolution validation (`resolve_and_validate_destination`) and destination IP pinning verification (`verify_destination_pinning`). | **LOW** | `test_dns_rebinding_defense.py` (2/2 pass). |
| **THREAT-06** | **Information Disclosure** | Unauthorized internal network port scanning via connector connection error diagnostics. | **HIGH** | Restricted error mapping (`map_postgres_error`, `map_mysql_family_error`), generic error categorization, absence of internal topology details. | **LOW** | `test_connector_security.py` (6/6 pass). |
| **THREAT-07** | **Tampering** | TLS downgrade attack (falling back to unencrypted plaintext transport). | **HIGH** | Configurable minimum TLS version (TLS 1.2+ default), explicit SSLContext generation (`create_default_context`), hostname verification in `verify-full`. | **LOW** | `test_postgres_security.py` (5/5 pass). |
| **THREAT-08** | **Tampering** | TLS certificate spoofing (invalid or untrusted CA certificate). | **HIGH** | Default `ssl.CERT_REQUIRED` in verification modes, explicit CA bundle loading, rejection of self-signed certs unless configured. | **LOW** | `test_postgres_security.py` (5/5 pass). |
| **THREAT-09** | **Elevation** | SQLite filesystem directory traversal accessing host operating system files (e.g. `/etc/passwd`). | **CRITICAL** | Canonical realpath resolution (`os.path.realpath`), approved storage root containment (`os.path.commonpath`), null byte rejection. | **LOW** | `test_sqlite_isolation.py` (7/7 pass). |
| **THREAT-10** | **Elevation** | Symlink escape attack pointing a harmless SQLite file to sensitive host storage. | **HIGH** | Symlink traversal resolution during `realpath` validation; resolved real path must reside strictly within approved root. | **LOW** | `test_sqlite_isolation.py` (7/7 pass). |
| **THREAT-11** | **Information Disclosure** | Cross-workspace metadata or connection configuration access in multi-tenant environments. | **CRITICAL** | Mandatory tenant authorization (`validate_workspace_authorization`) executed before secret resolution or query execution. | **LOW** | `test_workspace_isolation.py` (4/4 pass). |
| **THREAT-12** | **Denial of Service** | Connection pool exhaustion via leaked or unclosed database connections. | **HIGH** | Idempotent cleanup in `close()`, try/finally context management, connection timeout caps, pool size bounds. | **LOW** | `test_lifecycle.py` (10/10 pass). |
| **THREAT-13** | **Denial of Service** | Unbounded long-running catalog queries causing driver execution hangs or memory bloat. | **HIGH** | Centralized `DeadlineTracker` enforcing overall inspection budgets (default 120s), driver statement timeouts (`statement_timeout = 30000`). | **LOW** | `test_timeouts_and_cancellation.py` (5/5 pass). |
| **THREAT-14** | **Information Disclosure** | Metadata exfiltration by crafting queries that extract customer table data rows. | **HIGH** | Absence of arbitrary SQL endpoints; execution restricted strictly to catalog introspection views (`information_schema`, `pg_catalog`). | **LOW** | `test_query_allowlist.py` (6/6 pass). |
| **THREAT-15** | **Denial of Service** | Cancellation failure leaving orphaned long-running transactions active on customer database. | **MEDIUM** | Cooperative `EnhancedCancellationToken` registering driver interrupt callbacks and transaction rollbacks. | **LOW** | `test_timeouts_and_cancellation.py` (5/5 pass). |
| **THREAT-16** | **Elevation** | Database account privilege escalation via `GRANT` or administrative stored procedures. | **HIGH** | Static keyword blocking (`GRANT`, `REVOKE`, `xp_cmdshell`, `sys_eval`), least-privilege role recommendation documentation. | **LOW** | `test_read_only_enforcement.py` (8/8 pass). |
| **THREAT-17** | **Tampering** | Malicious database metadata payload (extreme identifier lengths, control characters, null bytes). | **MEDIUM** | Bound checking (`ConnectorResourceLimits`), identifier length capped at 1,024 chars, definition length capped at 1MB. | **LOW** | `test_resource_limits.py` (5/5 pass). |
| **THREAT-18** | **Tampering** | Unsafe database driver behavior (e.g. SQLite loadable extensions, automatic remote file loading). | **HIGH** | Explicit restriction of extension loading, SQLite URI forced to `mode=ro`, safe driver options only. | **LOW** | `test_sqlite_isolation.py` (7/7 pass). |

---

## 3. Residual Risks & Operational Guidance

1. **Host-Level Network Egress Controls:** While application-level SSRF defenses block cloud metadata and private IP ranges, production deployments should enforce OS-level egress firewalls (e.g. AWS Security Groups, iptables, or Cilium egress policies) as defense-in-depth against kernel-level bypasses.
2. **Customer Database Role Privileges:** Connector session read-only enforcement (`SET SESSION TRANSACTION READ ONLY`) prevents inadvertent mutations. However, customer database administrators must provision dedicated, read-only database roles granting `SELECT` only on catalog tables, with zero permissions on customer application tables.
3. **Database Server Resource Consumption:** Catalog introspection queries across schemas with hundreds of thousands of partitions or columns can induce CPU load on customer database servers. DERA enforces row caps (`max_result_rows = 50,000`) and statement timeouts (`30s`) to prevent database server strain.
