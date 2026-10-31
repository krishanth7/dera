# Suppression Governance Specification

## Overview

DERA Phase 8.5 implements auditable, authorized suppression governance. Uncontrolled or silent suppression of diagnostic findings is strictly prohibited. Findings may be exempted only through explicit, scoped, authorized records that preserve full visibility in compliance audits.

## Suppression Model

A suppression record contains:
- `suppression_id`: Cryptographically secure unique identifier
- `rule_id`: Target diagnostic rule or `*` (global scope requires admin privileges)
- `scope`: `FINDING_FINGERPRINT`, `OBJECT_ID`, `RULE`, or `GLOBAL`
- `target_identifier`: The specific fingerprint or object ID being suppressed
- `reason`: Mandatory justification explaining the engineering exemption
- `authorized_actor`: Verified user/service identity applying the suppression
- `created_at`: UTC timestamp of creation
- `expires_at`: Optional expiration timestamp for temporary exemptions
- `status`: `ACTIVE`, `EXPIRED`, or `REVOKED`

## Expiration and Revocation

- **Deterministic Expiration**: Evaluations check active suppressions against the current timestamp. If `expires_at` has passed, the suppression is marked `EXPIRED`, and the finding reverts to active evaluation.
- **Revocation**: Authorized administrators may explicitly revoke a suppression before expiration.

## Audit and Visibility Guarantee

- **No Silent Drops**: Suppressed findings are **never** omitted from diagnostic reports.
- **Reporting Visibility**: Suppressed findings appear in the report with `suppression_state.is_suppressed = true`, detailing the active suppression ID and reason.
- **Audit Logging**: All suppression creations, revocations, and expirations are logged in an append-only audit register.
