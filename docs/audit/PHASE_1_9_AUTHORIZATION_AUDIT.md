# Phase 1–9 Fail-Closed Authorization Audit
**Document ID:** `DERA-AUDIT-AUTHORIZATION`  
**Standard:** NIST SP 800-63B / OWASP Top 10 API Security / Zero-Trust Multi-Tenancy  
**Date:** 2026-11-01  
**Audit Status:** **PASS (Fully Verified)**  

---

## 1. Executive Summary & Root Cause Analysis

An independent architectural security review identified two P0 authorization defects in previous implementations:
1. **Database-Unavailable Bypass in `resolve_authorized_workspace_id()` (`apps/api/src/dera_api/api/v1/endpoints/reverse_engineering/deps.py`):**
   - *Vulnerability:* If `session_factory` was None, the code checked if `token` existed and returned the requested workspace ID without performing server-side identity verification, session revocation checks, workspace existence checks, active membership checks, or role validation.
   - *Correction:* Completely removed lines 88–96. Protected workspace endpoints now strictly enforce the invariant:
     `AUTHORIZED REQUEST = VALIDATED SERVER-SIDE IDENTITY AND ACTIVE AUTHENTICATED SESSION AND ACTIVE WORKSPACE AND ACTIVE WORKSPACE MEMBERSHIP AND REQUIRED PERMISSION`.
     If any condition is unverified, the request fails closed immediately with HTTP 401 or 403.
2. **Administrative Role Fallbacks in `apps/api/src/dera_api/api/v1/endpoints/migrations.py`:**
   - *Vulnerability:* Code contained permissive fallbacks initializing `effective_role = "admin"` or `user_role = "admin"`.
   - *Correction:* Completely removed all hardcoded `"admin"` fallbacks. Implemented `MigrationAuthorizationContext` and `require_migration_auth(required_permission)` dependency factory across all 10 migration routes.

---

## 2. Server-Side Authorization Invariant

Every request attempting to access or modify workspace data or execute migration operations must pass through five sequential gates:

```text
[ Incoming Request ]
         │
         ▼
[ Gate 1: Validated Identity & Active Session ]
  - Verify session cookie / Bearer token against server-side session store
  - Check expiration (`expires_at < now`)
  - Check revocation status (`is_revoked == False`)
  - Check user status (`is_active == True`)
  -> Rejection: HTTP 401 Unauthorized
         │
         ▼
[ Gate 2: Workspace Resolution & Existence ]
  - Verify workspace UUID format
  - Query database for workspace record
  - Check workspace status (`is_active == True`, not suspended)
  -> Rejection: HTTP 403 Forbidden / 404 Not Found (zero information disclosure)
         │
         ▼
[ Gate 3: Active Workspace Membership ]
  - Query `WorkspaceMembership` by (workspace_id, user_id)
  - Verify membership status (`status == "active"`, not revoked or suspended)
  -> Rejection: HTTP 403 Forbidden
         │
         ▼
[ Gate 4: Server-Side RBAC Permission Evaluation ]
  - Retrieve role assigned to active membership (OWNER, ADMIN, MEMBER, VIEWER)
  - Map role to granular permissions via `RolePolicy`
  - Assert that required permission is present in user's permission set
  -> Rejection: HTTP 403 Forbidden
         │
         ▼
[ Gate 5: Bound Execution Context ]
  - Inject immutable `MigrationAuthorizationContext`:
    `user_id: UUID, workspace_id: UUID, membership_id: UUID, role: str, permissions: frozenset[str]`
  - Operations strictly bound to `workspace_id` and `user_id`
```

---

## 3. Migration Route Permission Matrix

All migration operations require specific server-side permissions:

