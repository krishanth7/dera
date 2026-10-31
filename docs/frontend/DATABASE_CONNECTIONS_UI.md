# Database Connections UI Specification

**Document Reference**: `docs/frontend/DATABASE_CONNECTIONS_UI.md`  
**Milestone**: Phase 7.3 — Database Connection & Schema Explorer UI  

---

## 1. Overview & Architecture

The DERA Database Connections UI provides authorized users with a centralized interface to manage database connection configurations, execute diagnostic connectivity probes, and trigger schema metadata extractions.

```text
[ Browser / Next.js Client ]
             │ (HTTPS + HttpOnly Session Cookie + CSRF Header)
             ▼
[ DERA API: /api/v1/workspaces/{id}/connections ]
             │ (Read-Only Boundaries + Vault Isolation)
             ▼
[ DERA Connector Adapters ] ──> [ Remote Customer DB / Contained SQLite ]
```

---

## 2. Key Capabilities

- **Workspace Scoped Listing**: All database connections are isolated to the active tenant workspace.
- **Engine Badging**: Visual badges for PostgreSQL, Supabase, MySQL, MariaDB, and contained SQLite.
- **Sanitized Coordinates**: Hostnames and ports are rendered safely without password disclosure.
- **Real-Time Status**: Displays connection health (`connected`, `failed`, `not_tested`, `testing`).
- **Inspection Triggers**: Direct action to trigger reverse engineering and transition to the Schema Explorer.
