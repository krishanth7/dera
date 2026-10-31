# Phase 6.6 Reverse Engineering APIs & Exports — Implementation Baseline

**Document Reference**: `docs/audit/PHASE_6_6_API_BASELINE.md`  
**Milestone**: Phase 6.6 — Reverse Engineering APIs & Exports  
**Implementation Branch**: `feat/phase-6.6-reverse-engineering-api-exports`  
**Base Commit SHA**: `455de3c91edbafd18930c1ded913108d9ad8aade`  
**Audit Date**: October 2026  
**Auditor**: Principal Software Architect & Application Security Engineer  

---

## 1. Executive Summary

Phase 6.6 bridges DERA's Reverse Engineering Core Engine (Phases 6.1–6.5) with client-facing interfaces by delivering a production-grade, versioned REST API (`/api/v1/reverse-engineering`) and a deterministic multi-format export subsystem (`dera.reverse_engineering.exports`).

This baseline audit assesses repository prerequisites, evaluates existing API patterns and security architectures, identifies missing capabilities, analyzes security surfaces, and defines the definitive implementation sequence.

---

## 2. Verified Prerequisites

| Prerequisite Milestone | Status | Key Verified Artifacts |
| :--- | :--- | :--- |
| **Phase 4.1 Backend Foundation** | Merged & Certified | FastAPI application factory, lifespan management, structured logging. |
| **Phase 4.2 API Contracts** | Merged & Certified | RFC 9457 `ProblemDetail` errors, versioned router prefix `/api/v1`. |
| **Phase 4.3 Database & Migrations** | Merged & Certified | PostgreSQL database models, Alembic migrations, session management. |
| **Phase 4.4 Authentication & RBAC** | Merged & Certified | Session token verification, CSRF defense, default-deny RBAC policies. |
| **Phase 4.5 Background Workers** | Merged & Certified | `JobService`, transactional outbox, allowlisted `TaskRegistry`. |
| **Phase 4.6 Observability** | Merged & Certified | Structured JSON logs, OpenTelemetry spans, metrics middleware. |
| **Phase 5 Connectors** | Merged & Certified | PostgreSQL, SQLite, MySQL, MariaDB connectors; read-only enforcement. |
| **Phase 5.5 Canonical Metadata & Identity** | Merged & Certified | `ObjectId` generation, canonical domain models. |
| **Phase 6.1 Schema Representation** | Merged & Certified | `SchemaRepresentation`, `ObjectRegistry`, `TypedRef`, `ForeignKeyReference`. |
| **Phase 6.2 Structural Reconstruction** | Merged & Certified | `StructuralReconstructionBuilder`, reconstructed entities. |
| **Phase 6.3 Relationship Graph** | Merged & Certified | `ForeignKeyGraph`, directed multigraph adjacency, composite edges. |
| **Phase 6.4 Dependency Analysis** | Merged & Certified | `DependencyAnalyzer`, Tarjan SCCs, Johnson elementary cycles, Kahn ordering. |
| **Phase 6.5 Schema Snapshots** | Merged & Certified | `SchemaSnapshot`, RFC 8785 canonical serialization, SHA-256 fingerprints. |

---

## 3. Existing Reusable Components

1. **FastAPI Router Hierarchy**: `api_v1_router` in `dera_api.api.v1.router` mounts modular sub-routers with standard RFC 9457 problem detail responses.
2. **Authentication & Tenancy Dependencies**:
   - `get_current_user`: Resolves authenticated `User`.
   - `require_workspace_permission_by_id`: Verifies active workspace membership and role permissions.
   - `verify_csrf`: Enforces double-submit CSRF cookie checks on state-changing requests.
3. **Core Reverse Engineering Engines**:
   - `SchemaRepresentation` and `SchemaBuilder` (`dera.reverse_engineering`)
   - `ForeignKeyGraph` and `ForeignKeyGraphBuilder` (`dera.reverse_engineering.graph`)
   - `DependencyAnalyzer` and `DependencyAnalysisResult` (`dera.reverse_engineering.dependencies`)
   - `SchemaSnapshot`, `SchemaSnapshotBuilder`, and `FileSystemSnapshotStorage` (`dera.reverse_engineering.snapshots`)