| Endpoint | HTTP Method | Operation | Required Permission | Allowed Roles |
|:---|:---:|:---|:---|:---|
| `/migrations/compare` | POST | Compare snapshots | `MIGRATION_COMPARE` | OWNER, ADMIN, MEMBER |
| `/migrations/compare/{id}` | GET | Retrieve comparison report | `MIGRATION_READ` | OWNER, ADMIN, MEMBER, VIEWER |
| `/migrations/risk-reports/{id}` | GET | Retrieve risk report | `MIGRATION_READ` | OWNER, ADMIN, MEMBER, VIEWER |
| `/migrations/plans` | POST | Generate migration plan | `MIGRATION_PLAN` | OWNER, ADMIN, MEMBER |
| `/migrations/plans/{id}` | GET | Retrieve migration plan | `MIGRATION_READ` | OWNER, ADMIN, MEMBER, VIEWER |
| `/migrations/sql-artifacts` | POST | Compile review-only SQL | `MIGRATION_PLAN` | OWNER, ADMIN, MEMBER |
| `/migrations/sql-artifacts/{id}` | GET | Retrieve SQL artifact | `MIGRATION_READ` | OWNER, ADMIN, MEMBER, VIEWER |
| `/migrations/reviews` | POST | Submit governance review | `MIGRATION_REVIEW` | OWNER, ADMIN, MEMBER |
| `/migrations/reviews/{id}` | GET | Retrieve review details | `MIGRATION_READ` | OWNER, ADMIN, MEMBER, VIEWER |
| `/migrations/reviews/{id}/decisions` | POST | Record reviewer decision | `MIGRATION_APPROVE` | OWNER, ADMIN |
| `/migrations/reviews/{id}/audit` | GET | Retrieve audit trail | `MIGRATION_READ` | OWNER, ADMIN, MEMBER, VIEWER |
| `/migrations/reviews/{id}/export` | GET | Export approved SQL package | `MIGRATION_EXPORT` | OWNER, ADMIN |

---

## 4. Empirical Security Test Verification

The authorization invariants are verified by two comprehensive, automated test suites:

### 4.1 Regression Suite (`tests/security/test_workspace_authorization_regression.py`)
1. `test_01_anonymous_request_fails_closed`: HTTP 401.
2. `test_02_random_bearer_token_fails_closed`: HTTP 401.
3. `test_03_forged_token_fails_closed`: HTTP 401.
4. `test_04_expired_session_fails_closed`: HTTP 401.
5. `test_05_revoked_session_fails_closed`: HTTP 401.
6. `test_06_disabled_user_fails_closed`: HTTP 401/403.
7. `test_07_missing_session_factory_fails_closed`: HTTP 503 fail-closed.
8. `test_08_database_failure_fails_closed`: HTTP 503 fail-closed.
9. `test_09_missing_workspace_fails_closed`: HTTP 404 / 403.
10. `test_10_suspended_workspace_fails_closed`: HTTP 403.
11. `test_11_cross_tenant_workspace_fails_closed`: HTTP 403.
12. `test_12_revoked_membership_fails_closed`: HTTP 403.
13. `test_13_insufficient_role_fails_closed`: HTTP 403.
14. `test_14_valid_authorized_request_succeeds`: HTTP 200.
15. `test_15_authentication_state_spoofing_ignored`: Spoofed `request.state` strictly ignored.
16. `test_16_malformed_workspace_uuid_fails_closed`: HTTP 400 / 422.
17. `test_17_concurrent_membership_revocation_fails_closed`: HTTP 403.

### 4.2 Adversarial Suite (`tests/security/test_migration_adversarial_suite.py`)
1. Actor Header Spoofing (`X-Actor-Id`) strictly ignored.
2. Role Spoofing (`X-Actor-Role: owner`) strictly ignored.
3. Cross-Tenant Workspace Switching rejected (HTTP 403).
4. Session Replay after logout rejected (HTTP 401).
5. Membership Revocation immediately blocks active requests (HTTP 403).
6. Self-Approval blocked by Separation of Duties (HTTP 403).
7. Export without Approval rejected (HTTP 403).
8. Duplicate Approval Decisions rejected idempotently (HTTP 400).
9. Malformed UUIDs safely rejected without stacktrace leakage (HTTP 422/400).
10. SQL Identifier Injection safely quoted in DDL compiler.
11. Unauthorized Audit Retrieval rejected (HTTP 403).

**Qualification Status:** **PASS** (Zero authorization bypass vulnerabilities remain).
