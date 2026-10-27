# DERA Session Management Architecture

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Maintainer:** Bunga Krishanth  
**Security Standard:** OWASP Session Management Cheat Sheet, NIST SP 800-63B  
**License:** [MIT License](../../LICENSE)  

---

## 1. Overview & Core Philosophy

DERA's session management is built on **server-managed opaque tokens** with high-entropy cryptographic generation, one-way SHA-256 database hashing, and defensive browser cookie configurations.

```mermaid
flowchart TD
    GEN[CSPRNG: secrets.token_hex(32)<br/>256 bits of entropy] --> RAW[Raw Token: 64 hex chars]
    RAW --> COOKIE[Browser Set-Cookie: dera_session<br/>HttpOnly, Secure, SameSite=Lax]
    RAW --> HASH[hash_session_token: SHA-256]
    HASH --> DB[(PostgreSQL dera_user_sessions<br/>token_hash VARCHAR(64) UNIQUE)]
    
    REQ[Client Request] --> EXTRACT{Extract Token:<br/>Authorization Header OR<br/>dera_session Cookie}
    EXTRACT --> CALC[Compute SHA-256 of Token]
    CALC --> LOOKUP[Query dera_user_sessions<br/>WHERE token_hash = ?]
    LOOKUP --> VALIDATE{Is Active?<br/>revoked_at IS NULL AND<br/>expires_at > UTC NOW}
    VALIDATE -- No: Expired --> 401E[401 SESSION_EXPIRED]
    VALIDATE -- No: Revoked --> 401R[401 SESSION_REVOKED]
    VALIDATE -- Yes --> USER_CHK{User Status == 'active'?}
    USER_CHK -- No --> 403D[403 ACCOUNT_DISABLED]
    USER_CHK -- Yes --> AUTH[Authenticated Principal]
```

---

## 2. Session Token Specifications

| Attribute | Specification | Rationale |
| :--- | :--- | :--- |
| **Entropy Source** | `secrets.token_hex(32)` (Python standard library `secrets` OS CSPRNG) | Guarantees non-predictable, cryptographically secure 256-bit random entropy. |
| **Token Format** | 64-character lowercase hexadecimal string | Compact, URL-safe, header-safe string representation. |
| **Database Hash** | SHA-256 hex digest (`hashlib.sha256(token.encode("utf-8")).hexdigest()`) | Stored in `dera_user_sessions.token_hash`. Plaintext session secrets are never persisted in the database. |
| **Default Lifetime** | 86,400 seconds (24 hours) | Configurable via `DERA_AUTH_SESSION_LIFETIME_SECONDS`. |
| **Revocation Marker** | `revoked_at TIMESTAMP WITH TIME ZONE` | Explicit timestamp allows distinguishing between expired and manually revoked sessions. |

---

## 3. Cookie Configuration & Browser Defenses

For browser clients, authentication is delivered through HTTP cookies with strict security flags:

```http
Set-Cookie: dera_session=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855; Max-Age=86400; Path=/; Secure; HttpOnly; SameSite=Lax
Set-Cookie: dera_csrf=a1b2c3d4e5f60718293a4b5c6d7e8f90; Max-Age=86400; Path=/; Secure; SameSite=Lax
```

### Security Directives

1. **`HttpOnly` (`dera_session`):** Prevents client-side scripts from reading the session identifier, mitigating XSS session hijacking attacks.
2. **`Secure`:** Mandates transmission exclusively over TLS/HTTPS (configurable for local offline HTTP test suites via `DERA_AUTH_COOKIE_SECURE`).
3. **`SameSite=Lax`:** Defends against cross-site request forgery on top-level navigation while permitting standard inbound links.
4. **`Path=/`:** Constrains cookie scope to the root path of the application.

---

## 4. Session Revocation & Concurrent Sessions

DERA supports both single-session logout and global multi-device session revocation:

### 1. Single Session Logout (`POST /api/v1/auth/logout`)

- Requires active authentication and valid CSRF token.
- Updates the active session record:
  ```sql
  UPDATE dera_user_sessions
  SET revoked_at = NOW()
  WHERE id = :active_session_id AND revoked_at IS NULL;
  ```
- Emits `auth.logout.success` audit event.
- Instructs the client browser to delete both `dera_session` and `dera_csrf` cookies via negative expiration.

### 2. Revoke All Sessions (`POST /api/v1/auth/logout-all`)

- Used during credential changes, security incident response, or user-initiated remote logout.
- Marks every active session of the user as revoked:
  ```sql
  UPDATE dera_user_sessions
  SET revoked_at = NOW()
  WHERE user_id = :user_id AND revoked_at IS NULL;
  ```
- Emits `auth.logout_all.success` audit event with the total count of terminated sessions.

---

## 5. Account Disablement Immediate Invalidation

When an administrator disables a user account (`dera_users.status = 'disabled'`), session validation instantly denies access across all endpoints:

```python
if user.status != "active":
    raise AccountDisabledError()
```

This prevents disabled or terminated employees from using existing valid sessions, eliminating delay windows.
