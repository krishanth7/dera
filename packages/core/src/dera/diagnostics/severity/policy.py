"""DERA Diagnostics — Severity Policy Engine.

Enforces deterministic, conservative severity derivation based on rule semantics,
verified evidence, object scope, and metadata completeness without artificial inflation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dera.diagnostics.enums import DiagnosticSeverity
from dera.diagnostics.evidence.models import EvidenceCompleteness, FindingConfidence
from dera.diagnostics.prioritization.classification import FindingClassification

if TYPE_CHECKING:
    pass

SEVERITY_POLICY_VERSION = "1.0.0"

# Rules strictly prohibited from escalating to CRITICAL
_NON_CRITICAL_RULE_PATTERNS = (
    "DERA-MNT-001",  # Wide tables
    "DERA-IDX-003",  # Unindexed foreign keys
    "DERA-DEP-001",  # Dependency cycles
    "DERA-MNT-003",  # Naming convention deviations
    "DERA-MNT-005",  # Namespace imbalance
)


def derive_effective_severity(
    rule_id: str,
    default_severity: DiagnosticSeverity,
    classification: FindingClassification,
    completeness: EvidenceCompleteness,
    confidence: FindingConfidence,
) -> tuple[DiagnosticSeverity, str]:
    """Deterministically derives the effective severity and explanation.

    Applies conservative guardrails:
      - Prevents CRITICAL severity on maintainability, style, or indexing candidates.
      - Caps severity at MEDIUM when metadata is PARTIAL or confidence is CONDITIONAL/INCOMPLETE.
      - Demotes severity when evidence is UNSUPPORTED.
    """
    rule_upper = rule_id.upper()
    effective = default_severity
    rationale_points: list[str] = [
        f"Base severity '{default_severity.value}' assigned by rule '{rule_id}'."
    ]

    # Guardrail 1: Enforce conservative bounds on non-critical rules (Section 13)
    if any(pattern in rule_upper for pattern in _NON_CRITICAL_RULE_PATTERNS):
        if effective == DiagnosticSeverity.CRITICAL:
            effective = DiagnosticSeverity.HIGH
            rationale_points.append(
                f"Capped at HIGH per conservative safety policy: {classification.display_name} "
                "cannot be assigned CRITICAL without verified active transactional blockage."
            )

    # Guardrail 2: Style & naming deviations are capped at LOW
    if classification == FindingClassification.NAMING_CONVENTION_DEVIATION:
        if effective.rank > DiagnosticSeverity.LOW.rank:
            effective = DiagnosticSeverity.LOW
            rationale_points.append(
                "Capped at LOW: Naming deviations represent engineering style preferences, not defects."
            )

    # Guardrail 3: Optimization candidates are capped at MEDIUM unless proven defect
    if classification == FindingClassification.OPTIMIZATION_CANDIDATE:
        if effective.rank > DiagnosticSeverity.MEDIUM.rank:
            effective = DiagnosticSeverity.MEDIUM
            rationale_points.append(
                "Capped at MEDIUM: Optimization recommendations require workload verification."
            )

    # Guardrail 4: Incomplete or partial metadata caps severity at MEDIUM
    if completeness in (EvidenceCompleteness.PARTIAL, EvidenceCompleteness.RESTRICTED):
        if effective.rank > DiagnosticSeverity.MEDIUM.rank:
            effective = DiagnosticSeverity.MEDIUM
            rationale_points.append(
                f"Reduced to MEDIUM due to {completeness.value} metadata completeness."
            )

    # Guardrail 5: Unsupported metadata reduces to INFORMATIONAL
    if (
        completeness == EvidenceCompleteness.UNSUPPORTED
        or confidence == FindingConfidence.UNSUPPORTED
    ):
        effective = DiagnosticSeverity.INFORMATIONAL
        rationale_points.append(
            "Reduced to INFORMATIONAL: Connector does not support required metadata capability."
        )

    # Guardrail 6: Incomplete confidence reduces by one level
    if confidence == FindingConfidence.INCOMPLETE:
        if effective.rank > DiagnosticSeverity.LOW.rank:
            effective = DiagnosticSeverity.LOW
            rationale_points.append(
                "Reduced to LOW: Incomplete evidence precludes confirming a defect."
            )

    rationale = " ".join(rationale_points)
    return effective, rationale
