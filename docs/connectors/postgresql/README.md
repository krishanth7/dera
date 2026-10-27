# DERA PostgreSQL & Supabase PostgreSQL Connector

## Overview

The DERA PostgreSQL Connector is a production-oriented, asynchronous, read-only database introspection adapter implementing the Phase 5.1 `DatabaseConnector` protocol. It supports standard PostgreSQL (versions 14 through 18) and cloud-hosted Supabase PostgreSQL (direct, session pooler, and transaction pooler interfaces).

Built on top of `asyncpg`, the connector provides high-throughput system catalog interrogation, strict TLS validation, SSRF boundary enforcement, and multi-layer read-only session locking without ever querying customer row data or invoking stored procedures.

---

## Key Features

- **Strict Read-Only Guarantee:** Every connection initializes with `SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;` and an explicit `statement_timeout`.
- **System Catalog Queries:** Extracts rich schema metadata directly from `pg_catalog` (`pg_namespace`, `pg_class`, `pg_attribute`, `pg_constraint`, `pg_index`, `pg_description`, `pg_views`, `pg_sequences`, `pg_partitioned_table`).
- **Supabase Pooler Compatibility:** Native auto-detection of Supabase endpoints with automatic disabling of prepared statement caching (`statement_cache_size=0`) when connecting via PgBouncer transaction poolers on port 6543.
- **SSRF & Network Defenses:** Pre-flight network validation blocks access to cloud metadata services (`169.254.169.254`) and restricted private networks.
- **Deterministic Ordering:** All metadata outputs (schemas, tables, columns, constraints, indexes, views, sequences, partitions) are sorted alphabetically or ordinally.
- **Zero AI / Deterministic:** Operates purely on relational metadata queries without any LLM, vector, or agentic inference.

---

## Documentation Navigation

- [Architecture Guide](./ARCHITECTURE.md): Driver evaluation, component layout, and lifecycle design.
- [Configuration Reference](./CONFIGURATION.md): Connection parameters, TLS controls, and timeout settings.
- [Security Model](./SECURITY.md): Defense-in-depth, SSRF safeguards, and read-only transaction guarantees.
- [Catalog Inspection](./CATALOG_INSPECTION.md): Detailed catalog query inventory and SQL mapping.
- [Capability Matrix](./CAPABILITIES.md): Introspection capabilities and permission status.
- [Type Handling](./TYPE_HANDLING.md): Preservation of PostgreSQL native types, domains, enums, and generated columns.
- [Permissions & Role Guide](./PERMISSIONS.md): Least-privilege role configuration and SQL grants.
- [Testing Guide](./TESTING.md): Running unit, conformance, security, and live integration tests.
- [Troubleshooting](./TROUBLESHOOTING.md): Diagnosing connection errors, pooler limitations, and timeouts.
- [Supabase Compatibility](./SUPABASE_COMPATIBILITY.md): Connecting to Supabase direct, session, and transaction poolers.
