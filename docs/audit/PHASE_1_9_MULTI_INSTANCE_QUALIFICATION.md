# Phase 1–9 Multi-Instance & Restart Qualification Report
**Document ID:** `DERA-AUDIT-MULTI-INSTANCE`  
**Test Suite:** `tests/integration/test_migration_restart_and_multi_instance.py`  
**Date:** 2026-11-01  
**Qualification Status:** **PASS (Fully Verified)**  

---

## 1. Objective & Methodology

Horizontal scaling and zero-downtime rolling deployments require that no API worker maintains exclusive authoritative ownership of state in process-local memory.

This qualification exercises two critical operational scenarios:
1. **Application Restart Recovery:** Verifying that a complete cold-restart of the API process preserves all comparisons, risk reports, plans, SQL artifacts, governance reviews, and audit events.
2. **Multi-Instance Concurrency & Quorum Consistency:** Running two independent `FastAPI` application instances (`Instance A` and `Instance B`) with distinct process memory spaces backed by the same relational database.

---

## 2. Test Execution & Evidence

### 2.1 Application Restart Recovery (`test_application_restart_recovery`)

**Scenario Execution:**
1. **Phase 1 Pipeline Execution (Instance 1):**
   - Two valid snapshots (`snap_v1`, `snap_v2`) ingested.
   - Comparison report generated and persisted (`comp_id`).
   - Risk report generated and persisted (`risk_id`).
   - Topological plan compiled and persisted (`plan_id`).
   - Review-only PostgreSQL SQL compiled and persisted (`art_id`).
   - Governance review submitted and persisted (`rev_id`).
2. **Worker Cold Restart:**
   - Client and FastAPI application instance 1 destroyed.
   - Process-local migration caches completely purged.
   - FastAPI application instance 2 initialized with fresh state, connected to the same database.
3. **Recovery Verification (Instance 2):**
   - Ingested snapshots retrieved from snapshot storage.
   - Plan retrieved via `/api/v1/migrations/plans/{plan_id}` -> SHA-256 fingerprint verified against original.
   - SQL artifact retrieved via `/api/v1/migrations/sql-artifacts/{art_id}` -> DDL script verified intact.
   - Governance review retrieved via `/api/v1/migrations/reviews/{rev_id}` -> Initial `SUBMITTED` state verified intact.
   - Authorized reviewer submits approval decision via Instance 2 -> Status transitions to `APPROVED`.
   - SQL artifact exported via Instance 2 -> Package exported with disclaimer and valid cryptographic audit log.

**Result:** **PASS** (100% durable recovery across restarts).

---

### 2.2 Multi-Instance Concurrency & Quorum Consistency (`test_multi_instance_consistency_and_quorum`)

**Scenario Execution:**
1. **Topology:**
   - `Instance A` (`client_a`): API worker 1 with independent cache `_reviews_a`.
   - `Instance B` (`client_b`): API worker 2 with independent cache `_reviews_b`.
   - Shared persistence: PostgreSQL/SQLite transactional database.
   - Governance Policy: Quorum = 2 distinct authorized reviewers.
2. **Step-by-Step Flow:**
   - Propose migration review `rev_xyz` on Instance A (Quorum required: 2).
   - Reviewer 1 approves review `rev_xyz` on Instance A:
     - Decision persisted to `dera_migration_review_decisions`.
     - Quorum evaluated: 1/2. Status remains `SUBMITTED`.
   - Reviewer 2 approves review `rev_xyz` on Instance B:
     - Decision persisted to `dera_migration_review_decisions`.
     - Quorum evaluated: 2/2. Status transitions to `APPROVED`.
     - Review updated in database.
   - Instance A receives export request from workspace owner:
     - Instance A's `get_review()` queries authoritative database state.
     - Detects status is `APPROVED` directly from the database, overriding any local stale cache.
     - Successfully exports approved SQL package with full audit trail.

**Result:** **PASS** (Zero stale cache overrides, zero lost updates across concurrent workers).
