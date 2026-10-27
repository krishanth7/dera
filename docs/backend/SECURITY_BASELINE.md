# DERA Backend Security Baseline

> **Component:** `apps/api/src/dera_api`  
> **Phase:** 4.1 — Python/FastAPI Application Foundation  
> **Status:** Authoritative Security Policy & Baseline  

---

## 1. Security Architecture Principles

The DERA backend foundation adheres strictly to OWASP API Security guidelines:

1. **Deterministic Execution (Zero-AI Policy):** No generative AI, prompt injection attack vectors, or non-deterministic code evaluation paths.
2. **Defensive Headers:** All responses carry standard security headers preventing MIME sniffing, clickjacking, and unauthorized embedding.
3. **Information Leak Prevention:** Production profiles forbid debug tracebacks, raw exception strings, and file path disclosure.
4. **Least Privilege CORS:** Origin allowlists are explicitly defined. Wildcards combined with credentials are strictly prohibited.
5. **Correlation Tracking:** Safe, bounded correlation IDs (`X-Request-ID`) enable forensic request tracking without leaking sensitive payload data.

---

## 2. Security Headers Invariant

Every response from the DERA API includes the following defensive HTTP headers:

| Header | Value | Purpose |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | Prevents browser MIME-type sniffing |
| `X-Frame-Options` | `DENY` | Prevents clickjacking and unauthorized frame embedding |
| `X-XSS-Protection` | `1; mode=block` | Enables legacy browser cross-site scripting filters |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Controls referrer metadata leakage across origins |
| `X-DERA-Policy` | `DETERMINISTIC_ZERO_AI` | Formal assertion of deterministic non-AI execution |

---

## 3. Production Environment Safeguards

In the `production` environment profile, `ApiSettings` enforces:

- **Debug Mode Forbidden:** `APP_DEBUG=true` triggers an immediate fatal startup error.
- **Wildcard CORS Forbidden:** Origin `*` triggers an immediate fatal startup error.
- **Documentation Gating:** Interactive OpenAPI endpoints (`/docs`, `/redoc`, `/openapi.json`) are disabled by default.
- **Secret Redaction Filter:** The structured logging pipeline (`SensitiveDataFilter`) masks database passwords, bearer tokens, API keys, and authorization headers before emitting logs to standard output.

---

## 4. Security Verification

Security postures are continually verified through automated CI checks:

- **Bandit SAST:** `python -m bandit -r packages/core/src/ apps/api/src/ -ll -q`
- **Architecture Tests:** `tests/architecture/test_module_boundaries.py`
- **Integration Tests:** `tests/integration/test_api_integration.py`
