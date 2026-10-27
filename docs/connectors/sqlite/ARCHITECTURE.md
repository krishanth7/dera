# DERA SQLite Connector Architecture

## Architectural Position

The SQLite connector integrates cleanly into DERA's Phase 5 layered platform:

```text
┌───────────────────────────────────────────────────────────────┐
│               DERA Backend Platform (FastAPI)                 │
├───────────────────────────────────────────────────────────────┤
│          Authentication & Multi-Tenant Workspace RBAC         │
├───────────────────────────────────────────────────────────────┤
│        Phase 5.1 Universal DatabaseConnector Protocol         │
├───────────────────────────────────────────────────────────────┤
│                  SqliteConnector Adapter                      │
├────────────────────────────────┬──────────────────────────────┤
│    Filesystem Boundary Guard   │   SqliteConnectionManager    │
│    - Storage Root Confinement  │   - Non-blocking Thread Pool │
│    - Traversal & Symlink Check │   - URI mode=ro & PRAGMAs    │
├────────────────────────────────┴──────────────────────────────┤
│        Pre-Approved SQLite 3 Database File (.sqlite/.db)      │
│        (sqlite_schema + PRAGMA Introspection Engine)          │
└───────────────────────────────────────────────────────────────┘
```

SQLite differs fundamentally from network databases like PostgreSQL. It runs in-process, accesses local filesystem blocks directly, and has no network sockets, user authentication roles, or TLS handshakes.

---

## Driver Selection & Async Strategy

### Evaluation

1. **Python Standard Library `sqlite3` (Selected):**
   - Built into Python 3.12+ and linked directly to the system's SQLite 3 C library.
   - Zero additional third-party dependencies required.
   - High performance, mature, and predictable.
   - Supports URI filename handling (`file:...`), `mode=ro`, and PRAGMAs.
2. **`aiosqlite`:**
   - Wraps standard library `sqlite3` using background threads.
   - Adds an external dependency that duplicates `asyncio.to_thread` functionality.
3. **Decision:**
   - Standard library `sqlite3` offloaded asynchronously via Python's built-in `asyncio.to_thread` was selected. This guarantees non-blocking execution inside FastAPI while eliminating unnecessary dependencies.

### Threading & Concurrency Model

SQLite connections cannot be safely shared across concurrent execution threads without serialized threading mode. `SqliteConnectionManager` manages a connection pinned to worker threads, guarded by an `asyncio.Lock` to ensure serialized query execution.

When an operation deadline expires or a `CancellationToken` is tripped:
1. `asyncio.wait_for` raises `TimeoutError` or checks the token.
2. `sqlite3.Connection.interrupt()` is called to immediately halt any long-running C query execution.
3. Resources are safely closed and released.
