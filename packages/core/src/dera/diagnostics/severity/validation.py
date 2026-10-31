"""DERA Diagnostics — Severity Validation Engine.

Enforces boundary rules and security policies on severity evaluations and overrides.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dera.diagnostics.enums import DiagnosticSeverity
from dera.diagnostics.prioritization.classification import FindingClassification

if TYPE_CHECKING:
    from dera.diagnostics.severity.overrides import SeverityOverride


def validate_severity_override(
    override: SeverityOverride,
    classification: FindingClassification,
) -> tuple[bool, str]:
    """Validates whether a requested severity override adheres to safety policy."""
    # Prevent overriding style deviations to CRITICAL
    if classification == FindingClassification.NAMING_CONVENTION_DEVIATION:
        if override.effective_severity == DiagnosticSeverity.CRITICAL:
            return (
                False,
                "Cannot override naming convention deviation to CRITICAL: violates conservative severity policy.",
            )

    return True, "Severity override is valid."
