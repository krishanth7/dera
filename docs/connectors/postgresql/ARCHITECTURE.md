# PostgreSQL Connector Architecture

## Component Hierarchy

The PostgreSQL connector is situated in the DERA ecosystem as a concrete adapter implementing the Phase 5.1 `DatabaseConnector` protocol:

```text
DERA FastAPI Platform / Workers
        │
        ▼
Connector Registry (`create_connector`)
        │
        ▼
PostgresConnector (`dera_connectors.postgresql.adapter`)
        │
        ├── PostgresConnectorConfig (Pydantic v2 validation)
        ├── ConnectionLifecycle (CREATED -> CONNECTING -> CONNECTED -> CLOSING -> CLOSED)
        ├── PostgresConnectionManager (asyncpg connection wrapper)
        │       ├── SSLContext (verify-full, verify-ca, require)
        │       └── Session Initialization (READ ONLY + statement_timeout)
        │
        ├── Catalog Inspection Engine (`dera_connectors.postgresql.catalog`)
        │       └── pg_catalog Queries (`dera_connectors.postgresql.queries`)
        │
        └── Error Classifier (`dera_connectors.postgresql.errors`)
                └── SQLSTATE / Exception -> DERA Domain Error
```

---

## Driver Selection Rationale

`asyncpg` was selected as the standard PostgreSQL driver for DERA:
1. **Binary Protocol Efficiency:** Implements PostgreSQL frontend/backend protocol directly in Python with Cython acceleration.
2. **Cancellation Support:** Native `Connection.cancel()` allows clean cancellation propagation from DERA `CancellationToken`.
3. **Session Parameterization:** Allows setting `application_name` and `statement_timeout` during initial handshake.
4. **Supabase Compatibility:** Compatible with PgBouncer transaction pooling when prepared statement caching is disabled (`statement_cache_size=0`).
5. **No ORM Side-Effects:** Directly executes parameterized catalog queries without polluting SQLAlchemy engine metadata or triggering table reflection overhead.

---

## Connection Lifecycle State Machine

1. **Instantiation:** `PostgresConnector` initializes with `ConnectionState.CREATED`. No network operations or DNS lookups are performed at import or initialization.
2. **Connection Phase (`connect()`):**
   - Transitions to `ConnectionState.CONNECTING`.
   - Pre-flight SSRF validation checks `host` against forbidden targets.
   - SSLContext negotiated according to `TLSSettings`.
   - `asyncpg.connect()` establishes connection.
   - Read-only session characteristics and statement timeout applied immediately.
   - Transitions to `ConnectionState.CONNECTED`.
3. **Execution Phase:**
   - Catalog queries run through `fetch()` or `fetchrow()` with query timeout deadlines and cooperative cancellation checks.
4. **Teardown Phase (`close()`):**
   - Transitions to `ConnectionState.CLOSING`.
   - Underlying socket closed and resources released.
   - Transitions to `ConnectionState.CLOSED` (safely idempotent).