4. **Asynchronous Task Infrastructure**:
   - `TaskRegistry` and `JobService` (`dera_api.jobs`)

---

## 4. Gap Analysis & Missing Capabilities

1. **HTTP Endpoint Layer**:
   - No REST routes exist under `/api/v1/reverse-engineering/` to expose schemas, namespaces, tables, columns, constraints, relationships, dependencies, cycles, or snapshots.
2. **Export Engine**:
   - No structured export subsystem exists in `packages/core/src/dera/reverse_engineering/exports/`.
   - Missing deterministic JSON, CSV (with formula injection defense), GraphML (valid XML), DOT (safe Graphviz), and canonical snapshot exporters.
3. **Export Job Processing**:
   - Background task handler `reverse_engineering.export` not yet registered in `TaskRegistry`.
   - Artifact download endpoint with MIME typing and Content-Disposition not yet implemented.
4. **RBAC Permission Tokens**:
   - `Permission` enum needs dedicated reverse engineering tokens (`schema:read`, `snapshot:create`, `snapshot:read`, `snapshot:verify`, `export:create`, `export:read`).

---

## 5. Security & Risk Analysis

1. **Tenant / Workspace Boundary Isolation**:
   - *Risk*: A user in Workspace A queries a `schema_id`, `table_id`, `snapshot_id`, or `export_id` belonging to Workspace B.
   - *Mitigation*: All endpoints must validate workspace membership server-side, resolve resources within the caller's workspace, and return 404 on cross-tenant requests.
2. **CSV Formula Injection**:
   - *Risk*: Exported table or column names containing `=cmd|...` or `-2+3` execute arbitrary code when opened in spreadsheet software (Excel, LibreOffice).
   - *Mitigation*: Implement spreadsheet-safe CSV escaping by prefixing leading dangerous characters (`=`, `+`, `-`, `@`, `\t`, `\r`) with single quotes (`'`).
3. **GraphML XML & DOT Statement Injection**:
   - *Risk*: Malicious identifiers injecting XML entities or closing tags in GraphML, or injecting Graphviz DOT syntax.
   - *Mitigation*: Strict XML entity escaping via `xml.sax.saxutils.escape` and DOT string escaping/quoting.
4. **Export Denial of Service (DoS)**:
   - *Risk*: Enormous schemas triggering out-of-memory or high CPU spikes during export generation.
   - *Mitigation*: Enforce resource limits (`ExportResourceLimits`), bound graph traversal depth, and process heavy exports asynchronously via background worker jobs.

---

## 6. Implementation Plan

1. **Core Export Package (`packages/core/src/dera/reverse_engineering/exports/`)**:
   - Define export data models, formats (`JSON`, `CSV`, `GRAPHML`, `DOT`, `SNAPSHOT`), and limits.
   - Implement `JSONExporter`, `CSVExporter` (with formula injection protection), `GraphMLExporter`, `DOTExporter`, and `SnapshotExporter`.
   - Implement `ExportRegistry` and `ExportService`.
2. **RBAC & Authorization Extensions (`apps/api/src/dera_api/auth/`)**:
   - Add reverse engineering permission tokens to `Permission` and `ROLE_PERMISSIONS`.
3. **REST API Endpoints (`apps/api/src/dera_api/api/v1/endpoints/reverse_engineering/`)**:
   - Schema and hierarchy endpoints (schemas, namespaces, tables, columns, constraints).
   - Relationship graph endpoints (graph, direct table relationships).
   - Dependency & cycle endpoints (dependencies, table dependencies, elementary cycles).
   - Snapshot endpoints (create, list, get, verify).
   - Export endpoints (request export, get export job status, download artifact).
4. **Export Job Worker Integration**:
   - Register `reverse_engineering.export` in `TaskRegistry`.
5. **Testing Suite (`tests/reverse_engineering/phase_6_6/`)**:
   - Unit tests for all exporters.
   - Contract and authorization tests.
   - Security tests (CSV injection, XML escaping, DOT escaping, tenant isolation).
   - Determinism tests (identical bytes).
   - Performance benchmarks.
6. **Documentation & Audits**:
   - Complete 20 documentation deliverables.
   - Author `PHASE_6_6_API_EXPORT_ACCEPTANCE.md` and `PHASE_6_COMPLETENESS.md`.
