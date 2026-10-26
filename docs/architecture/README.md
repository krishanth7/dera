# DERA Architecture Documentation Index

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Maintainer:**  Krishanth  

---

## Architecture Specifications Index

| Document | Purpose | Status |
|---|---|---|
| [OVERVIEW.md](./OVERVIEW.md) | Platform architectural philosophy, core pillars, and subsystem breakdown | **Active** |
| [MONOREPO_STRUCTURE.md](./MONOREPO_STRUCTURE.md) | Authoritative monorepo directory layout, package responsibilities, and tooling mapping | **Active** |
| [MODULE_BOUNDARIES.md](./MODULE_BOUNDARIES.md) | Unidirectional dependency rules, forbidden import matrix, and contributor extension guide | **Active** |
| [DEPENDENCY_GRAPH.md](./DEPENDENCY_GRAPH.md) | Mermaid dependency graphs, end-to-end data flows, and non-AI boundaries | **Active** |
| [adr/0001-monorepo-architecture.md](./adr/0001-monorepo-architecture.md) | Formal Architecture Decision Record for selecting the Modular Monolith structure | **Proposed** |
| [overview.md](./overview.md) | Legacy architecture specification baseline | **Maintained** |

---

## Core Architectural Invariants

1. **Deterministic Execution:** No AI models, LLMs, or non-deterministic inference services.
2. **Read-Only Database Safety:** Introspection connectors execute under strict read-only constraints with static mutation interception.
3. **Framework Independence of Core:** Domain models and graph algorithms depend exclusively on the Python standard library.
4. **Contract Synchronization:** Shared contracts ensure type parity between Python backend services and TypeScript frontend studios.
