# Database Connector Architecture

## Architectural Separation

DERA connector systems strictly decouple internal platform infrastructure from customer database inspection:

1. **Layer A — DERA Platform Infrastructure:**
   - Internal PostgreSQL database storing users, sessions, workspaces, audit logs, and background jobs.
   - FastAPI application layer with centralized RBAC and tenant boundaries.
   - Celery/Redis background worker orchestration.

2. **Layer B — Universal Connector Abstraction (Phase 5.1):**
   - **Protocol (`DatabaseConnector`):** Strongly typed asynchronous protocol for lifecycle and inspection.
   - **Capability Model:** Explicit capability flags and permission status declarations.
   - **Metadata Contracts:** Engine-agnostic Pydantic v2 metadata descriptors.
   - **Registry & Factory:** Static adapter registry preventing arbitrary module execution.
   - **Security Policy:** Read-only query validation, SSRF target filtering, and secret scrubbing.

3. **Layer C — Database-Specific Adapters (Future Milestones):**
   - Phase 5.2: PostgreSQL & Supabase PostgreSQL adapter (`asyncpg`).
   - Phase 5.3: SQLite adapter (`aiosqlite`).
   - Phase 5.4: MySQL & MariaDB adapter (`asyncmy`).

## Core Invariants

- **Read-Only Operation:** Connectors never issue `CREATE`, `DROP`, `ALTER`, `INSERT`, `UPDATE`, or `DELETE`.
- **Zero Customer Database Contamination:** Customer databases are never used to store DERA application state, telemetry, or scratch tables.
- **Tenant Isolation:** Connector configurations and contexts are permanently bound to a `workspace_id`. Cross-tenant credential or metadata access is impossible.
- **Deterministic Ordering:** Schemas, tables, columns, constraints, and indexes are ordered deterministically across all queries.
