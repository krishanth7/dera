# DERA MySQL Connector

## Overview

The DERA MySQL Connector (`MySqlConnector`) is a production-grade, asynchronous, read-only metadata introspection adapter implementing the Phase 5.1 `DatabaseConnector` protocol. It enables safe, deterministic schema discovery of MySQL 8.0+ and 8.4 LTS database instances without modifying customer data or executing arbitrary SQL.

MySQL is a network-attached relational database management system. The connector enforces multi-tenant workspace isolation, SSRF destination protection, TLS certificate validation (`ssl.SSLContext`), session-level read-only locking (`SET SESSION TRANSACTION READ ONLY;`), least-privilege catalog querying via `INFORMATION_SCHEMA`, and non-blocking asynchronous execution using `PyMySQL` and `asyncio.to_thread`.

---

## Key Features

- **Strict Read-Only Guarantee:** Every connection executes session-level read-only initialization statements immediately upon connection establishment, rejecting any DDL/DML mutation attempts.
- **SSRF and Network Protection:** Restricts outbound connections to authorized database destinations, blocks loopback and cloud metadata endpoints (`169.254.169.254`), and enforces port boundaries.
- **Deterministic Metadata Discovery:** All queries against `INFORMATION_SCHEMA` use fixed parameterization, pre-reviewed SQL, and deterministic `ORDER BY` clauses across schemas, tables, columns, constraints, and indexes.
- **MySQL 8.0+ Feature Support:** Full discovery support for stored and virtual generated columns, MySQL 8.0.16+ `CHECK_CONSTRAINTS`, invisible indexes, and functional expression indexes.
- **Dialect Fidelity:** Preserves native MySQL data types, unsigned/zerofill flags, auto-increment attributes, character sets, and collations without lossy translations.
- **Asynchronous & Thread-Safe:** Pure Python driver (`PyMySQL`) bridged via `asyncio.to_thread` for non-blocking event loop execution, bounded timeouts, and cancellation.
- **Zero AI / Deterministic:** Operates purely on deterministic catalog queries without LLMs, machine-learning inference, or external AI services.

---

## Documentation Navigation

- [Architecture Guide](../mysql-family/ARCHITECTURE.md): Shared MySQL-family architecture, driver evaluation, and threading model.
- [Configuration Reference](./CONFIGURATION.md): Typed connection parameters, port defaults, character set bindings, and timeouts.
- [Security Model](./SECURITY.md): Multi-layer read-only defenses, TLS verification, credential isolation, and SSRF rules.
- [Metadata Inspection](./METADATA_INSPECTION.md): Information schema catalog queries, column attribute extraction, and index handling.
- [Capability Matrix](./CAPABILITIES.md): Detailed capability declarations and unsupported engine features.
- [Privileges Guide](../mysql-family/PRIVILEGES.md): Least-privilege grant matrix for metadata inspection accounts.
- [Compatibility Matrix](./COMPATIBILITY.md): Supported MySQL versions, LTS releases, and platform invariants.
- [Testing Guide](../mysql-family/TESTING.md): Conformance suite, mock verification, and live integration tests.
- [Troubleshooting](./TROUBLESHOOTING.md): Common connection errors, access denials, TLS errors, and remedies.
