# DERA SQLite Connector

## Overview

The DERA SQLite Connector (`SqliteConnector`) is a production-grade, asynchronous, read-only metadata introspection adapter implementing the Phase 5.1 `DatabaseConnector` protocol. It enables safe, deterministic schema discovery of local SQLite 3 database files without altering customer files or executing user-supplied SQL.

SQLite is an embedded, file-based relational engine rather than a networked client-server database. Consequently, the connector focuses on strict filesystem boundary isolation, approved storage root confinement, symlink redirection protection, URI `mode=ro` enforcement, `PRAGMA query_only = ON` locking, and comprehensive SQLite 3 schema introspection (`sqlite_schema` + PRAGMAs).

---

## Key Features

- **Strict Read-Only Defense in Depth:** Every SQLite connection is opened via validated SQLite URIs with `mode=ro`, augmented by immediate `PRAGMA query_only = ON;` and `PRAGMA busy_timeout` enforcement.
- **Filesystem Isolation:** Rejects directory traversal attempts (`..`), enforces approved storage root boundaries, validates realpath symlink targets, and prevents access to system files.
- **Deep Metadata Introspection:** Extracts tables, columns (`PRAGMA table_xinfo`), primary keys, composite foreign keys (`PRAGMA foreign_key_list`), unique constraints, check constraints (DDL parsing), indexes (`PRAGMA index_xinfo`), views, and triggers from `sqlite_schema`.
- **Advanced SQLite Features:** Full recognition and metadata discovery for `STRICT` tables, `WITHOUT ROWID` tables, stored/virtual generated columns, partial indexes (`WHERE` clause predicates), and expression indexes.
- **Type Affinity Engine:** Implements the official SQLite 3 Type Affinity rules (Rules 1–5), distinguishing native declared column types from derived affinities (`INTEGER`, `TEXT`, `BLOB`, `REAL`, `NUMERIC`).
- **Non-Blocking Asynchronous Engine:** Offloads synchronous SQLite C runtime calls to a dedicated worker thread via `asyncio.to_thread` with cooperative `cancellation_token` and timeout interruption.
- **Zero AI / Deterministic:** Operates purely on deterministic catalog queries and rule-based DDL extraction without LLMs, generative AI, or external inference services.

---

## Documentation Navigation

- [Architecture Guide](./ARCHITECTURE.md): Driver evaluation, threading model, and async connection management.
- [Configuration Reference](./CONFIGURATION.md): Typed connection parameters, storage roots, timeouts, and snapshot options.
- [Security Model](./SECURITY.md): Multi-layer read-only defenses, authorizer restrictions, and denial-of-service bounds.
- [Filesystem Isolation](./FILESYSTEM_ISOLATION.md): Canonical path resolution, traversal prevention, and symlink policy.
- [Metadata Inspection](./METADATA_INSPECTION.md): Catalog queries, PRAGMA interrogation, and DDL constraint extraction.
- [Capability Matrix](./CAPABILITIES.md): Detailed capability declarations and unsupported engine features.
- [Type Affinity](./TYPE_AFFINITY.md): Implementation of SQLite 3 Type Affinity rules 1 through 5.
- [Testing Guide](./TESTING.md): Conformance suite, filesystem security, live WAL testing, and unit tests.
- [Troubleshooting](./TROUBLESHOOTING.md): Common error scenarios, locked databases, and resolution strategies.
- [Compatibility Matrix](./COMPATIBILITY.md): Supported SQLite versions, Python runtimes, and platform invariants.
