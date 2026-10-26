# DERA Frontend Documentation Index

> **Workspace:** `apps/web`  
> **Maintainer:** Krishanth  
> **Status:** Active Documentation Hub  
> **Last Verified:** 2026-10-26 (Commit `e550fdd`)  

---

## 1. Frontend Specifications Index

| Document | Purpose | Status |
|---|---|---|
| [**APPLICATION_ARCHITECTURE.md**](APPLICATION_ARCHITECTURE.md) | Next.js 15 framework structure, component hierarchy, API client, and security boundaries | **Active** |

---

## 2. Key Frontend Invariants

1. **Pure Presentation:** Frontend code handles presentation and user interaction; it performs zero direct database connections.
2. **Zero Credentials in Browser:** Database connection secrets must never enter client-side state.
3. **Contract Driven:** Data shapes consumed by the frontend match `@dera/contracts` TypeScript definitions.
4. **Planned Visualization:** The interactive React Flow ER diagram canvas is scheduled for Phase 7.

---

## 3. Related Documentation Hubs

- [Root Documentation Hub](../README.md)
- [System Architecture Overview](../architecture/SYSTEM_OVERVIEW.md)
- [Backend Documentation](../backend/README.md)
- [Shared Contracts](../contracts/README.md)
