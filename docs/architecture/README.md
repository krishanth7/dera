# DERA Architecture Documentation Index

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Maintainer:** Krishanth  
> **Last Verified:** 2026-10-26 (Commit `e550fdd`)  

---

## 1. Architecture Specifications Index

| Document | Purpose | Status |
|---|---|---|
| [**SYSTEM_OVERVIEW.md**](./SYSTEM_OVERVIEW.md) | Platform architectural philosophy, core pillars, component diagram, and subsystem breakdown | **Active** |
| [**MONOREPO_STRUCTURE.md**](./MONOREPO_STRUCTURE.md) | Authoritative monorepo directory layout, package responsibilities, and tooling mapping | **Active** |
| [**MODULE_BOUNDARIES.md**](./MODULE_BOUNDARIES.md) | Unidirectional dependency rules, forbidden import matrix, and contributor extension guide | **Active** |
| [**DATA_FLOW.md**](./DATA_FLOW.md) | End-to-end metadata inspection lifecycle and sequence architecture diagrams | **Active** |
| [**DEPENDENCY_GRAPH.md**](./DEPENDENCY_GRAPH.md) | Detailed dependency graphs, package hierarchy, and non-AI boundaries | **Active** |
| [**TECHNOLOGY_DECISIONS.md**](./TECHNOLOGY_DECISIONS.md) | Technology choices, selection rationale, limitations, and future considerations | **Active** |
| [**adr/README.md**](./adr/README.md) | Architecture Decision Record (ADR) index and submission policy | **Active** |
| [**adr/0001-monorepo-architecture.md**](./adr/0001-monorepo-architecture.md) | ADR 0001: Modular Monolith Monorepo Architecture for DERA | **Accepted** |
| [overview.md](./overview.md) | Historical Phase 1.2 architecture overview baseline | **Archived Baseline** |
| [README_ARCHITECTURE.md](./README_ARCHITECTURE.md) | Historical Phase 1.2 architectural blueprint reference | **Archived Baseline** |

---

## 2. Core Architectural Invariants

1. **Strict Deterministic Execution:** Zero artificial intelligence, zero large language models, zero vector databases, and zero probabilistic inference.
2. **Read-Only Database Safety:** Connectors execute exclusively under session-level read-only constraints (`SET TRANSACTION READ ONLY;`, `PRAGMA query_only = ON;`) backed by static SQL mutation interception.
3. **Framework Independence of Core:** Domain models, graph algorithms, and diagnostic rules depend solely on the Python standard library.
4. **Contract Synchronization:** Shared schemas (`packages/contracts`) guarantee type parity across Python backend services and TypeScript frontend studios.
5. **Loopback Security by Default:** The backend API binds strictly to `127.0.0.1` by default to prevent unintended network exposure.

---

## 3. Related Documentation Hubs

- [Developer Guide](../development/README.md)
- [Backend Architecture](../backend/README.md)
- [Frontend Architecture](../frontend/README.md)
- [Core Engine Guide](../core/README.md)
- [Database Connectors Guide](../connectors/README.md)
- [Shared Contracts](../contracts/README.md)
- [Security Architecture](../security/README.md)
- [Repository Audit Log](../audit/README.md)
