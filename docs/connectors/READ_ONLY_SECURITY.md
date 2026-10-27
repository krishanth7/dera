# Read-Only Security Policy & SSRF Defenses

## Two-Tier Read-Only Defense

1. **Protocol & API Layer:**
   - The `DatabaseConnector` protocol defines zero mutation methods (`execute_sql`, `drop_table`, `insert`, etc.).
   - Static query analysis via `validate_read_only_sql` rejects queries containing `DROP`, `TRUNCATE`, `ALTER`, `CREATE`, `INSERT`, `UPDATE`, `DELETE`, `GRANT`, `REVOKE`, `REPLACE`, `EXECUTE`, or `LOCK`.

2. **Database Engine Session Layer (Future Adapters):**
   - SQLite: `PRAGMA query_only = ON;`
   - PostgreSQL: `SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;`
   - MySQL: `SET SESSION TRANSACTION READ ONLY;`

## SSRF and Network Target Validation

Connectors prevent Server-Side Request Forgery (`packages/connectors/src/dera_connectors/security.py`):
- **Cloud Metadata Protection:** Unconditionally blocks `169.254.169.254`, `metadata.google.internal`, and loopback addresses (`127.0.0.1`, `::1`).
- **Private Network Policy:** Rejects RFC 1918 addresses (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) unless explicitly allowed in tenant network policy.
