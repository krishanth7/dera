# Phase 7.3 Database Connection & Schema Explorer UI — Baseline Audit

**Document Reference**: `docs/audit/PHASE_7_3_EXPLORER_BASELINE.md`  
**Milestone**: Phase 7.3 — Database Connection & Schema Explorer UI  
**Implementation Branch**: `feat/phase-7.3-connection-schema-explorer`  
**Base Commit SHA**: `a60d13ea099383ab7b52b832100baa36f8f93d74`  
**Audit Date**: October 2026  
**Auditor**: Coordinated Engineering Architecture Team  

---

## 1. Executive Summary

Phase 7.3 delivers DERA's database connection management and interactive schema explorer frontend studio. This baseline audit assesses existing frontend infrastructure (Phase 7.1 Next.js foundation, Phase 7.2 authentication & workspaces), backend connectors (Phase 5 PostgreSQL, Supabase, SQLite, MySQL, MariaDB adapters), and reverse-engineering services (Phase 6 canonical schema representations, dependency analysis, snapshots).

All connections, diagnostic tests, and schema explorations are strictly mediated by authorized DERA backend services. Direct browser-to-database connections and client-side credential persistence are strictly prohibited.

---

## 2. Verified Prerequisites & System Status

| Domain | Milestone | Status | Verified Capabilities |
| :--- | :--- | :--- | :--- |
| **Backend Core** | Phase 4.1–4.6 | Merged & Active | FastAPI application factory, session authentication, CSRF double-submit protection, workspace RBAC, transactional outbox jobs. |
| **Connectors** | Phase 5.1–5.6 | Merged & Active | PostgreSQL, Supabase, SQLite, MySQL, MariaDB adapters with read-only transaction enforcement, timeout bounds, and credential isolation. |
| **Reverse Engineering** | Phase 6.1–6.5 | Merged & Active | Canonical `SchemaRepresentation`, structural reconstruction, foreign key graph, dependency ordering, RFC 8785 canonical snapshots. |
| **Reverse Engineering APIs** | Phase 6.6 | Merged & Active | REST endpoints for schemas, namespaces, tables, columns, constraints, foreign keys, dependencies, cycles, snapshots, and exports. |
| **Frontend Foundation** | Phase 7.1 | Merged & Active | Next.js App Router, Tailwind CSS v4, Radix primitives, dark/light theme, typed `DeraApiClient`, application shell. |
| **Auth & Workspaces** | Phase 7.2 | Merged & Active | Login, registration, password guidance, workspace listing & creation, role-based member management with last-owner protection. |

---

## 3. Gap Analysis & Architecture Decisions

1. **Connection Management Endpoints**:
   - Provide `/api/v1/connectors/engines` returning engine discovery descriptors and supported providers.
   - Provide `/api/v1/connections/test` for ephemeral, non-persisted diagnostic connectivity checks.
   - Provide workspace-scoped CRUD endpoints under `/api/v1/workspaces/{workspace_id}/connections`.
   - Provide connection test and schema inspection triggers under `/api/v1/workspaces/{workspace_id}/connections/{connection_id}/test` and `/inspect`.
   - Never return plaintext passwords or secrets in API responses.

2. **Schema Explorer Routes & Components**:
   - `/connections`: Workspace connection listing, engine badges, status indicators, and delete/test actions.
   - `/connections/new`: Engine selector and guided forms for PostgreSQL, Supabase, MySQL, MariaDB, and contained SQLite.
   - `/connections/[connectionId]`: Connection overview, safe metadata display, testing panel, and schema inspection trigger.
   - `/schemas`: Schema directory and summary catalog within active workspace.
   - `/schemas/[schemaId]`: Split-pane explorer layout with database navigation tree, namespace nodes, table items, search, filtering, and tabbed inspectors (Overview, Columns, Constraints, Indexes, Provenance).

3. **Security & Zero-AI Invariants**:
   - Strict Zero-AI compliance: zero machine learning, LLM, or external generative dependencies.
   - No direct database connections from the browser.
   - SQL check expressions and identifiers rendered as sanitized, inert text to prevent XSS.
   - SQLite filesystem containment: arbitrary client-provided server paths are rejected.
   - Workspace boundary enforcement: all requests verified against active workspace context headers.

---

## 4. Implementation Plan

1. **Backend Integration**: Implement connection routes (`/api/v1/connectors/engines`, `/api/v1/connections/test`, and `/api/v1/workspaces/{workspace_id}/connections`).
2. **Frontend Typed API Client**: Extend `DeraApiClient` with connections and schema explorer service modules.
3. **Connection UI**: Build connection list, engine selection, guided forms, diagnostic tester, and detail view.
4. **Schema Explorer UI**: Build split-pane layout, database tree, namespace filter, table inspector, column table, constraint cards, index view, and completeness indicators.
5. **Testing Suite**: Unit tests, component tests, accessibility checks, authorization validation, and Next.js build verification.
6. **Documentation & Acceptance**: Complete technical documentation and formal acceptance audit.
