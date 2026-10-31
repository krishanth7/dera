"""DERA Diagnostics — Severity Subsystem.

Exposes deterministic severity policy, rationale formatting, and authorized overrides.
"""

from __future__ import annotations

from dera.diagnostics.severity.overrides import (
    SeverityOverride,
    UnauthorizedSeverityOverrideError,
    create_severity_override,
)
from dera.diagnostics.severity.policy import (
    SEVERITY_POLICY_VERSION,
    derive_effective_severity,
)
from dera.diagnostics.severity.rationale import build_severity_rationale
from dera.diagnostics.severity.validation import validate_severity_override

__all__ = [
    "SEVERITY_POLICY_VERSION",
    "SeverityOverride",
    "UnauthorizedSeverityOverrideError",
    "build_severity_rationale",
    "create_severity_override",
    "derive_effective_severity",
    "validate_severity_override",
]
