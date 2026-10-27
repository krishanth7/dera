# DERA Database Configuration Guide

## Environment Variables

All database settings are validated at application startup using Pydantic v2 settings.

| Environment Variable | Alias | Default | Description |
| :--- | :--- | :--- | :--- |
| `DERA_PLATFORM_DATABASE_URL` | `DATABASE_URL` | `None` | Asynchronous database connection URI (`postgresql+asyncpg://...`). |
| `DERA_DB_POOL_SIZE` | `DB_POOL_SIZE` | `10` | Number of persistent connections maintained in the pool (1-100). |
| `DERA_DB_MAX_OVERFLOW` | `DB_MAX_OVERFLOW` | `5` | Maximum number of surge connections allowed beyond pool size (0-50). |
| `DERA_DB_POOL_TIMEOUT` | `DB_POOL_TIMEOUT` | `30.0` | Seconds to block waiting for an available pooled connection (1.0-300.0). |
| `DERA_DB_POOL_RECYCLE` | `DB_POOL_RECYCLE` | `1800` | Connection recycling interval in seconds (prevents stale TCP connections). |
| `DERA_DB_CONNECT_TIMEOUT` | `DB_CONNECT_TIMEOUT` | `10.0` | Socket-level timeout in seconds when establishing new TCP connections. |
| `DERA_DB_STATEMENT_TIMEOUT_MS` | `DB_STATEMENT_TIMEOUT_MS` | `30000` | Server-side query execution timeout in milliseconds. |
| `DERA_DB_SSL_MODE` | `DB_SSL_MODE` | `prefer` | SSL transport mode (`disable`, `allow`, `prefer`, `require`, `verify-ca`, `verify-full`). |
| `DERA_DB_ECHO` | `DB_ECHO` | `false` | Enable verbose SQL statement logging (strictly prohibited in production). |

---

## Connection Limits & Capacity Sizing

The maximum theoretical connections held by a single application worker process is:

$$\text{Max Connections} = \text{db\_pool\_size} + \text{db\_max\_overflow}$$

For default values: $10 + 5 = 15 \text{ connections per worker process}$.

If running under a multi-worker ASGI server (e.g., Uvicorn with 4 workers), total application connections approach $4 \times 15 = 60 \text{ connections}$. Ensure your PostgreSQL server's `max_connections` parameter is sized appropriately with sufficient headroom for migration jobs and diagnostic connections.

---

## Credential Sanitization & Security

The platform configuration layer enforces defensive protections:

1. **Automatic Password Masking**: `settings.sanitized_database_url` replaces passwords with `***` before emitting to logs.
2. **Production Echo Prohibition**: Setting `DERA_DB_ECHO=true` when `APP_ENV=production` raises a fatal configuration validation error.
3. **Stateless Fallback**: When `DERA_PLATFORM_DATABASE_URL` is omitted, the API gateway starts in stateless mode without errors, gracefully reporting `platform_database: not_configured` on `/health/ready`.
