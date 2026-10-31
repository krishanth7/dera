# Phase 7.2 Authentication, Workspaces & User Management UI — Baseline Audit

**Document Reference**: `docs/audit/PHASE_7_2_AUTH_BASELINE.md`
**Milestone**: Phase 7.2 — Authentication, Workspaces & User Management UI
**Implementation Branch**: `feat/phase-7.2-auth-workspaces-user-management`
**Base Commit SHA**: `9ad1452a23ebf908e08d66dfab0389ca4453545b`
**Audit Date**: October 2026
**Auditors**: Principal Frontend Architect, Identity & Access Management Architect, AppSec Engineer

---

## 1. Executive Summary

This baseline audit evaluates the backend identity, session, and workspace API contracts implemented in Phase 4.4 and the frontend foundation established in Phase 7.1. It specifies the verified backend contracts, exact role taxonomy, CSRF cookie mechanics, supported vs. planned identity workflows, security requirements, and the technical implementation roadmap for Phase 7.2.

---

## 2. Verified Backend Identity Contracts

### 2.1 Authentication Endpoints (`/api/v1/auth`)

| Endpoint | Method | Contract Details | Transport / Security |
|:---|:---:|:---|:---|
| `/api/v1/auth/register` | `POST` | `RegisterRequest` (`email`, `password`) → `AuthResponse` (`user`, `session_id`, `csrf_token`, `expires_at`) | Sets `dera_session` (HttpOnly, Secure) + `dera_csrf` cookies |
| `/api/v1/auth/login` | `POST` | `LoginRequest` (`email`, `password`) → `AuthResponse` | IP+Email rate limiting (5 attempts/15m), Secure cookies |
| `/api/v1/auth/logout` | `POST` | Requires `verify_csrf` (`x-csrf-token` header or double-submit cookie) | Revokes active session, clears cookies (`204 No Content`) |
| `/api/v1/auth/logout-all` | `POST` | Requires `verify_csrf` | Revokes all user sessions across devices (`204 No Content`) |
| `/api/v1/auth/me` | `GET` | Authenticated session check → `UserResponse` (`id`, `email`, `status`, `created_at`) | Returns 401 if unauthenticated or session expired |

### 2.2 Workspace & Member Endpoints (`/api/v1/workspaces`)

| Endpoint | Method | Required Permission | Description |
|:---|:---:|:---:|:---|
| `/api/v1/workspaces` | `GET` | Authenticated | Lists all workspaces for current user with their active role |
| `/api/v1/workspaces` | `POST` | Authenticated + CSRF | Creates workspace (`name`, `slug`), assigns creator as `owner` |
| `/api/v1/workspaces/{slug}` | `GET` | `workspace:read` | Returns workspace details and current user role |
| `/api/v1/workspaces/{slug}/members` | `GET` | `member:read` | Lists all members (`id`, `user_id`, `user_email`, `role`, `status`) |
| `/api/v1/workspaces/{slug}/members` | `POST` | `member:invite` + CSRF | Adds/invites member (`email`, `role`) with role transition validation |
| `/api/v1/workspaces/{slug}/members/{user_id}` | `PATCH` | `member:update_role` + CSRF | Updates member role (`role`), enforces last-owner safeguard |
| `/api/v1/workspaces/{slug}/members/{user_id}` | `DELETE` | `member:remove` + CSRF | Removes member, prevents removing the last owner |

---

## 3. Authoritative Role & Permission Model

Roles are defined in `WorkspaceRole` (`dera_api.auth.roles`):
1. **`owner`**: Full administrative authority, workspace deletion, cannot be demoted or removed if last owner.
2. **`admin`**: Workspace management, member invitations, role updates (up to Admin), member removal.
3. **`editor`**: Schema read, snapshot create/verify, export create/read.
4. **`viewer`**: Read-only workspace and schema inspection.

---

## 4. Supported vs. Unsupported Workflows

| Capability | Backend Status | Phase 7.2 UI Implementation |
|:---|:---:|:---|
| **User Sign-In** | **Supported** | Full interactive form with real `/login` endpoint integration |
| **User Registration** | **Supported** | Full interactive form with `/register` endpoint |
| **Session Restoration** | **Supported** | Automatic restoration via `/api/v1/auth/me` on startup |
| **Single & All Logout** | **Supported** | Secure logout invoking `/logout` and `/logout-all` with CSRF tokens |
| **Workspace Listing & Switching** | **Supported** | Header dropdown and `/workspaces` dedicated selection view |
| **Workspace Creation** | **Supported** | Modal and dedicated creation flow with slug generation |
| **Member Directory** | **Supported** | Enterprise data table with roles, status, and join date |
| **Add / Invite Member** | **Supported** | Direct member addition via email and role with backend validation |
| **Update Member Role** | **Supported** | Role modification modal with last-owner protection safeguards |
| **Remove Member** | **Supported** | Destructive confirmation dialog with last-owner protection |
| **Password Recovery / Reset** | **Planned (Backend)** | Truthful informative state explaining enterprise self-hosted/recovery status |
| **Standalone Invitation Tokens** | **Planned (Backend)** | Direct member provisioning supported; external email tokens scheduled |

---

## 5. Security & Session Integrity

1. **Zero Client-Side Credentials**: No passwords, database credentials, or auth tokens in `localStorage`/`sessionStorage`.
2. **Double-Submit CSRF**: State-changing operations (POST/PATCH/DELETE) extract the CSRF token from the `dera_csrf` cookie and transmit it in the `X-CSRF-Token` header.
3. **Tenant Context Isolation**: Switching workspaces invalidates cached membership and ensures no cross-workspace state contamination.
4. **Safe Redirects**: Post-login redirect sanitization blocks open redirects and external URLs.
