# DERA Phase 4.4 — Identity, Authentication & RBAC Baseline Audit

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
> **Maintainer:** Bunga Krishanth (`@krishanth7`)  
> **Development Phase:** 4 — Backend & Platform Infrastructure  
> **Milestone:** 4.4 — Authentication, Authorization & Role-Based Access Control  
> **Audit Date:** 2026-10-27  
> **Base Commit SHA:** `53efc2ff80cb661d6b72af3fc0b5bd67997f98c8`  
> **Branch:** `feat/phase-4.4-auth-rbac`  
> **Audit Status:** **QUALIFIED** (Prerequisites Verified, Ready for Implementation)

---

## 1. Executive Summary

Milestone 4.4 implements DERA's authoritative identity, authentication, session management, workspace tenancy, role-based access control (RBAC), and security audit infrastructure.

This audit evaluates the repository state following the completion of Milestone 4.3 (Platform PostgreSQL Database & Migrations) and validates all foundational components required for Phase 4.4.

---

## 2. Prerequisite Phase Verification

| Phase | Description | Status | Evidence / Notes |
| :--- | :--- | :--- | :--- |
| **Phase 4.1** | Python/FastAPI Application Foundation | **PASS** | Lifespan management, application factory, configuration, security middleware, and health probes verified. |
| **Phase 4.2** | API Contracts, Validation & Error Handling | **PASS** | RFC 9457 Problem Details schema, canonical error taxonomy, and OpenAPI drift verification verified. |
| **Phase 4.3** | Platform PostgreSQL Database & Migrations | **PASS** | SQLAlchemy 2.x async engine, session factory, `transaction_scope`, Alembic async migrations, `PlatformMetadata`, and live PostgreSQL 16 CI test suite verified. |

---

## 3. Existing Identity & Security Baseline

1. **Authentication Code:**
   - Currently, the API has no authentication endpoints or user identity models. All endpoints (e.g., `/health/live`, `/health/ready`, `/api/v1/system/info`) are either operational or unauthenticated system diagnostics.
2. **Session Management:**
   - No session management or token issuance exists.
3. **Authorization & Tenancy:**
   - No workspace entities, membership roles, or permission registries exist.
4. **Security Middleware:**
   - `SecurityHeadersMiddleware` is active and injects `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, and `X-DERA-Policy`.
5. **Database Persistence Infrastructure:**
   - `apps/api/src/dera_api/db/`: Asynchronous engine (`create_database_engine`), `AsyncAdaptedQueuePool`, `async_sessionmaker`, `transaction_scope`, and `PlatformMetadata` ORM model.
   - `migrations/versions/001_initial_platform_metadata.py`: Initial revision establishing `dera_platform_metadata`.

---

## 4. Threat Model & Security Considerations Preview

1. **Credential Stuffing & Brute Force:**
   - *Mitigation:* Argon2id password hashing, constant-time verification, login attempt rate-limiting, and generic failure messages without account enumeration.
2. **Session Hijacking & Fixation:**
   - *Mitigation:* Cryptographically secure 256-bit random session tokens; only SHA-256 token hashes are stored in the database. Tokens are rotated upon privilege escalation.
3. **Cross-Site Request Forgery (CSRF):**
   - *Mitigation:* For cookie-based authentication, double-submit cookie or signed `X-CSRF-Token` validation on state-changing requests (POST, PUT, PATCH, DELETE) paired with `SameSite=Lax` / `SameSite=Strict`.
4. **Cross-Tenant & Broken Object-Level Authorization (BOLA/IDOR):**
   - *Mitigation:* Strict workspace scoping on all resource queries (`WHERE workspace_id = :ws_id`); membership and permission validation enforced in dependency injection before accessing domain models.
5. **Privilege Escalation:**
   - *Mitigation:* Centralized, deterministic RBAC registry with `Owner`, `Admin`, `Editor`, and `Viewer` roles. Default deny policy. Safeguards preventing removing the final owner or self-demoting without a successor.

---

## 5. Required Implementation Scope

1. **Identity & Workspace Models (SQLAlchemy 2.x):**
   - `User` (`dera_users`): `id` (UUID), `email` (normalized, unique), `password_hash`, `status`, `email_verified_at`, `created_at`, `updated_at`.
   - `UserSession` (`dera_user_sessions`): `id` (UUID), `user_id`, `token_hash`, `ip_address`, `user_agent`, `expires_at`, `revoked_at`, `created_at`, `last_seen_at`.
   - `Workspace` (`dera_workspaces`): `id` (UUID), `name`, `slug` (unique), `status`, `created_at`, `updated_at`.
   - `WorkspaceMembership` (`dera_workspace_memberships`): `id` (UUID), `workspace_id`, `user_id`, `role`, `status`, `created_at`, `updated_at` (composite unique `[workspace_id, user_id]`).
   - `SecurityAuditEvent` (`dera_security_audit_events`): `id` (UUID), `event_type`, `actor_user_id`, `workspace_id`, `target_type`, `target_id`, `request_id`, `created_at`, `metadata`.
2. **Alembic Migration:**
   - `002_identity_and_workspaces.py` with full upgrade and downgrade reversibility.
3. **Password Security:**
   - Argon2id via `argon2-cffi` (`PasswordHasher`), NIST SP 800-63B aligned policy (min 12, max 128 chars).
4. **Session Engine & Cookie Management:**
   - Opaque 64-char hex tokens, SHA-256 database storage, cookie/bearer extraction, revocation and logout.
5. **CSRF Protection:**
   - Double-submit CSRF cookie & header validation.
6. **RBAC & Authorization Engine:**
   - Deterministic role-to-permission mapping, `require_authenticated_user`, `require_workspace_permission`.
7. **API Endpoints:**
   - `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/logout`, `/api/v1/auth/me`, `/api/v1/auth/logout-all`.
   - `/api/v1/workspaces/`, `/api/v1/workspaces/{slug}`, `/api/v1/workspaces/{slug}/members`.
8. **Test Matrix:**
   - Unit tests (passwords, sessions, roles, email normalization, CSRF).
   - Integration tests (registration, login, logout, current user, audit logging).
   - Tenant isolation tests (Workspace A vs Workspace B negative matrix).
   - Session security & abuse tests (rate limits, revocation, expiration).
