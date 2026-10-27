# Database Engine Compatibility Matrix

## Supported Engine Targets

| Engine | Canonical Dialect | Target Drivers | Target Versions | Phase |
|---|---|---|---|---|
| **PostgreSQL** | `postgresql` | `asyncpg` (async) | PostgreSQL 12, 13, 14, 15, 16 | Phase 5.2 |
| **Supabase PostgreSQL** | `postgresql` (provider `supabase`) | `asyncpg` (async) | PostgreSQL 15, 16 | Phase 5.2 |
| **SQLite** | `sqlite` | `aiosqlite` (async) | SQLite 3.35+ | Phase 5.3 |
| **MySQL** | `mysql` | `asyncmy` (async) | MySQL 8.0, 8.4 LTS | Phase 5.4 |
| **MariaDB** | `mariadb` | `asyncmy` (async) | MariaDB 10.6, 11.x | Phase 5.4 |

## Compatibility Policy

- Only database versions actively supported by their upstream maintainers are certified.
- Deprecated database versions will trigger diagnostic advisories in `DatabaseIdentity.server_capability_hints`.
