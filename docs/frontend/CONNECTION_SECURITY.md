# Connection Security Specification

**Document Reference**: `docs/frontend/CONNECTION_SECURITY.md`  
**Milestone**: Phase 7.3 — Database Connection & Schema Explorer UI  

---

## 1. Zero-Trust Security Architecture

The DERA frontend operates under a strict zero-trust boundary regarding database connections and user-supplied metadata.

```text
+--------------------------------------------------------------+
|                        Browser Client                        |
| - Never stores database passwords in localStorage / sessionStorage |
| - Never establishes direct TCP/WebSocket database connections  |
| - Sends credentials exclusively via POST/PATCH payloads     |
| - Treats all database names and identifiers as untrusted text |
+--------------------------------------------------------------+
                               │ HTTPS / TLS
                               ▼
+--------------------------------------------------------------+
|                       DERA Backend API                       |
| - Validates workspace membership & role permissions (RBAC)   |
| - Enforces SSRF and DNS-rebinding network protections         |
| - Stores credentials in server-side encrypted vault           |
| - Executes read-only transaction queries with statement timeout|
+--------------------------------------------------------------+
```

---

## 2. Credential Protection Policies

- **Ephemeral Memory**: Password inputs are held strictly within local React component state during submission and cleared upon form unmount or completion.
- **Zero Client Persistence**: Database passwords are never written to `localStorage`, `sessionStorage`, browser cookies, or IndexedDB.
- **Masked Retrieval**: Backend API responses omit the password field. The frontend renders passwords as `••••••••` in inspection screens.
- **CSRF Defense**: All mutating connection requests transmit the `X-CSRF-Token` header read from the secure `csrf_token` cookie.

---

## 3. Network Restrictions & SSRF Defenses

Backend connectors reject requests targeting internal cloud metadata endpoints (`169.254.169.254`), loopback addresses (`127.0.0.1`), or private subnets unless explicitly configured in development mode.
Client-side form validation alerts users when disallowed addresses are entered.
