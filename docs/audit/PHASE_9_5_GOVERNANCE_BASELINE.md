# Phase 9.5 Baseline Audit: Migration Review, Approval & Safety Controls

**Base Commit SHA:** `ee0fcf8b4635aed2c567446e8fa831d3adf3df5c`  
**Date:** 2026-11-01  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Branch:** `feat/phase-9.5-migration-governance-approval`  

---

## 1. Verified Prerequisites
- [PHASE_9_1_COMPARISON_ACCEPTANCE.md](PHASE_9_1_COMPARISON_ACCEPTANCE.md) — **VERIFIED PASS**
- [PHASE_9_2_RISK_ANALYSIS_ACCEPTANCE.md](PHASE_9_2_RISK_ANALYSIS_ACCEPTANCE.md) — **VERIFIED PASS**
- [PHASE_9_3_MIGRATION_PLANNING_ACCEPTANCE.md](PHASE_9_3_MIGRATION_PLANNING_ACCEPTANCE.md) — **VERIFIED PASS**
- [PHASE_9_4_SQL_GENERATION_ACCEPTANCE.md](PHASE_9_4_SQL_GENERATION_ACCEPTANCE.md) — **VERIFIED PASS**
- Phase 4 RBAC & Persistence:
  - `WorkspaceRole` (`OWNER`, `ADMIN`, `EDITOR`, `VIEWER`), `Permission` registry.
  - PostgreSQL persistence, FastAPI routing patterns.

## 2. Scope & Governance Architecture
Phase 9.5 builds the production-grade **Migration Review, Approval, and Safety Control Engine** governing Phase 9.4 generated SQL artifacts:
1. **Migration Review Requests:** Immutable binding between a review request and a specific Phase 9.4 `SqlMigrationArtifact` revision and fingerprint.
2. **Review Lifecycle State Machine:**
   `DRAFT` $\to$ `SUBMITTED` $\to$ `UNDER_REVIEW` $\to$ `APPROVED` / `REJECTED` / `CHANGES_REQUESTED` / `CANCELLED` / `SUPERSEDED` / `BLOCKED`.
3. **Safety Gates:**
   - Artifact integrity gate (SHA-256 fingerprint verification).
   - SQL validation gate.
   - Risk evidence gate.
   - Destructive operation gate (extra reviewer or manual preservation review required).
   - Prerequisite completeness gate.
4. **Separation of Duties (SoD) & Approval Quorum:**
   - Requester cannot approve their own review request when SoD is enforced.
   - Configurable quorum (e.g. at least 1 Admin/Owner or distinct reviewer roles).
   - Duplicate approvals from the same identity cannot satisfy quorum.
5. **Approval Invalidation:**
   - Any modification to the SQL text, plan fingerprint, or risk report immediately invalidates prior approvals.
6. **Append-Only Tamper-Evident Audit Evidence:**
   - Per-review event log with cryptographic SHA-256 hash chaining.
7. **Controlled Export Eligibility:**
   - Evaluates whether an approved SQL artifact is eligible for export (export eligibility $\neq$ live execution).

## 3. Strict Non-Negotiables
- AI/LLM/ML models: **Strictly Prohibited**.
- Migration Execution / Customer DB Mutation: **Strictly Prohibited**.
- Self-Approval when prohibited by policy: **Strictly Blocked**.
- Stale Approval on Changed Artifact: **Strictly Invalidated**.
- Cross-Tenant Access: **Strictly Isolated by Workspace ID**.
