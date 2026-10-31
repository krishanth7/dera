# Connection Forms Specification

**Document Reference**: `docs/frontend/CONNECTION_FORMS.md`  
**Milestone**: Phase 7.3 — Database Connection & Schema Explorer UI  

---

## 1. Engine Selection and Form Architecture

The connection creation interface (`/connections/new`) implements dynamic engine-specific form validation grounded in backend connector contracts.

### Supported Database Engines

1. **PostgreSQL**: Standard relational connection parameters with mandatory SSL/TLS support.
2. **Supabase PostgreSQL**: Managed PostgreSQL variant with pooling/direct toggle and connection string parsing.
3. **MySQL**: MySQL wire protocol parameters with character set and SSL mode configuration.
4. **MariaDB**: Dedicated MariaDB driver specifications honoring MariaDB-specific engine semantics.
5. **SQLite**: Path-contained or in-memory SQLite databases strictly restricted from arbitrary server filesystem paths.

```text
[ Engine Selector Cards ]
          │
          ├── PostgreSQL  ──> [ Host, Port (5432), DB, User, Password, SSL ]
          ├── Supabase    ──> [ Project Ref / Host, Port (6543/5432), DB, User, Password, SSL ]
          ├── MySQL       ──> [ Host, Port (3306), DB, User, Password, SSL ]
          ├── MariaDB     ──> [ Host, Port (3306), DB, User, Password, SSL ]
          └── SQLite      ──> [ Contained Path (:memory: | workspace/*.db | demo/*.db) ]
```

---

## 2. Field Specifications and Validation

| Field | Engines | Validation Rule | Sensitive / Masked |
|---|---|---|---|
| `name` | All | 1–100 characters, alphanumeric with hyphens/spaces | No |
| `host` | Postgres, Supabase, MySQL, MariaDB | Valid hostname or IPv4/IPv6, SSRF-restricted | No |
| `port` | Postgres, Supabase, MySQL, MariaDB | Integer between 1 and 65535 | No |
| `database` | Postgres, Supabase, MySQL, MariaDB | 1–64 characters, valid database identifier | No |
| `username` | Postgres, Supabase, MySQL, MariaDB | 1–64 characters | No |
| `password` | Postgres, Supabase, MySQL, MariaDB | UTF-8 string, masked input element | Yes (Never persisted client-side) |
| `database_path` | SQLite | Restricted to `:memory:` or `workspace/`, `demo/` | No |
| `ssl_enabled` | Postgres, Supabase, MySQL, MariaDB | Boolean | No |

---

## 3. SQLite Path Containment

To mitigate arbitrary local filesystem read vulnerabilities, client-supplied SQLite paths are validated against allowlisted containment roots:

```typescript
// Validation rule enforced in both frontend and backend
const isAllowedPath = path === ":memory:" || 
                      path.startsWith("workspace/") || 
                      path.startsWith("demo/");
```
