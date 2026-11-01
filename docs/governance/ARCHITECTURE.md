# Phase 9.5 Migration Governance Architecture

## Overview
Phase 9.5 establishes DERA's **Production-Grade Migration Governance, Review, Approval, and Safety Control Engine**.
It wraps Phase 9.4 generated SQL migration artifacts in an immutable review lifecycle, enforcing separation of duties, role-based authorization, safety gates, quorum requirements, approval invalidation upon artifact mutation, and tamper-evident append-only audit chaining.

```text
Phase 9.4 SQL Migration Artifact
              │
              ▼
    Artifact Validation Gate (SHA-256 Digest Check)
              │
              ▼
    Migration Review Request (State: DRAFT -> SUBMITTED)
              │
              ▼
    Governance Policy Engine & Safety Gates
    ├── Status Gate (Not blocked / unsupported)
    ├── Validation Gate (Zero syntax/quote errors)
    ├── Destructive Changes Gate (Requires Admin)
    └── Manual Review Gate
              │
              ▼
    Review Decisions & RBAC Evaluation
    ├── Role Verification (Owner, Admin, Editor)
    └── Separation of Duties (Requester != Approver)
              │
              ▼
    Approval Quorum Evaluation
    ├── Distinct Approvals Count >= Quorum
    └── Mandatory Admin Sign-Off for Destructive Changes
              │
      ┌───────┴───────┐
      ▼               ▼
   APPROVED        REJECTED / CHANGES_REQUESTED
      │
      ▼
Append-Only Cryptographic Audit Hash Chain (SHA-256)
      │
      ▼
Controlled Export Eligibility Assessment
      │
      ▼
Approval Evidence Bundle
```

## Architectural Tenets
1. **Zero-AI / Zero-Probabilistic Logic:** Pure deterministic Python state machine and policy evaluation.
2. **Review-Only & Advisory:** Approving a review request does not execute SQL against any database.
3. **Separation of Duties:** Requesters are strictly prohibited from approving their own migration review requests.
4. **Approval Invalidation:** If an underlying SQL artifact is modified, all prior approvals are immediately invalidated and the review is blocked.
5. **Tamper-Evident Hash Chain:** All governance lifecycle events are chained via SHA-256 hashes linking to prior event hashes.
