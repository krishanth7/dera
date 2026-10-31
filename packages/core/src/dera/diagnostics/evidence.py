"""DERA Diagnostics — Typed Evidence Model.

Provides structured, immutable, sanitizable evidence records supporting
deterministic diagnostic findings without leaking credentials or row data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Patterns to sanitize from evidence values and context data
_SENSITIVE_KEY_PATTERN = re.compile(
    r"(?i)(password|secret|token|api_key|credential|private_key|auth|connection_string)"
)
_CONNECTION_STRING_PATTERN = re.compile(r"://[^:]+:[^@]+@")


def sanitize_value(val: Any) -> Any:
    """Recursively removes sensitive strings and credentials from evidence values."""
    if isinstance(val, str):
        # Redact embedded password credentials in connection URLs
        return _CONNECTION_STRING_PATTERN.sub("://***:***@", val)
    if isinstance(val, dict):
        sanitized_dict: dict[str, Any] = {}
        for k, v in val.items():
            if _SENSITIVE_KEY_PATTERN.search(str(k)):
                sanitized_dict[str(k)] = "[REDACTED]"
            else:
                sanitized_dict[str(k)] = sanitize_value(v)
        return sanitized_dict
    if isinstance(val, (list, tuple)):
        return [sanitize_value(item) for item in val]
    return val


@dataclass(frozen=True)
class DiagnosticEvidence:
    """Represents a discrete, verifiable piece of evidence supporting a finding."""

    object_id: str
    field_name: str
    observed_value: Any
    expected_value: Any | None = None
    message: str = ""
    provenance_reference: str | None = None
    context_data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.object_id:
            raise ValueError("DiagnosticEvidence must specify a non-empty object_id.")
        if not self.field_name:
            raise ValueError("DiagnosticEvidence must specify a non-empty field_name.")

        # Sanitize observed_value and context_data to prevent credential leakage
        object.__setattr__(self, "observed_value", sanitize_value(self.observed_value))
        if self.expected_value is not None:
            object.__setattr__(self, "expected_value", sanitize_value(self.expected_value))
        if self.context_data:
            object.__setattr__(self, "context_data", sanitize_value(self.context_data))

    def to_canonical_dict(self) -> dict[str, Any]:
        """Produces a deterministic dictionary representation for hashing and JSON output."""
        return {
            "object_id": self.object_id,
            "field_name": self.field_name,
            "observed_value": self.observed_value,
            "expected_value": self.expected_value,
            "message": self.message,
            "provenance_reference": self.provenance_reference,
            "context_data": dict(sorted(self.context_data.items())),
        }
