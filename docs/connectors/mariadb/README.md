# DERA MariaDB Connector

## Overview

The DERA MariaDB Connector (`MariaDbConnector`) is a production-grade, asynchronous, read-only metadata introspection adapter implementing the Phase 5.1 `DatabaseConnector` protocol. It enables safe, deterministic schema discovery of MariaDB 10.11+ and 11.4 LTS database instances without modifying customer data or executing arbitrary SQL.

MariaDB is an independent relational database engine originating as a community fork of MySQL. While wire-compatible with MySQL clients, MariaDB possesses distinct server versioning, storage engine ecosystems (Aria, InnoDB, ColumnStore), check constraint handling (MariaDB 10.2+), and generated column syntax (`PERSISTENT` vs `STORED`). The DERA MariaDB adapter recognizes and respects these architectural differences.

---

## Key Features

- **Strict Read-Only Guarantee:** Enforces session-level read-only initialization statements upon connection establishment, rejecting any DDL/DML mutation attempts.
- **SSRF and Network Protection:** Restricts outbound connections to authorized database destinations, blocks loopback and cloud metadata endpoints (`169.254.169.254`), and enforces port boundaries.
- **Accurate Engine Fingerprinting:** Distinguishes MariaDB servers from standard MySQL via server version strings and `@@version_comment` inspection, reporting `DatabaseEngine.MARIADB`.
- **MariaDB Storage Engine Inspection:** Accurately introspects table storage engines including `Aria` and `InnoDB`.
- **MariaDB Check Constraints:** Discovers check constraints using MariaDB 10.2+ `INFORMATION_SCHEMA.CHECK_CONSTRAINTS` without execution.
- **Generated Columns:** Identifies MariaDB virtual and persistent (`PERSISTENT GENERATED`) columns and extracts generation expressions.
- **Asynchronous & Thread-Safe:** Pure Python driver (`PyMySQL`) bridged via `asyncio.to_thread` for non-blocking event loop execution, bounded timeouts, and cancellation.
- **Zero AI / Deterministic:** Operates purely on deterministic catalog queries without LLMs, machine-learning inference, or external AI services.

---

## Documentation Navigation

- [Architecture Guide](../mysql-family/ARCHITECTURE.md): Shared MySQL-family architecture, driver evaluation, and threading model.
- [Configuration Reference](./CONFIGURATION.md): Typed connection parameters, port defaults, character set bindings, and timeouts.
- [Security Model](./SECURITY.md): Multi-layer read-only defenses, TLS verification, credential isolation, and SSRF rules.
- [Metadata Inspection](./METADATA_INSPECTION.md): Information schema catalog queries, column attribute extraction, and constraint handling.
- [Capability Matrix](./CAPABILITIES.md): Detailed capability declarations and unsupported engine features.
- [Privileges Guide](../mysql-family/PRIVILEGES.md): Least-privilege grant matrix for metadata inspection accounts.
- [Compatibility Matrix](./COMPATIBILITY.md): Supported MariaDB versions, LTS releases, and platform invariants.
- [Testing Guide](../mysql-family/TESTING.md): Conformance suite, mock verification, and live integration tests.
- [Troubleshooting](./TROUBLESHOOTING.md): Common connection errors, access denials, TLS errors, and remedies.
