"""DERA Diagnostics — Governance Subsystem.

Exposes suppression governance, finding lifecycle tracking, and immutable audit logging.
"""

from __future__ import annotations

from dera.diagnostics.governance.audit import (
    GovernanceAuditRecord,
    record_governance_action,
)
from dera.diagnostics.governance.lifecycle import (
    FindingLifecycleState,
    InvalidLifecycleTransitionError,
    transition_lifecycle_state,
)
from dera.diagnostics.governance.suppressions import (
    DiagnosticSuppression,
    SuppressionScope,
    SuppressionStatus,
    UnauthorizedSuppressionError,
    create_suppression,
)

__all__ = [
    "DiagnosticSuppression",
    "FindingLifecycleState",
    "GovernanceAuditRecord",
    "InvalidLifecycleTransitionError",
    "SuppressionScope",
    "SuppressionStatus",
    "UnauthorizedSuppressionError",
    "create_suppression",
    "record_governance_action",
    "transition_lifecycle_state",
]
