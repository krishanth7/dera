# Frontend Security Architecture & Threat Model

**Module**: `apps/web/`  
**Phase**: 7.6 — Accessibility, Responsive Design & Frontend Quality Assurance  

---

## 1. Security Architecture & Threat Vectors

The DERA frontend operates under a zero-trust model regarding source database metadata:

```text
+--------------------------------------------------------------------------+
|                  External Source Database / Customer Data                |
|           (Contains arbitrary names, SQL expressions, UTF-8 strings)     |
+------------------------------------+-------------------------------------+
                                     |
                          [ Phase 6.6 REST API ]
                          (RBAC & Workspace Auth)
                                     |
                                     v
+--------------------------------------------------------------------------+
|                  Next.js Frontend & React Virtual DOM                    |
|  * Text Nodes auto-escaped (Zero dangerouslySetInnerHTML)                |
|  * SQL Check constraints rendered as inert text in <code> blocks         |
|  * Session tokens isolated; no database credentials in browser           |
|  * CSP enforced: default-src 'self'; script-src 'self'                   |
+--------------------------------------------------------------------------+
```

---

## 2. Security Mitigation Matrix

| Vulnerability | Mitigation Strategy in Phase 7.6 | Status |
| :--- | :--- | :--- |
| **Cross-Site Scripting (XSS)** | Pure JSX text escaping. Check constraints, table names, and column comments are rendered as standard string children. Zero unescaped HTML injection. | Verified |
| **Credential Disclosure** | Database passwords and connection secrets are strictly handled on the backend. Frontend only receives masked connection strings and status flags. | Verified |
| **Cross-Tenant Metadata Leakage** | All API requests require a valid JWT bearer token and enforce `X-Workspace-Id` verification. Cross-workspace schema IDs return 403 Forbidden. | Verified |
| **SQL Injection via UI** | Frontend performs zero SQL generation or execution. All database metadata is queried via strongly-typed REST endpoints. | Verified |
| **Content Security Policy** | Strict CSP headers configured preventing arbitrary inline script execution or untrusted third-party asset loading. | Verified |
