# DERA CSRF Protection Architecture

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Maintainer:** Bunga Krishanth  
**Security Reference:** OWASP Cross-Site Request Forgery Prevention Cheat Sheet  
**License:** [MIT License](../../LICENSE)  

---

## 1. Overview & Threat Model

Cross-Site Request Forgery (CSRF) occurs when an unauthorized external website forces a victim's browser to send state-changing HTTP requests with ambient session cookies attached to a trusted web application.

While modern browsers enforce `SameSite=Lax` on cookies, relying solely on `SameSite` is insufficient under strict defense-in-depth principles (due to potential browser incompatibilities, top-level `GET` pivots, and subdomain compromises).

DERA implements the industry-standard **Signed/High-Entropy Double-Submit Cookie Pattern** for state-changing browser requests.

```mermaid
sequenceDiagram
    autonumber
    actor Browser as User Browser
    participant API as FastAPI Gateway
    participant Dep as verify_csrf Dependency

    Note over Browser,API: Login / Session Establishment
    API-->>Browser: Set-Cookie: dera_session (HttpOnly, Secure, SameSite=Lax)<br/>Set-Cookie: dera_csrf (Secure, SameSite=Lax, NOT HttpOnly)

    Note over Browser,API: State-Changing Request (POST / PUT / PATCH / DELETE)
    Browser->>Browser: JavaScript reads 'dera_csrf' cookie value
    Browser->>API: POST /api/v1/auth/logout<br/>Cookie: dera_session=...; dera_csrf=XYZ<br/>Header: X-CSRF-Token: XYZ
    API->>Dep: verify_csrf(request)
    Dep->>Dep: Compare cookie 'dera_csrf' vs header 'X-CSRF-Token' (constant-time)
    alt Match & Non-Empty
        Dep-->>API: Validated -> Proceed to Endpoint Logic
    else Missing or Mismatched
        Dep-->>Browser: 403 Forbidden (CSRF_FAILED)
    end
```

---

## 2. Double-Submit Defense Rules

1. **State-Changing Methods:** CSRF validation is strictly enforced on `POST`, `PUT`, `PATCH`, and `DELETE`.
2. **Safe Read Methods Exempt:** `GET`, `HEAD`, and `OPTIONS` do not execute mutations and are exempt.
3. **Explicit Bearer Tokens Exempt:** When a request is authenticated via an explicit HTTP `Authorization: Bearer <token>` header, CSRF verification is bypassed because ambient browser cookies are not being used for authorization, and cross-origin scripts cannot forge custom `Authorization` headers without explicit CORS approval.
4. **Constant-Time Comparison:** The token from the `dera_csrf` cookie and the token from the `X-CSRF-Token` header are compared using `hmac.compare_digest` (`constant_time_compare`) to prevent timing side-channel leaks.

---

## 3. Configuration Parameters

| Environment Variable | Default | Purpose |
| :--- | :--- | :--- |
| `DERA_AUTH_CSRF_ENABLED` | `true` | Toggle CSRF enforcement (must remain enabled in production). |
| `DERA_AUTH_CSRF_COOKIE_NAME` | `dera_csrf` | Name of the cookie containing the CSRF token. |
| `DERA_AUTH_CSRF_HEADER_NAME` | `X-CSRF-Token` | HTTP header name client scripts must supply on mutations. |
