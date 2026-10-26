# DERA Backend Documentation Index

> **Workspace:** `apps/api`  
> **Maintainer:** Krishanth  
> **Status:** Active Documentation Hub  
> **Last Verified:** 2026-10-26 (Commit `e550fdd`)  

---

## 1. Backend Documentation Specifications

| Document | Purpose | Status |
|---|---|---|
| [**APPLICATION_ARCHITECTURE.md**](APPLICATION_ARCHITECTURE.md) | FastAPI framework structure, configuration, security middleware, and execution flow | **Active** |
| [**API_CONTRACTS.md**](API_CONTRACTS.md) | Authoritative reference for implemented and planned REST endpoints, schemas, and curl examples | **Active** |

---

## 2. Key Backend Invariants

1. **Stateless Gateway:** The backend holds no state across requests.
2. **Deterministic Processing:** No generative AI, machine learning inference, or vector databases.
3. **Loopback Binding by Default:** Listens on `127.0.0.1:8000` to prevent accidental network exposure.
4. **OWASP Security Headers:** Every response is decorated with defensive HTTP headers.
5. **Read-Only Database Boundaries:** Database connectors are strictly guarded against query mutations.

---

## 3. Related Documentation Hubs

- [Root Documentation Hub](../README.md)
- [System Architecture Overview](../architecture/SYSTEM_OVERVIEW.md)
- [Frontend Documentation](../frontend/README.md)
- [Core Engine Guide](../core/README.md)
- [Database Connectors Guide](../connectors/README.md)
- [Shared Contracts](../contracts/README.md)
