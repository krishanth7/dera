"""DERA Diagnostics — Authorized Severity Overrides.

Provides domain models and validation for actor-attributed severity overrides,
ensuring security and full audit traceability without silent modifications.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from dera.diagnostics.enums import DiagnosticSeverity
from dera.diagnostics.exceptions import DiagnosticEngineError


class UnauthorizedSeverityOverrideError(DiagnosticEngineError):
    """Raised when an unauthorized actor attempts to record a severity override."""

    def __init__(self, actor: str, reason: str) -> None:
        super().__init__(f"Unauthorized severity override by actor '{actor}': {reason}")
        self.actor = actor
        self.reason = reason


@dataclass(frozen=True)
class SeverityOverride:
    """Explicit, auditable record of an authorized severity modification."""

    override_id: str
    finding_fingerprint: str
    original_severity: DiagnosticSeverity
    effective_severity: DiagnosticSeverity
    override_reason: str
    authorized_actor: str
    timestamp: str
    policy_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if not self.finding_fingerprint:
            raise ValueError("SeverityOverride must specify a non-empty finding_fingerprint.")
        if not self.override_reason or len(self.override_reason.strip()) < 5:
            raise ValueError("SeverityOverride must include an explanatory override_reason.")
        if not self.authorized_actor or not self.authorized_actor.strip():
            raise UnauthorizedSeverityOverrideError(
                actor=self.authorized_actor,
                reason="Actor identifier cannot be empty.",
            )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "override_id": self.override_id,
            "finding_fingerprint": self.finding_fingerprint,
            "original_severity": self.original_severity.value,
            "effective_severity": self.effective_severity.value,
            "override_reason": self.override_reason,
            "authorized_actor": self.authorized_actor,
            "timestamp": self.timestamp,
            "policy_version": self.policy_version,
        }


def create_severity_override(
    finding_fingerprint: str,
    original_severity: DiagnosticSeverity,
    effective_severity: DiagnosticSeverity,
    override_reason: str,
    authorized_actor: str,
    policy_version: str = "1.0.0",
) -> SeverityOverride:
    """Factory creating an authenticated SeverityOverride record."""
    override_id = f"ovr_{uuid.uuid4().hex[:12]}"
    timestamp = datetime.now(UTC).isoformat()
    return SeverityOverride(
        override_id=override_id,
        finding_fingerprint=finding_fingerprint,
        original_severity=original_severity,
        effective_severity=effective_severity,
        override_reason=override_reason,
        authorized_actor=authorized_actor,
        timestamp=timestamp,
        policy_version=policy_version,
    )
