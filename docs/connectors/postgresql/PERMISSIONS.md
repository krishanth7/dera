# PostgreSQL Least-Privilege Permissions Guide

## Inspection Role Policy

To guarantee security when analyzing customer databases, DERA recommends provisioning a dedicated, unprivileged inspection role.

### Principle of Least Privilege

The inspection role requires:
1. `LOGIN` privileges to establish an authenticated session.
2. `CONNECT` permission on the target database.
3. `USAGE` on application schemas whose metadata is to be inspected.
4. Read access to system catalogs (`pg_catalog` is readable by all authenticated users by default).
5. **Zero Mutation Grants:** No `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, `CREATE`, `DROP`, or `ALTER` permissions on any customer relation or schema.

---

## Example Role Provisioning Script

```sql
-- 1. Create a dedicated read-only introspection role
CREATE ROLE dera_inspector WITH LOGIN PASSWORD 'ReplaceWithStrongGeneratedPassword';

-- 2. Grant connection to the target database
GRANT CONNECT ON DATABASE my_production_db TO dera_inspector;

-- 3. Grant schema usage for catalog visibility
GRANT USAGE ON SCHEMA public TO dera_inspector;
GRANT USAGE ON SCHEMA analytics TO dera_inspector;

-- 4. In PostgreSQL 14+, grant standard read-only membership if desired
-- GRANT pg_read_all_data TO dera_inspector; (Optional: provides visibility to all tables)

-- 5. Revoke mutation rights explicitly (defense-in-depth)
REVOKE CREATE ON SCHEMA public FROM dera_inspector;
ALTER DEFAULT PRIVILEGES REVOKE INSERT, UPDATE, DELETE ON TABLES FROM dera_inspector;
```
