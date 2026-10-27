# DERA Authentication & Workspace API Specification

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Maintainer:** Bunga Krishanth  
**API Version:** v1 (`/api/v1`)  
**Standard:** OpenAPI 3.1.0, RFC 9457 Problem Details for HTTP APIs  
**License:** [MIT License](../../LICENSE)  

---

## 1. Overview & Authentication Methods

The DERA Platform API supports two authentication mechanisms:
1. **Cookie-Based Sessions (Browser Clients):**
   - Session Cookie: `dera_session` (`HttpOnly`, `Secure`, `SameSite=Lax`).
   - CSRF Cookie: `dera_csrf` (`Secure`, `SameSite=Lax`).
   - Required Mutation Header: `X-CSRF-Token: <dera_csrf_value>` on `POST`, `PUT`, `PATCH`, `DELETE`.
2. **Bearer Token Header (CLI / SDK Clients):**
   - Header: `Authorization: Bearer <session_token>`.
   - Bypasses CSRF checks automatically since ambient browser cookies are not utilized.

All errors strictly conform to **RFC 9457 Problem Details** with canonical types and localized machine-readable codes.

---

## 2. Authentication Endpoints (`/api/v1/auth`)

### 2.1 Register User Account

Creates a new platform user identity, hashes the password with Argon2id, creates an initial active session, and attaches session cookies.

- **Endpoint:** `POST /api/v1/auth/register`
- **Authentication:** None (Public)
- **Status Code:** `201 Created`

#### Request Body

```json
{
  "email": "engineer@example.com",
  "password": "correct-horse-battery-staple-2026"
}
```

#### Response Body (`201 Created`)

```json
{
  "user": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "email": "engineer@example.com",
    "status": "active",
    "created_at": "2026-10-27T10:00:00Z",
    "updated_at": "2026-10-27T10:00:00Z"
  },
  "session_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "csrf_token": "9f8e7d6c5b4a3210...",
  "expires_at": "2026-10-28T10:00:00Z"
}
```

---

### 2.2 Login (Authenticate Session)

Validates credentials against Argon2id hash with rate-limiting protection. Issues a new opaque 256-bit session token.

- **Endpoint:** `POST /api/v1/auth/login`
- **Authentication:** None (Public)
- **Status Code:** `200 OK`

#### Request Body

```json
{
  "email": "engineer@example.com",
  "password": "correct-horse-battery-staple-2026"
}
```

#### Response Body (`200 OK`)

Returns the identical `AuthResponse` structure as registration, and sets `dera_session` and `dera_csrf` cookies.

---

### 2.3 Logout (Revoke Active Session)

Revokes the calling active session and instructs the client to delete cookies.

- **Endpoint:** `POST /api/v1/auth/logout`
- **Authentication:** Required (`dera_session` cookie or `Authorization: Bearer <token>`)
- **CSRF Defense:** Mandatory `X-CSRF-Token` header if authenticated via cookie.
- **Status Code:** `204 No Content`

---

### 2.4 Logout All (Revoke All Sessions)

Revokes all active sessions for the current authenticated user across all devices.

- **Endpoint:** `POST /api/v1/auth/logout-all`
- **Authentication:** Required
- **CSRF Defense:** Mandatory `X-CSRF-Token` header if authenticated via cookie.
- **Status Code:** `204 No Content`

---

### 2.5 Current User Introspection (`/api/v1/auth/me`)

Returns the profile of the current authenticated user.

- **Endpoint:** `GET /api/v1/auth/me`
- **Authentication:** Required
- **Status Code:** `200 OK`

---

## 3. Workspaces & Membership Endpoints (`/api/v1/workspaces`)

### 3.1 Create Workspace

Creates a new tenant workspace and automatically registers the calling user as the initial `owner`.

- **Endpoint:** `POST /api/v1/workspaces`
- **Authentication:** Required
- **Status Code:** `201 Created`

#### Request Body

```json
{
  "name": "Acme Database Engineering",
  "slug": "acme-db-eng"
}
```

---

### 3.2 List Workspaces

Lists all active workspaces where the calling user holds an active membership.

- **Endpoint:** `GET /api/v1/workspaces`
- **Authentication:** Required
- **Status Code:** `200 OK`

---

### 3.3 Get Workspace Details

Retrieves workspace metadata and the caller's active role.

- **Endpoint:** `GET /api/v1/workspaces/{slug}`
- **Authentication:** Required (User must be an active member)
- **Status Code:** `200 OK`

---

### 3.4 Manage Workspace Members

- `GET /api/v1/workspaces/{slug}/members` (Requires `member:read`)
- `POST /api/v1/workspaces/{slug}/members` (Requires `member:invite`)
- `PATCH /api/v1/workspaces/{slug}/members/{user_id}` (Requires `member:update_role`)
- `DELETE /api/v1/workspaces/{slug}/members/{user_id}` (Requires `member:remove`)
