"""DERA Diagnostics — Governance Audit Logging.

Maintains immutable audit records for suppression actions, severity overrides,
and finding lifecycle events.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class GovernanceAuditRecord:
    """Immutable audit record logging an administrative or governance action."""

    audit_id: str
    action_type: str
    target_id: str
    actor: str
    timestamp: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "action_type": self.action_type,
            "target_id": self.target_id,
            "actor": self.actor,
            "timestamp": self.timestamp,
            "details": dict(sorted(self.details.items())),
        }


def record_governance_action(
    action_type: str,
    target_id: str,
    actor: str,
    details: dict[str, Any] | None = None,
) -> GovernanceAuditRecord:
    """Creates a timestamped, unique audit record for a governance event."""
    return GovernanceAuditRecord(
        audit_id=f"aud_{uuid.uuid4().hex[:12]}",
        action_type=action_type,
        target_id=target_id,
        actor=actor,
        timestamp=datetime.now(UTC).isoformat(),
        details=details or {},
    )
