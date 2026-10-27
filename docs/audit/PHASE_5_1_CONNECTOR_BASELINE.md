# DERA Milestone 5.1 Connector Baseline Audit: Connector Interface & Capability Model

**Milestone:** Phase 5.1 — Connector Interface & Capability Model  
**Audit Date:** 2026-10-27  
**Base Commit SHA:** `82071dbe4bb070f98ac5fc690223e8f003d9c7c4`  
**Default Branch:** `main`  
**Maintainer:** Bunga Krishanth (`@krishanth7`)  
**Standard:** Deterministic, extensible, read-only, least-privilege, tenant-isolated, strongly typed  

---

## 1. Baseline Repository Inspection

A live audit was conducted on repository `https://github.com/krishanth7/dera` at commit `82071dbe4bb070f98ac5fc690223e8f003d9c7c4`.

### Subsystem Verification Matrix

| Subsystem | Verified Infrastructure | Readiness Status | Evidence |
|---|---|---|---|
| **FastAPI Core (Phase 4.1)** | Lifespan, CORS, Request ID, Error Handling | **READY** | `apps/api/src/dera_api/factory.py`, `tests/unit/test_api_lifespan.py` |
| **API Contracts (Phase 4.2)** | Pydantic v2 schemas, RFC 9457 errors, OpenAPI 3.1 | **READY** | `apps/api/src/dera_api/contracts/`, `openapi.v1.json` (0 drift) |
| **PostgreSQL Persistence (Phase 4.3)** | SQLAlchemy 2.x async pooling, Alembic migrations | **READY** | `apps/api/src/dera_api/db/`, `migrations/versions/001-003` |
| **Identity & RBAC (Phase 4.4)** | Argon2id auth, sessions, workspace memberships | **READY** | `apps/api/src/dera_api/auth/`, `tests/authorization/` |
| **Background Processing (Phase 4.5)** | Transactional outbox, Celery/Redis, allowlisted tasks | **READY** | `apps/api/src/dera_api/jobs/`, `apps/api/src/dera_api/workers/` |
| **Connector Layer (Legacy / Baseline)** | Minimal synchronous BaseConnector & SqliteConnector | **READY FOR 5.1** | `packages/connectors/src/dera_connectors/base/` |

---

## 2. Gap Analysis for Milestone 5.1

1. **Protocol & Async Lifecycle:** Current `BaseConnector` is synchronous and lacks async context management, explicit connection lifecycle states (`CREATED`, `CONNECTING`, `CONNECTED`, `FAILED`, `CLOSING`, `CLOSED`), cancellation tokens, and timeouts.
2. **Capability Model:** No typed capability registry exists to report supported introspection operations (`SCHEMA_ENUMERATION`, `TABLE_ENUMERATION`, `COLUMN_INSPECTION`, `VIEW_INSPECTION`, etc.) or differentiate engine capabilities from permission restrictions.
3. **Universal Metadata Contracts:** Missing strongly-typed Pydantic v2 models for schemas, tables, columns, constraints (PK, FK, Unique, Check), indexes, and views with deterministic ordering.
4. **Error Taxonomy:** Missing standardized error codes (`CONNECTOR_UNAVAILABLE`, `CONNECTOR_AUTHENTICATION_FAILED`, `CONNECTOR_PERMISSION_DENIED`, `CONNECTOR_TIMEOUT`, etc.) that prevent raw connection string leakage.
5. **Registry & Factory:** No explicit connector registry resolving database engines without dynamic arbitrary imports.
6. **Testing & Conformance:** No deterministic mock connector or reusable adapter conformance suite.
7. **Security & SSRF Safeguards:** Missing egress target validation (blocking loopback, link-local, cloud metadata IPs).

---

## 3. Scope Definition

Phase 5.1 delivers **Layer B (Connector Abstraction)**:
- Connector protocol, engine identities, capability model, universal metadata models, configuration and credential boundaries, connection lifecycle, error taxonomy, read-only policy, registry, adapter factory, deterministic fake connector, and conformance test suite.
- Full production database-specific connectors (PostgreSQL/Supabase, SQLite, MySQL/MariaDB) belong to subsequent milestones (Phases 5.2–5.4).
