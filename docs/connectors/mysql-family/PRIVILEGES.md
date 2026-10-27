# MySQL & MariaDB Least-Privilege Guide

## Overview

DERA connectors strictly adhere to the principle of least privilege. Metadata inspection accounts require only the minimum privileges necessary to query catalog information without elevated administrative permissions or table modification rights.

---

## Minimal Privilege Matrix

| Object / Scope | Required Grant | Purpose |
|---|---|---|
| Target Database (`dbname.*`) | `SELECT` | Required by MySQL/MariaDB for catalog visibility of tables, columns, and constraints in `INFORMATION_SCHEMA`. |
| Target Database (`dbname.*`) | `SHOW VIEW` | Required to view definitions of SQL views in `INFORMATION_SCHEMA.VIEWS`. |
| Global (`*.*`) | *None* | Administrative privileges (`SUPER`, `PROCESS`, `FILE`, `RELOAD`) are **prohibited**. |
| System Schemas (`mysql.*`) | *None* | Direct access to internal user and privilege tables is **prohibited**. |

---

## Least-Privilege Provisioning Script

Run the following SQL on the source database to provision a dedicated, least-privilege inspection user:

```sql
-- 1. Create inspection user with restricted network scope
CREATE USER 'dera_inspector'@'%' IDENTIFIED BY 'StrongRandomPassword123!';

-- 2. Grant read-only access to customer database
GRANT SELECT, SHOW VIEW ON `customer_database`.* TO 'dera_inspector'@'%';

-- 3. Require TLS transport
ALTER USER 'dera_inspector'@'%' REQUIRE SSL;

-- 4. Apply changes
FLUSH PRIVILEGES;
```

---

## Explicitly Prohibited Privileges

Never grant any of the following to a DERA connector user account:

- `INSERT`, `UPDATE`, `DELETE`: Violates DERA read-only invariants.
- `CREATE`, `ALTER`, `DROP`, `TRUNCATE`: Schema mutation privileges are rejected by design.
- `GRANT OPTION`: Prevents credential delegation or privilege escalation.
- `SUPER`, `PROCESS`, `RELOAD`: Avoids exposing server-wide internal state or process lists.
