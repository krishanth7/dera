# DERA Backend Documentation Index

> **Workspace:** `apps/api`  
> **Maintainer:** Krishanth  
> **Status:** Active Documentation Hub  
> **Phase:** 4.1 — Python/FastAPI Application Foundation  

---

## 1. Backend Documentation Specifications

| Document | Purpose | Status |
|---|---|---|
| [**ARCHITECTURE.md**](ARCHITECTURE.md) | Authoritative FastAPI architecture, factory pattern, lifecycle, and middleware ordering | **Active** |
| [**LOCAL_DEVELOPMENT.md**](LOCAL_DEVELOPMENT.md) | Local developer environment setup, Uvicorn execution, and test commands | **Active** |
| [**CONFIGURATION.md**](CONFIGURATION.md) | Typed configuration reference, environment profiles, and security defaults | **Active** |
| [**API_FOUNDATION.md**](API_FOUNDATION.md) | API routing conventions, truthful health probes, and correlation tracking | **Active** |
| [**TESTING.md**](TESTING.md) | Automated testing strategy, test isolation, and CI integration | **Active** |
| [**SECURITY_BASELINE.md**](SECURITY_BASELINE.md) | OWASP defense headers, CORS policies, and secret redaction | **Active** |
| [**APPLICATION_ARCHITECTURE.md**](APPLICATION_ARCHITECTURE.md) | Historical FastAPI framework structure and execution flow | **Maintained** |
| [**API_CONTRACTS.md**](API_CONTRACTS.md) | Authoritative reference for implemented and planned REST endpoints and schemas | **Maintained** |

---

## 2. Key Backend Invariants

1. **Deterministic Processing:** Zero generative AI, machine learning inference, LLM APIs, or vector databases.
2. **Factory-Driven Construction:** Applications are instantiated deterministically via `create_app(settings)`.
3. **Modern Lifespan Management:** Lifecycle execution relies on `contextlib.asynccontextmanager`.
4. **Loopback Binding by Default:** Listens on `127.0.0.1:8000` to prevent accidental network exposure.
5. **OWASP Security Headers:** Every response is decorated with defensive HTTP headers.
6. **Information Leak Prevention:** Production errors are sanitized with request correlation IDs and never leak stack traces.
7. **Read-Only Database Boundaries:** Database connectors are strictly guarded against query mutations.

---

## 3. Related Documentation Hubs

- [Root Documentation Hub](../README.md)
- [System Architecture Overview](../architecture/SYSTEM_OVERVIEW.md)
- [Frontend Documentation](../frontend/README.md)
- [Core Engine Guide](../core/README.md)
- [Database Connectors Guide](../connectors/README.md)
- [Shared Contracts](../contracts/README.md)
