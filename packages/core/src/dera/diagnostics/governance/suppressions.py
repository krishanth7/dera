"""DERA Diagnostics — Finding Suppression Governance.

Provides structured, authorized, and auditable suppression models supporting
fine-grained scopes, deterministic expiration, and transparent reporting.
Suppressed findings are never silently dropped; they remain fully inspectable.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from dera.diagnostics.exceptions import DiagnosticEngineError

if TYPE_CHECKING:
    pass


class UnauthorizedSuppressionError(DiagnosticEngineError):
    """Raised when an unauthorized actor attempts to record a finding suppression."""

    def __init__(self, actor: str, reason: str) -> None:
        super().__init__(f"Unauthorized suppression by actor '{actor}': {reason}")
        self.actor = actor
        self.reason = reason


class SuppressionScope(StrEnum):
    """Scope defining the boundary of a finding suppression."""

    FINGERPRINT = "fingerprint"
    OBJECT = "object"
    RULE = "rule"


class SuppressionStatus(StrEnum):
    """Lifecycle status of a suppression entry."""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass(frozen=True)
class DiagnosticSuppression:
    """Explicit, auditable record governing finding suppression."""

    suppression_id: str
    scope: SuppressionScope
    reason: str
    authorized_actor: str
    created_at: str
    rule_id: str | None = None
    fingerprint: str | None = None
    scoped_object_id: str | None = None
    expires_at: str | None = None
    status: SuppressionStatus = SuppressionStatus.ACTIVE
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.reason or len(self.reason.strip()) < 5:
            raise ValueError("DiagnosticSuppression must specify a meaningful reason (>= 5 chars).")
        if not self.authorized_actor or not self.authorized_actor.strip():
            raise UnauthorizedSuppressionError(
                actor=self.authorized_actor,
                reason="Actor identifier cannot be empty.",
            )

        if self.scope == SuppressionScope.FINGERPRINT and not self.fingerprint:
            raise ValueError("Fingerprint-scoped suppression must specify a fingerprint.")
        if self.scope == SuppressionScope.OBJECT and not self.scoped_object_id:
            raise ValueError("Object-scoped suppression must specify a scoped_object_id.")
        if self.scope == SuppressionScope.RULE and not self.rule_id:
            raise ValueError("Rule-scoped suppression must specify a rule_id.")

    def is_active(self, current_time: str | None = None) -> bool:
        """Determines whether the suppression is currently active and unexpired."""
        if self.status != SuppressionStatus.ACTIVE:
            return False

        if self.expires_at is not None:
            now_iso = current_time or datetime.now(UTC).isoformat()
            # ISO 8601 string comparison is deterministic for UTC strings
            if now_iso >= self.expires_at:
                return False

        return True

    def matches(self, finding: Any) -> bool:
        """Checks whether this suppression matches the target finding."""
        if self.scope == SuppressionScope.FINGERPRINT:
            return getattr(finding, "fingerprint", None) == self.fingerprint

        if self.scope == SuppressionScope.OBJECT:
            obj_id = getattr(finding, "object_id", "")
            matches_obj = obj_id == self.scoped_object_id
            if self.rule_id:
                return matches_obj and getattr(finding, "rule_id", "") == self.rule_id
            return matches_obj

        if self.scope == SuppressionScope.RULE:
            return getattr(finding, "rule_id", "") == self.rule_id

        return False

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "suppression_id": self.suppression_id,
            "scope": self.scope.value,
            "rule_id": self.rule_id,
            "fingerprint": self.fingerprint,
            "scoped_object_id": self.scoped_object_id,
            "reason": self.reason,
            "authorized_actor": self.authorized_actor,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "status": self.status.value,
            "notes": self.notes,
        }


def create_suppression(
    scope: SuppressionScope,
    reason: str,
    authorized_actor: str,
    rule_id: str | None = None,
    fingerprint: str | None = None,
    scoped_object_id: str | None = None,
    expires_at: str | None = None,
    notes: str = "",
) -> DiagnosticSuppression:
    """Factory creating an authenticated DiagnosticSuppression record."""
    suppression_id = f"sup_{uuid.uuid4().hex[:12]}"
    created_at = datetime.now(UTC).isoformat()

    return DiagnosticSuppression(
        suppression_id=suppression_id,
        scope=scope,
        rule_id=rule_id,
        fingerprint=fingerprint,
        scoped_object_id=scoped_object_id,
        reason=reason,
        authorized_actor=authorized_actor,
        created_at=created_at,
        expires_at=expires_at,
        status=SuppressionStatus.ACTIVE,
        notes=notes,
    )
