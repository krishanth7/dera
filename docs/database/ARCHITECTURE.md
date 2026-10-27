# DERA Platform Database Architecture

## 1. Architectural Mission

The DERA Platform Database provides internal operational state persistence for the DERA platform. It serves as the single source of truth for platform configuration, workspace metadata, future audit records, and internal migration history.

---

## 2. Strict Database Separation Invariant

DERA operates across two independent architectural domains that must never be unified or share database connections:

```mermaid
graph TD
    subgraph DERA_Platform["DERA Platform Domain"]
        API[FastAPI Gateway] --> Engine[SQLAlchemy 2.x AsyncEngine]
        Engine --> Pool[AsyncAdaptedQueuePool]
        Pool --> PlatformDB[(Platform PostgreSQL 16+)]
        Migrations[Alembic CLI] -.->|Controlled DDL| PlatformDB
    end

    subgraph Customer_Domain["Customer Inspected Domain (Phase 5+)"]
        Connectors[Read-Only Connectors] --> InspectTarget[(Customer Databases)]
    end

    style DERA_Platform fill:#f0f7ff,stroke:#0366d6,stroke-width:2px
    style Customer_Domain fill:#fff5f5,stroke:#d73a49,stroke-width:2px
```

### Architectural Guarantees

1. **Zero Cross-Contamination**: No connection string, connection pool, or session object is shared between the platform database and customer databases.
2. **Read-Only Customer Databases**: Customer databases inspected in Phase 5+ are accessed exclusively via read-only transactions.
3. **No Platform Migrations on Customer DBs**: Alembic manages exclusively the internal platform schema (`dera_platform_metadata` and future platform tables). It is strictly forbidden to execute Alembic against customer systems.

---

## 3. Component Interaction Lifecycle

```mermaid
sequenceDiagram
    participant App as FastAPI Lifespan
    participant Engine as AsyncEngine Factory
    participant Pool as Connection Pool
    participant Route as Request Handler
    participant Session as AsyncSession

    App->>Engine: create_database_engine(settings)
    Engine->>Pool: Configure pool_size & max_overflow
    App->>App: Attach session_factory to app.state
    
    Note over Route,Session: Request Processing
    Route->>Session: get_db_session() dependency
    Session->>Pool: Acquire pooled connection
    Route->>Session: Execute typed repository operations
    Route->>Session: Commit or rollback on error
    Route->>Pool: Release connection back to pool

    App->>Engine: dispose_database_engine() on shutdown
    Engine->>Pool: Terminate all active pooled sockets
```

---

## 4. Initial Schema: Platform Metadata

Milestone 4.3 intentionally avoids speculative business models (no prematurely created user tables, roles, or billing models). It introduces a single justified operational table:

### Table: `dera_platform_metadata`

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `key` | `VARCHAR(64)` | No | Unique operational identifier (Primary Key). |
| `value` | `TEXT` | No | Persisted JSON/string representation of state. |
| `description` | `VARCHAR(255)` | Yes | Optional human-readable documentation. |
| `created_at` | `TIMESTAMPTZ` | No | Timestamp in UTC when entry was created. |
| `updated_at` | `TIMESTAMPTZ` | No | Timestamp in UTC when entry was last updated. |
