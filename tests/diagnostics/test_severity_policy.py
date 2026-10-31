"""DERA Diagnostics — Severity Policy and Rationale Unit Tests.

Validates deterministic severity derivation, conservative severity boundaries,
authorized overrides, rationale explanations, and policy versioning.
"""

from __future__ import annotations

import pytest
from dera.diagnostics.enums import DiagnosticSeverity
from dera.diagnostics.evidence.models import EvidenceCompleteness, FindingConfidence
from dera.diagnostics.prioritization.classification import FindingClassification
from dera.diagnostics.severity.overrides import (
    UnauthorizedSeverityOverrideError,
    create_severity_override,
)
from dera.diagnostics.severity.policy import (
    SEVERITY_POLICY_VERSION,
    derive_effective_severity,
)
from dera.diagnostics.severity.rationale import build_severity_rationale
from dera.diagnostics.severity.validation import validate_severity_override


def test_severity_policy_version() -> None:
    """Verifies severity policy version constant."""
    assert SEVERITY_POLICY_VERSION == "1.0.0"


@pytest.mark.parametrize(
    ("rule_id", "classification"),
    [
        ("DERA-MNT-001", FindingClassification.MAINTAINABILITY_CONCERN),  # Wide tables
        ("DERA-IDX-003", FindingClassification.OPTIMIZATION_CANDIDATE),  # Unindexed FK
        ("DERA-DEP-001", FindingClassification.POTENTIAL_ENGINEERING_CONCERN),  # Dependency cycle
        ("DERA-MNT-003", FindingClassification.NAMING_CONVENTION_DEVIATION),  # Naming deviation
        ("DERA-MNT-005", FindingClassification.MAINTAINABILITY_CONCERN),  # Namespace imbalance
    ],
)
def test_conservative_severity_bounds_prevent_critical(
    rule_id: str,
    classification: FindingClassification,
) -> None:
    """Verifies that non-critical rules are capped below CRITICAL per Section 13."""
    effective, rationale = derive_effective_severity(
        rule_id=rule_id,
        default_severity=DiagnosticSeverity.CRITICAL,
        classification=classification,
        completeness=EvidenceCompleteness.COMPLETE,
        confidence=FindingConfidence.VERIFIED,
    )
    assert effective.rank < DiagnosticSeverity.CRITICAL.rank
    assert effective in (DiagnosticSeverity.HIGH, DiagnosticSeverity.MEDIUM, DiagnosticSeverity.LOW)
    assert "conservative safety policy" in rationale or "Capped at" in rationale


def test_naming_convention_deviation_capped_at_low() -> None:
    """Verifies that naming convention deviations never exceed LOW severity."""
    effective, rationale = derive_effective_severity(
        rule_id="DERA-MNT-003",
        default_severity=DiagnosticSeverity.HIGH,
        classification=FindingClassification.NAMING_CONVENTION_DEVIATION,
        completeness=EvidenceCompleteness.COMPLETE,
        confidence=FindingConfidence.VERIFIED,
    )
    assert effective == DiagnosticSeverity.LOW
    assert "Capped at LOW" in rationale


def test_partial_metadata_caps_severity_at_medium() -> None:
    """Verifies that incomplete or partial metadata reduces high severity to MEDIUM."""
    effective, rationale = derive_effective_severity(
        rule_id="DERA-CON-001",
        default_severity=DiagnosticSeverity.HIGH,
        classification=FindingClassification.CONFIRMED_STRUCTURAL_DEFECT,
        completeness=EvidenceCompleteness.PARTIAL,
        confidence=FindingConfidence.CONDITIONAL,
    )
    assert effective == DiagnosticSeverity.MEDIUM
    assert "partial metadata completeness" in rationale


def test_unsupported_capability_reduces_to_informational() -> None:
    """Verifies that unsupported metadata capabilities downgrade severity to INFORMATIONAL."""
    effective, rationale = derive_effective_severity(
        rule_id="DERA-SCHEMA-003",
        default_severity=DiagnosticSeverity.HIGH,
        classification=FindingClassification.METADATA_LIMITATION,
        completeness=EvidenceCompleteness.UNSUPPORTED,
        confidence=FindingConfidence.UNSUPPORTED,
    )
    assert effective == DiagnosticSeverity.INFORMATIONAL
    assert "Reduced to INFORMATIONAL" in rationale


def test_build_severity_rationale_formatting() -> None:
    """Verifies human-readable severity rationale output."""
    rationale = build_severity_rationale(
        rule_id="DERA-CON-001",
        original_severity=DiagnosticSeverity.HIGH,
        effective_severity=DiagnosticSeverity.MEDIUM,
        classification=FindingClassification.CONFIRMED_STRUCTURAL_DEFECT,
        confidence=FindingConfidence.CONDITIONAL,
        completeness=EvidenceCompleteness.PARTIAL,
    )
    assert "Classification: Confirmed Structural Defect." in rationale
    assert "Evidence status: conditional (partial completeness)." in rationale
    assert "Adjusted from initial rule baseline of HIGH to MEDIUM" in rationale


def test_authorized_severity_override_creation() -> None:
    """Verifies creating an authorized severity override record."""
    override = create_severity_override(
        finding_fingerprint="abc123hash",
        original_severity=DiagnosticSeverity.HIGH,
        effective_severity=DiagnosticSeverity.LOW,
        override_reason="Accepted business deviation for legacy ingestion pipeline",
        authorized_actor="lead_dba@dera.org",
    )
    assert override.original_severity == DiagnosticSeverity.HIGH
    assert override.effective_severity == DiagnosticSeverity.LOW
    assert override.authorized_actor == "lead_dba@dera.org"
    assert override.policy_version == "1.0.0"

    canonical = override.to_canonical_dict()
    assert canonical["finding_fingerprint"] == "abc123hash"
    assert canonical["effective_severity"] == DiagnosticSeverity.LOW.value


def test_unauthorized_severity_override_rejected() -> None:
    """Verifies that empty actor or missing reason raises UnauthorizedSeverityOverrideError."""
    with pytest.raises(UnauthorizedSeverityOverrideError):
        create_severity_override(
            finding_fingerprint="abc123hash",
            original_severity=DiagnosticSeverity.HIGH,
            effective_severity=DiagnosticSeverity.LOW,
            override_reason="Valid reason",
            authorized_actor="",  # Empty actor
        )

    with pytest.raises(ValueError, match="override_reason"):
        create_severity_override(
            finding_fingerprint="abc123hash",
            original_severity=DiagnosticSeverity.HIGH,
            effective_severity=DiagnosticSeverity.LOW,
            override_reason="",  # Empty reason
            authorized_actor="dba@dera.org",
        )


def test_severity_override_safety_validation() -> None:
    """Verifies that overriding a style deviation to CRITICAL is rejected."""
    override = create_severity_override(
        finding_fingerprint="abc123hash",
        original_severity=DiagnosticSeverity.LOW,
        effective_severity=DiagnosticSeverity.CRITICAL,
        override_reason="Attempted escalation",
        authorized_actor="dba@dera.org",
    )
    is_valid, msg = validate_severity_override(
        override=override,
        classification=FindingClassification.NAMING_CONVENTION_DEVIATION,
    )
    assert not is_valid
    assert "violates conservative severity policy" in msg
