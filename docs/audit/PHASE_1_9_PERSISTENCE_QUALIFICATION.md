# Phase 1–9 Durable Persistence Qualification Report
**Document ID:** `DERA-AUDIT-PERSISTENCE`  
**Scope:** Migration Artifacts, Governance Reviews, Decisions, and Export Records  
**Database Engines Tested:** PostgreSQL 16 (Primary), SQLite 3 (Offline/Local)  
**ORM / Migration Framework:** SQLAlchemy 2.0 (AsyncIO), Alembic  
**Date:** 2026-11-01  
**Qualification Status:** **PASS (Fully Verified)**  

---

## 1. Executive Summary

Previous iterations of the Phase 9 migration service relied on process-local dictionaries (`_comparisons`, `_risk_reports`, `_plans`, `_artifacts`). These in-memory structures were non-durable and failed across API worker restarts, multi-instance horizontal deployments, and failovers.

In this remediation:
1. **Durable Database Models:** Created five authoritative relational models in `apps/api/src/dera_api/db/models/migration_artifacts.py`:
   - `MigrationComparisonRecord` (`dera_migration_comparisons`)
   - `MigrationRiskRecord` (`dera_migration_risk_reports`)
   - `MigrationPlanRecord` (`dera_migration_plans`)
   - `MigrationSqlArtifactRecord` (`dera_migration_sql_artifacts`)
   - `MigrationExportRecord` (`dera_migration_exports`)
2. **Alembic Revision 005:** Authored `migrations/versions/005_migration_artifacts.py` linking foreign keys to `dera_workspaces(id)` with `ondelete="CASCADE"`. Verified single head with `alembic heads`.
3. **Repository Layer:** Created `MigrationArtifactsRepository` in `apps/api/src/dera_api/repositories/migration_artifacts.py` providing transactional persistence, canonical JSON serialization, and cryptographic fingerprint verification.
4. **Authoritative State Resolution:** Updated `MigrationService` methods to query the database first before consulting process-local caches. Authoritative database state always overrides stale memory caches.
5. **Restart Recovery & Multi-Instance Verification:** Authored `tests/integration/test_migration_restart_and_multi_instance.py` confirming complete persistence survival across service restarts and concurrent multi-instance consistency.

---

## 2. Relational Schema Architecture

```text
                  ┌──────────────────────┐
                  │   dera_workspaces    │
                  └──────────┬───────────┘
                             │ 1
                             ├───────────────────────────────────────┐
                             │ *                                     │ *
              ┌──────────────┴───────────────┐        ┌──────────────┴───────────────┐
              │  dera_migration_comparisons  │        │  dera_migration_risk_reports │
              │  - id: UUID (PK)             │        │  - id: UUID (PK)             │
              │  - workspace_id: UUID (FK)   │        │  - workspace_id: UUID (FK)   │
              │  - comparison_id_str: String │        │  - risk_report_id_str: String│
              │  - baseline_snapshot_id: UUID│        │  - comparison_id: String     │
              │  - target_snapshot_id: UUID  │        │  - max_severity: String      │
              │  - comparison_fingerprint    │        │  - fingerprint: String       │
              │  - report_json: JSONB        │        │  - report_json: JSONB        │
              └──────────────┬───────────────┘        └──────────────┬───────────────┘
                             │                                       │
                             └───────────────────┬───────────────────┘
                                                 │
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │    dera_migration_plans     │
                                  │  - id: UUID (PK)            │
                                  │  - workspace_id: UUID (FK)  │
                                  │  - plan_id_str: String      │
                                  │  - risk_report_id: String   │
                                  │  - plan_fingerprint: String │
                                  │  - operation_count: Integer │
                                  │  - plan_json: JSONB         │
                                  └──────────────┬──────────────┘
                                                 │
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │ dera_migration_sql_artifacts│
                                  │  - id: UUID (PK)            │
                                  │  - workspace_id: UUID (FK)  │
                                  │  - artifact_id_str: String  │
                                  │  - plan_id: String          │
                                  │  - target_dialect: String   │
                                  │  - artifact_fingerprint: Str│
                                  │  - sql_content: Text        │
                                  │  - rollback_sql: Text       │
                                  │  - artifact_json: JSONB     │
                                  └──────────────┬──────────────┘
                                                 │
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │   dera_migration_reviews    │
                                  │  - id: UUID (PK)            │
                                  │  - workspace_id: UUID (FK)  │
                                  │  - review_id: String (UK)   │
                                  │  - artifact_id: String      │
                                  │  - artifact_fingerprint: Str│
                                  │  - status: Enum (APPROVED)  │
                                  │  - required_quorum: Integer │
                                  └──────────────┬──────────────┘
                                                 │
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │   dera_migration_exports    │
                                  │  - id: UUID (PK)            │
                                  │  - workspace_id: UUID (FK)  │
                                  │  - export_id_str: String    │
                                  │  - review_id: String (FK)   │
                                  │  - artifact_id: String      │
                                  │  - target_dialect: String   │
                                  │  - artifact_fingerprint: Str│
                                  │  - exported_by: String      │
                                  │  - forward_sql: Text        │
                                  │  - export_json: JSONB       │
                                  └─────────────────────────────┘
```

---

## 3. Cryptographic Fingerprint Verification

Every persisted artifact maintains a cryptographic SHA-256 fingerprint computed across canonical serialized domain representations:
- **Comparison Report:** SHA-256 of normalized schema differences.
- **Risk Assessment:** SHA-256 of classified risk items and severity ratings.
- **Migration Plan:** SHA-256 of topologically ordered operations.
- **SQL Artifact:** SHA-256 of target dialect DDL and rollback scripts.

**Tamper Detection Guarantee:**
When an export request is received for review `rev_123`, the service loads the artifact from the database and verifies:
`artifact.artifact_fingerprint == review.artifact_fingerprint`
If the SQL artifact is altered or corrupted after review approval, the export is blocked with HTTP 400 (`Integrity violation: artifact content has changed`). Verified in `test_artifact_tampering_blocks_export`.

---

## 4. Multi-Instance and Restart Recovery Evidence

Verified in `tests/integration/test_migration_restart_and_multi_instance.py`:
1. **Application Restart Recovery (`test_application_restart_recovery`):**
   - Full pipeline executed on Instance 1 (comparison -> risk -> plan -> SQL -> review submission).
   - Instance 1 terminated; in-memory cache purged.
   - Instance 2 initialized against the same database.
   - All artifacts retrieved, fingerprints verified, review continued, decision recorded, and SQL exported without data loss.
2. **Multi-Instance Consistency & Quorum (`test_multi_instance_consistency_and_quorum`):**
   - Instance A and Instance B running concurrently against the shared database.
   - Plan and SQL artifact created via Instance A.
   - Review proposed via Instance A.
   - Reviewer 1 approves via Instance A (Quorum status: 1/2 PENDING).
   - Reviewer 2 approves via Instance B (Quorum status: 2/2 APPROVED).
   - Instance A queries review status and immediately detects APPROVED status directly from the authoritative database, successfully exporting the approved SQL artifact.
   - Zero stale cache overrides. Zero lost updates.

**Qualification Status:** **PASS**
