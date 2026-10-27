# Supabase PostgreSQL Compatibility Guide

## Supabase Connection Interfaces

Supabase provides three primary connection topologies for PostgreSQL:

| Mode | Port | Supported Features | Pooler Technology | DERA Configuration |
|---|---|---|---|---|
| **Direct Connection** | `5432` | Full PostgreSQL features, prepared statements, IPv6 only on free tier. | Direct PostgreSQL instance | `supabase_pooler_mode="direct"` |
| **Session Pooler** | `6543` | Session-level pooling, supports prepared statements, IPv4 compatible. | Supavisor / PgBouncer | `supabase_pooler_mode="session"` |
| **Transaction Pooler** | `6543` | High concurrency, short transactions, **no prepared statements**, IPv4 compatible. | Supavisor / PgBouncer | `supabase_pooler_mode="transaction"` |

---

## Important Supabase Considerations

### 1. PgBouncer & Prepared Statements
In transaction pooling mode, connections are checked in and out of the pool per transaction. Because prepared statements in PostgreSQL exist in session memory, named prepared statements fail on transaction poolers.
**Solution:** DERA automatically sets `statement_cache_size=0` when `supabase_pooler_mode="transaction"` is configured, allowing seamless introspection via unnamed simple queries.

### 2. User Credentials Formatting
When connecting via Supabase connection poolers (port 6543), the username must specify the project reference ID:
`postgres.[your-project-ref]`

### 3. Password Authentication vs API Keys
Never use the Supabase `anon` public key or `service_role` secret API key as the database password. The connector connects to PostgreSQL using the database password configured in the Supabase Dashboard under Project Settings -> Database.

### 4. TLS Verification
Supabase enforces TLS for all remote connections. Ensure `tls.ssl_mode = "require"` (default) or `tls.ssl_mode = "verify-full"` with Supabase's trusted CA certificates.
