"""Phase 9.5 Migration Governance Enums.

Defines deterministic enumeration types for the review lifecycle, safety gate outcomes,
decision types, and export eligibility statuses.
"""

from enum import StrEnum


class ReviewLifecycleStatus(StrEnum):
    """Authoritative states in the migration review lifecycle."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    SUPERSEDED = "SUPERSEDED"
    BLOCKED = "BLOCKED"


class SafetyGateStatus(StrEnum):
    """Outcome of evaluating an individual governance safety gate."""

    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ReviewDecisionType(StrEnum):
    """Decision submitted by an assigned reviewer."""

    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    ABSTAIN = "ABSTAIN"


class ExportEligibilityStatus(StrEnum):
    """Evaluation status for controlled artifact export."""

    ELIGIBLE_FOR_CONTROLLED_EXPORT = "ELIGIBLE_FOR_CONTROLLED_EXPORT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
