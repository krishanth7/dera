# DERA Architecture Decision Records (ADR) Index

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Maintainer:** Krishanth  
> **Status:** Active Decision Log  
> **Last Verified:** 2026-10-26 (Commit `e550fdd`)  

---

## 1. Overview & ADR Policy

Architecture Decision Records (ADRs) capture significant, architectural design choices made during the evolution of DERA. They document the context, alternatives evaluated, trade-offs, and operational consequences of key technical decisions.

All ADRs follow Michael Nygard's standard template:
1. **Identifier & Title:** Monotonically increasing 4-digit number and clear descriptive title (e.g. `0001-monorepo-architecture.md`).
2. **Status:** `Proposed`, `Accepted`, `Superceded`, or `Deprecating`.
3. **Date & Deciders:** Recording when and by whom the decision was reached.
4. **Context & Problem Statement:** What problem necessitated this architectural decision.
5. **Decision:** Clear statement of the architecture chosen.
6. **Alternatives Considered:** Options analyzed and specific reasons for their rejection.
7. **Consequences:** Positive outcomes and negative trade-offs.
8. **Related Source Files & Invariants:** Links to implemented code enforcing the decision.

---

## 2. Architecture Decision Records Log

| ADR ID | Title | Status | Decision Date | Key Consequences |
|---|---|---|---|---|
| [**0001**](0001-monorepo-architecture.md) | Modular Monolith Monorepo Architecture for DERA | **Accepted** | 2026-10-26 | Unified Git repository housing Python core/connectors and TypeScript contracts/web workspaces with strict unidirectional dependency flow. |

---

## 3. How to Propose a New ADR

1. Copy the standard ADR format:
   ```markdown
   # ADR XXXX: [Title]
   
   > **Status:** Proposed  
   > **Date:** YYYY-MM-DD  
   > **Deciders:** [Names / Roles]  
   > **Technical Scope:** [Component / Boundary]  
   
   ## 1. Context and Problem Statement
   ## 2. Decision
   ## 3. Alternatives Considered and Rationale
   ## 4. Consequences & Operational Implications
   ## 5. Related Files & Invariants
   ```
2. Place the proposal in `docs/architecture/adr/XXXX-<topic>.md`.
3. Submit a pull request referencing the relevant GitHub Issue.
4. Discuss with maintainers and stakeholders.
5. Upon consensus, update status to `Accepted` and update this index.

---

## 4. Related Architecture Specifications

- [System Architecture Overview](../SYSTEM_OVERVIEW.md)
- [Monorepo Structure Specification](../MONOREPO_STRUCTURE.md)
- [Module Boundaries](../MODULE_BOUNDARIES.md)
- [Technology Decisions](../TECHNOLOGY_DECISIONS.md)
