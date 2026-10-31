# DERA End-to-End Data Flow Architecture

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Maintainer:** Krishanth  
> **Status:** Active Architectural Specification  
> **Last Verified:** 2026-10-26 (Commit `e550fdd`)  

---

## 1. Introspection Lifecycle Overview

DERA's end-to-end metadata processing lifecycle transforms raw database catalog rows into canonical domain models, dependency graphs, and diagnostic reports without touching customer table rows.

The full processing pipeline consists of 8 discrete stages:

```text
[1. Connection Configuration]
           │
           ▼
[2. Connection Validation (Read-Only Test)]
           │
           ▼
[3. Catalog Metadata Inspection]
           │
           ▼
[4. Canonical Schema Normalization]
           │
           ▼
[5. Referential Graph & Cycle Analysis]
           │
           ▼
[6. Diagnostic Rule Linting]
           │
           ▼
[7. Cryptographic Hashing & Serialization]
           │
           ▼
[8. Presentation / API Response]
```

---

## 2. Implemented vs. Planned Processing Stages

To maintain truth-in-documentation, the implementation status of each stage is classified as follows:

| Stage | Name | Implementation Status | Active Code Reference |
|---|---|---|---|
| **1** | Connection Configuration | **Implemented** | `ConnectionConfig` in [`dera_connectors.base.connector`](../../packages/connectors/src/dera_connectors/base/connector.py) |
| **2** | Connection Validation | **Implemented (SQLite)** | `SqliteConnector.test_connection()` in [`dera_connectors.sqlite.connector`](../../packages/connectors/src/dera_connectors/sqlite/connector.py) |
| **3** | Catalog Metadata Inspection | **Implemented (SQLite)** | `SqliteConnector.inspect_tables()` querying `sqlite_master` and PRAGMAs |
| **4** | Canonical Normalization | **Implemented** | `DatabaseTable`, `DatabaseColumn`, `PrimaryKeyConstraint`, `ForeignKeyConstraint`, `TableIndex` in [`dera.models`](../../packages/core/src/dera/models.py) |
| **5** | Dependency Graph Analysis | **Implemented** | `build_dependency_graph()` & `compute_topological_sort()` in [`dera.graph`](../../packages/core/src/dera/graph.py) |
| **6** | Diagnostic Rule Linting | **Implemented** | `run_all_diagnostics()` evaluating rules `RULE-INT-001` and `RULE-PERF-002` in [`dera.diagnostics`](../../packages/core/src/dera/diagnostics/__init__.py) |
| **7** | Snapshot Hashing & Serialization | **Implemented** | `SchemaSnapshot.compute_hash()` generating deterministic SHA-256 fingerprint in `dera.models` |
| **8** | API Response / Web Canvas | **Partially Implemented** | Health and meta endpoints active in `apps/api`; full inspection endpoint (`POST /api/v1/inspect`) and canvas visualizer scheduled for Phase 5 & 7 |

---

## 3. Sequence Architecture Diagram

The sequence diagram below models the end-to-end introspection flow, clearly distinguishing operational calls from planned service invocations:

```mermaid
sequenceDiagram
    autonumber
    actor User as Contributor / User
    participant Web as apps/web (Studio)
    participant API as apps/api (Gateway)
    participant Conn as packages/connectors
    participant Core as packages/core
    participant DB as Target Database (Read-Only)

    Note over User,DB: Stage 1: Connection & Validation (Operational for SQLite)
    User->>Web: Configure database target (dialect, path/host)
    Web->>API: Dispatch connection config
    API->>Conn: Instantiate Connector(ConnectionConfig)
    Conn->>DB: Connect (enforce read-only pragma/transaction)
    Conn->>DB: Execute read-only probe (SELECT 1;)
    DB-->>Conn: Probe success

    Note over Conn,DB: Stage 2: Metadata Extraction (Operational for SQLite)
    Conn->>DB: Query system catalog (sqlite_master / information_schema)
    Note over Conn: Static mutation check: validate_query_read_only()
    DB-->>Conn: Raw metadata result set

    Note over Conn,Core: Stage 3: Normalization & Graph Analysis (Operational)
    Conn->>Core: Map raw rows into canonical DatabaseTable models
    Core->>Core: Build SchemaGraph dependency adjacency list
    Core->>Core: Compute topological sort (Kahn's algorithm)
    Core->>Core: Evaluate diagnostic rules (Missing PK, Unindexed FK)
    Core->>Core: Construct immutable SchemaSnapshot
    Core->>Core: Compute deterministic SHA-256 hash digest

    Note over API,Web: Stage 4: Serialization & UI Display (Scaffold active)
    Core-->>API: Canonical SchemaSnapshot & DiagnosticFindings
    API-->>Web: JSON payload matching schema-snapshot.json
    Web-->>User: Display status, table list, and diagnostic findings
```

---

## 4. Query Safety & Read-Only Invariant Flow

To protect target databases against accidental modification or malicious queries, DERA enforces a multi-layer safety check:

```mermaid
flowchart TD
    QUERY[Candidate Query String] --> REGEX{BaseConnector Static Regex Check}
    REGEX -->|Contains DROP, ALTER, TRUNCATE, INSERT, UPDATE, DELETE, GRANT, REVOKE| REJECT[Raise ReadOnlyViolationError - Block Query]
    REGEX -->|Passes Clean| PRAGMA{Database Connection State}
    PRAGMA -->|SQLite: PRAGMA query_only = ON<br/>PostgreSQL: SET TRANSACTION READ ONLY| EXECUTE[Execute Query Against Catalog]
    EXECUTE --> RESULT[Return System Metadata Rows]

    classDef danger fill:#ffebee,stroke:#c62828,stroke-width:2px;
    classDef safe fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;

    class REJECT danger;
    class RESULT,EXECUTE safe;
```

---

## 5. Related Architecture Specifications

- [System Overview](SYSTEM_OVERVIEW.md)
- [Monorepo Directory Layout](MONOREPO_STRUCTURE.md)
- [Module Boundaries](MODULE_BOUNDARIES.md)
- [Database Connector Architecture](../connectors/CONNECTOR_ARCHITECTURE.md)
- [Graph Engine Documentation](../core/GRAPH_ENGINE.md)
