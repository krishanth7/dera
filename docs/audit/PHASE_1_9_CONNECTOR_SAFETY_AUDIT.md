# Phase 1–9 Database Connector Safety & SSRF Audit
**Document ID:** `DERA-AUDIT-CONNECTOR-SAFETY`  
**Scope:** PostgreSQL, Supabase, SQLite, MySQL, and MariaDB Connectors  
**Source Directory:** `packages/core/src/dera/connectors/`  
**Date:** 2026-11-01  
**Audit Status:** **PASS (Fully Verified)**  

---

## 1. Architectural Mandate & Threat Model

DERA operates exclusively as a **read-only database reverse-engineering, diagnostic, and planning engine**.

Under no circumstances does DERA:
- Execute `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, `DROP`, or `ALTER` statements against customer databases.
- Automatically deploy or execute compiled migration SQL against customer databases.
- Allow outbound network requests to internal cloud metadata IP addresses (`169.254.169.254`) or unauthorized loopback/link-local networks.
- Serialize or leak cleartext database credentials in error messages, API responses, or logs.

---

## 2. Dialect Safety Controls

### 2.1 PostgreSQL & Supabase (`packages/core/src/dera/connectors/postgres.py`)
- **Connection Mode:** Sessions initialized with `SET TRANSACTION READ ONLY;`.
- **Introspection Strategy:** Pure SQL queries targeting `information_schema` and system catalog views (`pg_catalog.pg_class`, `pg_catalog.pg_attribute`, `pg_catalog.pg_constraint`).
- **Connection Parameter Sanitization:** Client options prohibiting mutation flags; timeouts configured on all network operations (`statement_timeout=30000`).

### 2.2 SQLite (`packages/core/src/dera/connectors/sqlite.py`)
- **Connection Mode:** Opened via URI with strict `mode=ro` flag (`file:path?mode=ro`).
- **File System Safeguards:** File-based introspection verified offline; file locks preserved without mutation.
- **Introspection Strategy:** `PRAGMA table_info`, `PRAGMA foreign_key_list`, `PRAGMA index_list`.

### 2.3 MySQL & MariaDB (`packages/core/src/dera/connectors/mysql.py`)
- **Connection Mode:** Read-only session attributes (`SET SESSION TRANSACTION READ ONLY;`).
- **Introspection Strategy:** Queries targeting `information_schema.TABLES`, `information_schema.COLUMNS`, `information_schema.KEY_COLUMN_USAGE`, `information_schema.STATISTICS`.
- **Driver Safeguards:** Autocommit disabled, safe read timeouts enforced.

---

## 3. Server-Side Request Forgery (SSRF) Defenses

Implemented in `packages/core/src/dera/connectors/safety.py`:
1. **Target Address Resolution:** Hostnames are resolved to IPv4 and IPv6 addresses prior to socket initialization.
2. **Blocked IP Ranges:**
   - Cloud Instance Metadata Service (AWS/GCP/Azure): `169.254.169.254`, `fd00:ec2::254`
   - Loopback Addresses (when in production mode): `127.0.0.0/8`, `::1`
   - Link-Local Networks: `169.254.0.0/16`, `fe80::/10`
   - Private Ranges (configurable by enterprise policy): `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
3. **Fail-Closed Resolution:** Unresolvable hosts or addresses falling within prohibited subnets immediately abort connection establishment with `ConnectorSafetyError`.

---

## 4. Empirical Test Verification

Verified by automated connector safety test suites:
- Prohibited mutations (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`) attempted against isolated test databases fail closed.
- Metadata endpoints (`http://169.254.169.254/`) rejected immediately by connection validator.
- Database passwords masked in logs and exceptions via `redact_credentials()`.

**Qualification Status:** **PASS**
