# DERA Database Connectors Documentation Index

> **Package:** `packages/connectors`  
> **Maintainer:** Krishanth  
> **Status:** Active Documentation Hub  
> **Last Verified:** 2026-10-26 (Commit `e550fdd`)  

---

## 1. Connectors Specifications Index

| Document | Purpose | Status |
|---|---|---|
| [**CONNECTOR_ARCHITECTURE.md**](CONNECTOR_ARCHITECTURE.md) | `BaseConnector` design, lifecycle management, and static query mutation safety | **Active** |
| [**CAPABILITY_MATRIX.md**](CAPABILITY_MATRIX.md) | Engine-by-engine support matrix covering tables, columns, keys, indexes, and test coverage | **Active** |

---

## 2. Key Connector Invariants

1. **Absolute Read-Only Safety:** Any query matching mutating keywords (`DROP`, `ALTER`, `TRUNCATE`, `INSERT`, `UPDATE`, `DELETE`, `GRANT`, `REVOKE`) is rejected by static regex validation before execution.
2. **Session-Level Read-Only Directives:** Every database connection executes `PRAGMA query_only = ON;` (SQLite) or `SET TRANSACTION READ ONLY;` (PostgreSQL) upon opening.
3. **Metadata Exclusivity:** Introspection queries only target system catalogs; user data rows are never extracted, transmitted, or cached.
4. **Credential Isolation:** Database credentials remain strictly on the backend and are masked in logging and string representations.

---

## 3. Related Documentation Hubs

- [Root Documentation Hub](../README.md)
- [System Architecture Overview](../architecture/SYSTEM_OVERVIEW.md)
- [Core Engine Guide](../core/README.md)
- [Shared Contracts](../contracts/README.md)
- [Database Security Specification](../security/DATABASE_SECURITY.md)
