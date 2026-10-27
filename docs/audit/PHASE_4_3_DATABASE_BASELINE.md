# DERA Phase 4.3 — Platform PostgreSQL Database & Migrations Baseline Audit

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
> **Maintainer:** Bunga Krishanth (`@krishanth7`)  
> **Phase:** 4 — Backend & Platform Infrastructure  
> **Milestone:** 4.3 — Platform PostgreSQL Database & Migrations  
> **Execution Date:** 2026-10-27  
> **Base Commit SHA:** `0a20811eefea237a3e75a3eafe11db843469e88f`  
> **Base Branch:** `feat/phase-4.2-api-contracts-validation` (PR #38 ready, targeting `main` at `61cad34a33846289168faaea7d4fab1f4e0fdefc`)  

---

## 1. Executive Summary & Prerequisite Audit

Phase 4.1 established the FastAPI application foundation (application factory, lifespan management, typed configuration, and container health probes). Phase 4.2 established the canonical API contract layer (Pydantic v2 request/response envelopes, RFC 9457 Problem Details error models, error taxonomy, identifier validators, and zero-drift OpenAPI 3.1 governance).

This baseline audit evaluates DERA's state prior to constructing the internal platform PostgreSQL persistence layer. Currently:
1. **Zero Internal Platform Persistence**: DERA lacks any internal operational metadata storage, migration infrastructure, or async database session lifecycle.
2. **Customer Database Separation**: Customer database introspection is strictly confined to read-only connector abstractions in `packages/connectors/`. No platform database tables or migrations may ever target customer databases.
3. **CI PostgreSQL Service**: GitHub Actions CI already provisions a live `postgres:16-alpine` service container in the `database-integration` job.

---

## 2. Existing Repository State & Gap Analysis

| Component | Current State | Required Phase 4.3 Architecture | Gap Assessment |
|---|---|---|---|
| **PostgreSQL Driver** | None configured in dependencies | `asyncpg` (v0.29+) with SQLAlchemy 2.x async engine | Needs integration in `pyproject.toml` and CI |
| **ORM / Core Base** | No SQLAlchemy models | `DeclarativeBase` with typed `Mapped` attributes and deterministic naming conventions | Missing; must be created under `apps/api/src/dera_api/db/` |
| **Engine & Pool** | No engine factory | Async engine factory (`create_database_engine`) with configurable pool bounds and timeouts | Missing; must support safe lifecycle and dispose |
| **Session Lifecycle** | No sessionmaker | `async_sessionmaker` yielding isolated `AsyncSession` per request / unit of work | Missing; must integrate with FastAPI dependency injection |
| **Migration Engine** | No Alembic configuration | Alembic 1.13+ configured for async migrations under `migrations/` and `alembic.ini` | Missing; must be created without committed credentials |
| **Initial Schema** | No internal tables | Minimal platform metadata table (`dera_platform_metadata`) storing version and state | Missing; must be created via initial revision |
| **Health Probe** | `/health/ready` reports static status | Truthful readiness probe testing platform DB connectivity (`SELECT 1;`) with timeout | Needs integration with database engine |
| **Error Handling** | Generic exception handlers | Database exceptions mapped to `ErrorCode.DEPENDENCY_UNAVAILABLE` or `CONFLICT` | Needs mapping without leaking raw SQL or credentials |

---

## 3. Strict Database Separation Invariant

```text
+---------------------------------------------------------------------------------+
|                                 DERA PLATFORM                                   |
|                                                                                 |
|  [FastAPI Backend] ---> [AsyncSession] ---> [SQLAlchemy 2.x]                   |
|                                                     |                           |
|                                                     v (postgresql+asyncpg://)   |
|                                     +-------------------------------+           |
|                                     |    DERA Platform Database     |           |
|                                     |   (Internal Metadata Only)    |           |
|                                     +-------------------------------+           |
+---------------------------------------------------------------------------------+

                      STRICT ARCHITECTURAL SEPARATION
                                   (NO SHARING)

+---------------------------------------------------------------------------------+
|                         CUSTOMER INSPECTED DATABASES                            |
|                                                                                 |
|  [Schema Extractor (Phase 5)] ---> [Read-Only Connector]                        |
|                                              |                                  |
|                                              v (PRAGMA / SET TRANSACTION RO)    |
|                                     +-------------------------------+           |
|                                     |  External Customer Database   |           |
|                                     | (Strictly Read-Only, No DDL)  |           |
|                                     +-------------------------------+           |
+---------------------------------------------------------------------------------+
```

* **No Migration of Customer Databases**: Alembic migrations operate strictly against `DERA_PLATFORM_DATABASE_URL`.
* **No Connection Sharing**: Customer database credentials and platform database credentials are fundamentally isolated.

---

## 4. Security & Risk Analysis

1. **Credential Exposure Risk**: Database passwords must never appear in `alembic.ini`, source code, logs, or error responses. Handled via environment variables (`DERA_PLATFORM_DATABASE_URL`), `SecretStr` masking, and structured log sanitization.
2. **Connection Leak Risk**: Unclosed sessions or unbounded connection pools can exhaust database limits. Handled via explicit async context managers (`async with session:`) and bounded pool defaults (`pool_size=10`, `max_overflow=5`).
3. **Automatic Startup Migration Hazard**: Running `alembic upgrade head` inside FastAPI startup can cause race conditions in scaled deployments. Handled by decoupling migration execution into dedicated operational commands and CI steps.
4. **Information Disclosure in Errors**: Database constraint violations must not echo table contents, connection strings, or internal hosts to clients. Handled by sanitizing errors into canonical RFC 9457 `ProblemDetail` structures.

---

## 5. Implementation Roadmap for Phase 4.3

1. **Dependencies & Configuration**:
   * Add `sqlalchemy>=2.0.0`, `alembic>=1.13.0`, `asyncpg>=0.29.0`, and `aiosqlite>=0.20.0` to `pyproject.toml`.
   * Extend `Settings` in `apps/api/src/dera_api/core/config.py` with database pool and URL settings.
2. **Database Core Infrastructure**:
   * Create `apps/api/src/dera_api/db/base.py`: Declarative base with deterministic naming convention.
   * Create `apps/api/src/dera_api/db/engine.py`: Async engine factory with pool pre-ping, statement timeouts, and disposal.
   * Create `apps/api/src/dera_api/db/session.py`: Async session factory and explicit transaction manager.
   * Create `apps/api/src/dera_api/db/dependencies.py`: FastAPI `get_db_session` dependency.
   * Create `apps/api/src/dera_api/db/health.py`: Bounded `check_database_health()` (`SELECT 1;`).
   * Create `apps/api/src/dera_api/db/exceptions.py`: Persistence error classifier and sanitizer.
3. **Initial Platform Schema & Models**:
   * Create `apps/api/src/dera_api/db/models/platform.py`: `PlatformMetadata` model (`key`, `value`, `updated_at`).
4. **Alembic Migrations**:
   * Configure `alembic.ini` and `migrations/` with async SQLAlchemy support.
   * Generate initial migration `001_initial_platform_metadata.py`.
5. **Lifespan & Readiness Integration**:
   * Wire engine initialization and disposal into `apps/api/src/dera_api/core/lifespan.py`.
   * Wire `check_database_health` into `/health/ready` probe.
6. **Local Development & Docker**:
   * Provide `docker-compose.db.yml` for local PostgreSQL 16 development.
7. **Comprehensive Test Suites**:
   * Unit tests for engine, session, transactions, models, constraints, health, and error sanitization in `tests/database/`.
   * Live PostgreSQL 16 integration tests for migrations and transactions.
8. **Documentation Deliverables**:
   * Complete architecture, configuration, local setup, migration policy, and recovery documentation in `docs/database/`.
9. **Final Acceptance Audit & Pull Request**:
   * Record audit in `docs/audit/PHASE_4_3_DATABASE_ACCEPTANCE.md`.
   * Open PR `feat(database): complete Phase 4.3 PostgreSQL and migration foundation`.
