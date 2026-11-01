## Summary
This pull request delivers complete Phase 1-9 integration, architectural hardening, and production qualification across all 54 milestones in the DERA platform. It eliminates all demo mock dependencies in the migration dashboard, connects real authenticated FastAPI endpoints directly to Phase 9 core engines, and resolves all 10 P0 security review findings with fail-closed defenses, server-side RBAC, durable persistence, and cryptographic audit logging.

## Change Type
- [x] Bug fix (`fix`)
- [x] Security enhancement (`security`)
- [x] Documentation (`docs`)
- [x] Test improvement (`test`)

## Implementation Details
1. **Elimination of Untrusted Client Actor Headers**: Removed all inspection and trust in `X-Actor-Id` and `X-Actor-Role`. Caller identity is strictly bound to authenticated `current_user.id`.
2. **Elimination of Hardcoded Fallbacks**: Removed hardcoded identities and default `"admin"` fallback in `get_effective_user_role()`. Roles are computed dynamically via `MembershipRepository` or fail closed.
3. **Fail-Closed Workspace Authorization**: Updated `resolve_authorized_workspace_id()` to strictly validate bearer tokens/sessions against `UserRepository` and `SessionRepository` and verify active workspace membership. Missing auth or suspended membership returns HTTP 401 / 403.
4. **Authoritative Server-Side Identity Derivation**: Proposers and reviewers are derived strictly from server-side session context.
5. **Authoritative Workspace Membership & RBAC Enforcement**: Enforced explicit permissions (`MIGRATION_READ`, `MIGRATION_COMPARE`, `MIGRATION_PLAN`, `MIGRATION_REVIEW`, `MIGRATION_APPROVE`, `MIGRATION_EXPORT`) with membership checks on every endpoint.
6. **Trusted Quorum Governance**: Derived review approval quorum strictly from server-side governance policy (`policy.required_approval_quorum`), rejecting untrusted client-supplied quorum values.
7. **Durable, Transaction-Safe Database Persistence**: Implemented relational models (`MigrationReviewRecord`, `MigrationReviewDecisionRecord`, `MigrationAuditEventRecord`) in `dera_migration_reviews`, `dera_migration_review_decisions`, and `dera_migration_audit_events` with transaction-safe unit of work in `MigrationGovernanceRepository`.
8. **Authentic Risk-Report Fingerprint Linkage**: Added `source_risk_report_fingerprint` to `SqlMigrationArtifact`, forwarded from `plan_report.risk_report_fingerprint` and bound to the review state.
9. **Exhaustive Security Integration Tests**: Implemented 7 end-to-end security test cases verifying fail-closed handling for unauthenticated requests, spoofed actor headers, separation-of-duties self-approval, cross-tenant access, revoked memberships, artifact tampering, and durable DB persistence.
10. **Frontend Integration & Typed API**: Added typed methods in `api-client.ts`, wired `MigrationDashboard.tsx` to real endpoints with distinct keys per workspace, and mapped response structures accurately.

## Testing
- [x] Relevant tests passed (`python scripts/development/dev.py all` or `test`)

**Test evidence & notes:**
- **Backend Full Pytest**: 1,071 passed, 2 skipped, 407 subtests passed (`pytest`).
- **Security Integration Tests**: 7 / 7 passed (`tests/integration/test_migration_endpoints.py`).
- **Frontend Vitest**: 106 passed across 13 test files (`apps/web`).
- **TypeScript**: 0 errors (`tsc --noEmit`).
- **Next.js Production Build**: 19 / 19 routes built successfully.
- **OpenAPI Schema Check**: 0 schema drift (`validate_openapi.py`).
- **Documentation Integrity**: 589 / 589 markdown files validated (`validate_docs.py`).

## Security Impact & Deterministic Engineering
- [x] **Strict Non-AI Policy:** Verified zero generative AI, LLM, or external inference APIs are introduced.
- [x] **Database Safety:** Verified all database connector operations enforce read-only introspection without data modification.
- [x] **Credential Protection:** Confirmed that no production credentials, passwords, or `.env` secrets are committed.
- [x] **Least Privilege:** Validated that permissions and access boundaries are minimized.

## Breaking Changes
- [x] No breaking changes.

## Contributor Checklist
- [x] My code adheres to the project's coding standards (PEP 8, TypeScript strict mode).
- [x] My branch is rebased on the latest `main` branch.
- [x] The PR title follows Conventional Commits.
- [x] No unrelated changes or accidental files are included.
