"""DERA Diagnostics — Suppression Governance and Lifecycle Unit Tests.

Validates suppression scopes, authorization enforcement, expiration checks,
lifecycle state transitions, and audit trail records.
"""

from __future__ import annotations

import pytest
from dera.diagnostics.enums import DiagnosticSeverity
from dera.diagnostics.evidence import DiagnosticEvidence
from dera.diagnostics.governance import (
    FindingLifecycleState,
    InvalidLifecycleTransitionError,
    SuppressionScope,
    UnauthorizedSuppressionError,
    create_suppression,
    record_governance_action,
    transition_lifecycle_state,
)
from dera.diagnostics.models import DiagnosticFinding


def test_create_fingerprint_scoped_suppression() -> None:
    """Verifies creating a suppression scoped to a specific finding fingerprint."""
    sup = create_suppression(
        scope=SuppressionScope.FINGERPRINT,
        fingerprint="sha256_hash_12345",
        reason="Planned migration scheduled for Q4",
        authorized_actor="security_architect@dera.org",
    )
    assert sup.scope == SuppressionScope.FINGERPRINT
    assert sup.fingerprint == "sha256_hash_12345"
    assert sup.is_active() is True

    canonical = sup.to_canonical_dict()
    assert canonical["scope"] == "fingerprint"
    assert canonical["fingerprint"] == "sha256_hash_12345"
    assert canonical["status"] == "active"


def test_suppression_matches_rule_and_object() -> None:
    """Verifies suppression matching logic across scopes."""
    ev = DiagnosticEvidence(object_id="public.users", field_name="pk", observed_value=None)
    finding = DiagnosticFinding(
        rule_id="DERA-CON-001",
        rule_version="1.0.0",
        object_id="public.users",
        severity=DiagnosticSeverity.HIGH,
        title="Missing PK",
        description="Desc",
        evidence=(ev,),
        severity_rationale="Rationale",
    )

    # 1. Fingerprint match
    sup_fp = create_suppression(
        scope=SuppressionScope.FINGERPRINT,
        fingerprint=finding.fingerprint,
        reason="Accepted fingerprint",
        authorized_actor="dba@dera.org",
    )
    assert sup_fp.matches(finding) is True

    # 2. Object match
    sup_obj = create_suppression(
        scope=SuppressionScope.OBJECT,
        scoped_object_id="public.users",
        reason="Whole table suppressed",
        authorized_actor="dba@dera.org",
    )
    assert sup_obj.matches(finding) is True

    # 3. Rule match
    sup_rule = create_suppression(
        scope=SuppressionScope.RULE,
        rule_id="DERA-CON-001",
        reason="Rule suppressed",
        authorized_actor="dba@dera.org",
    )
    assert sup_rule.matches(finding) is True

    # 4. Non-matching object
    sup_other = create_suppression(
        scope=SuppressionScope.OBJECT,
        scoped_object_id="public.orders",
        reason="Other table",
        authorized_actor="dba@dera.org",
    )
    assert sup_other.matches(finding) is False


def test_suppression_expiration() -> None:
    """Verifies that past expiration dates render suppressions inactive."""
    sup = create_suppression(
        scope=SuppressionScope.FINGERPRINT,
        fingerprint="sha256_test",
        reason="Temporary exception",
        authorized_actor="dba@dera.org",
        expires_at="2020-01-01T00:00:00Z",  # Expired in past
    )
    assert sup.is_active(current_time="2026-10-31T12:00:00Z") is False


def test_unauthorized_suppression_rejected() -> None:
    """Verifies that missing actor or invalid reasons raise errors."""
    with pytest.raises(UnauthorizedSuppressionError):
        create_suppression(
            scope=SuppressionScope.RULE,
            rule_id="DERA-CON-001",
            reason="Valid reason here",
            authorized_actor="",  # Empty actor
        )

    with pytest.raises(ValueError, match="reason"):
        create_suppression(
            scope=SuppressionScope.RULE,
            rule_id="DERA-CON-001",
            reason="",  # Empty reason
            authorized_actor="dba@dera.org",
        )


def test_finding_lifecycle_transitions() -> None:
    """Verifies valid lifecycle state machine transitions."""
    state = FindingLifecycleState.OPEN

    # Transition OPEN -> ACKNOWLEDGED
    state = transition_lifecycle_state(
        current=state,
        target=FindingLifecycleState.ACKNOWLEDGED,
        actor="engineer@dera.org",
        reason="Reviewed and logged ticket",
    )
    assert state == FindingLifecycleState.ACKNOWLEDGED

    # Transition ACKNOWLEDGED -> SUPPRESSED
    state = transition_lifecycle_state(
        current=state,
        target=FindingLifecycleState.SUPPRESSED,
        actor="lead_dba@dera.org",
        reason="Granted exception",
    )
    assert state == FindingLifecycleState.SUPPRESSED

    # Transition SUPPRESSED -> REOPENED
    state = transition_lifecycle_state(
        current=state,
        target=FindingLifecycleState.REOPENED,
        actor="lead_dba@dera.org",
        reason="Exception expired",
    )
    assert state == FindingLifecycleState.REOPENED


def test_invalid_lifecycle_transition_raises_error() -> None:
    """Verifies invalid transitions are rejected."""
    with pytest.raises(InvalidLifecycleTransitionError):
        # Cannot jump from OPEN directly to REOPENED
        transition_lifecycle_state(
            current=FindingLifecycleState.OPEN,
            target=FindingLifecycleState.REOPENED,
            actor="engineer@dera.org",
            reason="Invalid transition attempt",
        )


def test_governance_audit_logging() -> None:
    """Verifies immutable audit trail recording."""
    record = record_governance_action(
        action_type="SUPPRESSION_CREATED",
        target_id="sup_12345",
        actor="admin@dera.org",
        details={"scope": "fingerprint", "rule_id": "DERA-CON-001"},
    )
    assert record.action_type == "SUPPRESSION_CREATED"
    assert record.target_id == "sup_12345"
    assert record.actor == "admin@dera.org"
    canonical = record.to_canonical_dict()
    assert canonical["action_type"] == "SUPPRESSION_CREATED"
