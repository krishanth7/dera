# DERA Database Connectors & Metadata Inspection Hub

## Overview

The DERA Database Connectors subsystem (`packages/connectors/src/dera_connectors/`) provides universal, strongly typed, deterministic database connectivity interfaces and capability discovery contracts. Designed according to strict read-only and least-privilege principles, DERA connects to external databases exclusively to extract relational catalog metadata (schemas, tables, columns, constraints, indexes, views). It never executes user-supplied SQL or modifies customer database schemas or data.

## Phase 5.1 Architecture

```text
Layer A: Platform Infrastructure (FastAPI, Auth, PostgreSQL persistence, Background jobs, RBAC)
   |
Layer B: Universal Connector Abstraction (Protocol, Capabilities, Metadata Models, Error Taxonomy, Security)
   |
Layer C: Database Adapters (PostgreSQL/Supabase [5.2], SQLite [5.3], MySQL/MariaDB [5.4])
```

## Documentation Index

| Specification | Description | Primary Reference |
|---|---|---|
| [**Architecture**](ARCHITECTURE.md) | Layered architecture, separation of concerns, and design principles | [ARCHITECTURE.md](ARCHITECTURE.md) |
| [**Connector Protocol**](CONNECTOR_PROTOCOL.md) | Universal typed `DatabaseConnector` protocol and async operations | [CONNECTOR_PROTOCOL.md](CONNECTOR_PROTOCOL.md) |
| [**Capability Model**](CAPABILITY_MODEL.md) | `ConnectorCapability`, status taxonomy, and discovery contracts | [CAPABILITY_MODEL.md](CAPABILITY_MODEL.md) |
| [**Metadata Contracts**](METADATA_CONTRACTS.md) | Strongly-typed Pydantic v2 schemas for tables, columns, constraints, indexes, views | [METADATA_CONTRACTS.md](METADATA_CONTRACTS.md) |
| [**Connection Lifecycle**](CONNECTION_LIFECYCLE.md) | Explicit state machine (`CREATED` -> `CONNECTED` -> `CLOSED`), cleanup, and cancellation | [CONNECTION_LIFECYCLE.md](CONNECTION_LIFECYCLE.md) |
| [**Read-Only Security**](READ_ONLY_SECURITY.md) | Mutation prevention, query validation, and SSRF egress restrictions | [READ_ONLY_SECURITY.md](READ_ONLY_SECURITY.md) |
| [**Credential Handling**](CREDENTIAL_HANDLING.md) | Secret masking, vault resolution, zero-logging of authentication tokens | [CREDENTIAL_HANDLING.md](CREDENTIAL_HANDLING.md) |
| [**Error Model**](ERROR_MODEL.md) | RFC 9457-compatible error taxonomy and sanitized exception mapping | [ERROR_MODEL.md](ERROR_MODEL.md) |
| [**Conformance Testing**](CONFORMANCE_TESTING.md) | Reusable `BaseConnectorConformanceTests` test suite for future adapters | [CONFORMANCE_TESTING.md](CONFORMANCE_TESTING.md) |
| [**PostgreSQL & Supabase**](postgresql/README.md) | Production PostgreSQL 14–18 & Supabase async read-only connector | [postgresql/README.md](postgresql/README.md) |
| [**SQLite Connector**](sqlite/README.md) | Production read-only SQLite 3 embedded connector adapter | [sqlite/README.md](sqlite/README.md) |
| [**Adapter Development**](ADAPTER_DEVELOPMENT.md) | Step-by-step implementation guide for new database adapters (Phases 5.2–5.4) | [ADAPTER_DEVELOPMENT.md](ADAPTER_DEVELOPMENT.md) |
| [**Engine Compatibility**](ENGINE_COMPATIBILITY.md) | Supported database engines, drivers, and version targets | [ENGINE_COMPATIBILITY.md](ENGINE_COMPATIBILITY.md) |
