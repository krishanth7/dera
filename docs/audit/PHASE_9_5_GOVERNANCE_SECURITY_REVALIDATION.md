# Phase 9.5 Governance Security Revalidation Report

## 1. Executive Summary
- **Component**: `packages/core/src/dera/migration/governance/`, `apps/api/src/dera_api/api/v1/endpoints/migrations.py`, and `apps/api/src/dera_api/repositories/migration_governance.py`
- **Milestone**: 9.5 — Migration Review, Approval & Safety Controls
- **Status**: **PASS (Verified Post-P0 Remediation)**
- **Audit Focus**: Elimination of Client Actor Headers, Fail-Closed Server-Side Identity Verification, Durable Transaction-Safe Persistence, Trusted Quorum Enforcement, Separation of Duties, Risk Report Linkage, Artifact Tamper Detection, and Multi-Tenant Isolation.

---

## 2. P0 Security Remediation & Architectural Verification

### 2.1 Complete Removal of Client-Supplied Actor Headers
- **Vulnerability Remediated**: API endpoints previously inspected `X-Actor-Id` or `X-Actor-Role` request headers, allowing an attacker to spoof caller identity and bypass RBAC.
- **Enforcement**:
  - Removed all extraction and trust of `X-Actor-Id` and `X-Actor-Role` in `apps/api/src/dera_api/api/v1/endpoints/migrations.py`.
  - Caller identity is derived exclusively from validated server-side authentication (`current_user.id`).
  - Caller workspace role is computed dynamically by querying `MembershipRepository` for the authenticated user within the target workspace. Hardcoded fallback identities and default `"admin"` fallbacks in `get_effective_user_role()` were completely removed.
- **Test Evidence**: Verified by `test_spoofed_actor_headers_are_ignored` (client spoofing `X-Actor-Id: evil-hacker` is ignored; review is attributed strictly to authenticated user `owner_id`).

### 2.2 Fail-Closed Workspace Identity & Access Verification
- **Vulnerability Remediated**: Weak fallback logic in `resolve_authorized_workspace_id()` permitted unauthenticated access when identity context was missing.
- **Enforcement**:
  - `resolve_authorized_workspace_id()` in `apps/api/src/dera_api/api/v1/endpoints/reverse_engineering/deps.py` now extracts credentials directly from the `Authorization` header / session cookies, validates the user against `UserRepository`, confirms active session status via `SessionRepository`, and validates active workspace membership.
  - If authentication or active membership cannot be established, the handler immediately fails closed with HTTP 401 or 403.
- **Test Evidence**: Verified by `test_unauthenticated_request_fails_closed` and `test_revoked_or_suspended_membership_fails`.

### 2.3 Durable, Transaction-Safe Database Persistence
- **Vulnerability Remediated**: Production governance reviews, approval decisions, and audit events were stored in volatile in-memory process dictionaries, losing audit integrity upon server restart or multi-instance scaling.
- **Enforcement**:
  - Implemented relational database models in `apps/api/src/dera_api/db/models/migration_governance.py`:
    - `MigrationReviewRecord` (table: `dera_migration_reviews`)
    - `MigrationReviewDecisionRecord` (table: `dera_migration_review_decisions`, unique constraint on `(review_record_id, reviewer_id)`)
    - `MigrationAuditEventRecord` (table: `dera_migration_audit_events`, append-only SHA-256 hash chaining)
  - Implemented transactional repository in `apps/api/src/dera_api/repositories/migration_governance.py` (`MigrationGovernanceRepository`) with unit-of-work commit guarantees.
- **Test Evidence**: Verified by `test_end_to_end_safe_migration_and_durable_persistence`, checking row counts in `dera_migration_reviews`, `dera_migration_review_decisions`, and `dera_migration_audit_events`.

### 2.4 Server-Side Policy Quorum Enforcement
- **Vulnerability Remediated**: Review request payloads could specify `required_approvals: 0` to bypass approval gates.
- **Enforcement**:
  - `apps/api/src/dera_api/api/v1/endpoints/migrations.py` strictly derives required approvals from `governance_policy.required_approval_quorum`, rejecting client-supplied quorum overrides.

### 2.5 Separation of Duties (SoD)
- **Rule**: Requesters are strictly forbidden from approving their own migration requests.
- **Enforcement**: In `GovernanceEngine.record_decision()`, if `decision.reviewer_id == review.requester_id` and `decision.decision_type == ReviewDecisionType.APPROVE`, a `SeparationOfDutiesViolation` is raised, returning HTTP 403.
- **Test Evidence**: Verified by `test_separation_of_duties_self_approval_blocked`.

### 2.6 Authentic Risk-Report Fingerprint Linkage
- **Vulnerability Remediated**: Artifact compiler previously set `risk_report_fingerprint` to a default empty string or plan hash.
- **Enforcement**:
  - Added `source_risk_report_fingerprint` to `SqlMigrationArtifact`.
  - Compiler forwards `plan_report.risk_report_fingerprint` directly into `artifact.source_risk_report_fingerprint`.
  - Governance engine binds reviews cryptographically to the actual verified risk report fingerprint.

### 2.7 Artifact Integrity & Tamper Invalidation
- **Rule**: Approvals are bound cryptographically to the SHA-256 fingerprint of the migration plan and generated SQL artifact.
- **Enforcement**:
  - `GovernanceEngine` compares the stored `artifact_fingerprint` against the decision payload.
  - The export endpoint (`/export`) verifies that `review.status == ReviewStatus.APPROVED` and confirms that the requested artifact fingerprint matches the approved review record. Any mismatch returns HTTP 400 with an integrity violation error.
- **Test Evidence**: Verified by `test_artifact_tampering_blocks_export`.

---

## 3. Security Regression Suite Summary
All 7 dedicated security integration tests in `tests/integration/test_migration_endpoints.py` PASS:
1. `test_unauthenticated_request_fails_closed` -> HTTP 401
2. `test_spoofed_actor_headers_are_ignored` -> HTTP 200 (Owner Identity Bound Server-Side)
3. `test_separation_of_duties_self_approval_blocked` -> HTTP 403
4. `test_cross_tenant_access_denied` -> HTTP 403 / 404
5. `test_revoked_or_suspended_membership_fails` -> HTTP 403
6. `test_artifact_tampering_blocks_export` -> HTTP 400 Integrity Error
7. `test_end_to_end_safe_migration_and_durable_persistence` -> HTTP 200 with verified DB persistence and hash-chained audit events
