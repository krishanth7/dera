"""DERA Diagnostics — Severity Rationale Generator.

Produces human-readable, deterministic explanations explaining why a specific
severity level was assigned to a diagnostic finding.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dera.diagnostics.enums import DiagnosticSeverity
    from dera.diagnostics.evidence.models import EvidenceCompleteness, FindingConfidence
    from dera.diagnostics.prioritization.classification import FindingClassification


def build_severity_rationale(
    rule_id: str,
    original_severity: DiagnosticSeverity,
    effective_severity: DiagnosticSeverity,
    classification: FindingClassification,
    confidence: FindingConfidence,
    completeness: EvidenceCompleteness,
    rule_reason: str = "",
) -> str:
    """Builds an explainable severity rationale string detailing rule conditions,
    classification impact, and policy adjustments.
    """
    statements: list[str] = []

    if rule_reason:
        statements.append(rule_reason.strip())
    else:
        statements.append(
            f"Assigned {effective_severity.value.upper()} severity under policy version 1.0.0."
        )

    statements.append(f"Classification: {classification.display_name}.")
    statements.append(f"Evidence status: {confidence.value} ({completeness.value} completeness).")

    if original_severity != effective_severity:
        statements.append(
            f"Adjusted from initial rule baseline of {original_severity.value.upper()} to "
            f"{effective_severity.value.upper()} based on conservative safety policy."
        )

    return " ".join(statements)
