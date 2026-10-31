"""DERA Diagnostics — Typed Evidence Domain Models.

Defines structured, immutable evidence models supporting verified traceability,
completeness indicators, finding confidence, and cryptographic reproducibility.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

# Sensitive patterns to sanitize from evidence values and context data
_SENSITIVE_KEY_PATTERN = re.compile(
    r"(?i)(password|secret|token|api_key|credential|private_key|auth|connection_string|access_key)"
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


class EvidenceType(StrEnum):
    """Categorical type of verifiable evidence."""

    CANONICAL_OBJECT_REFERENCE = "canonical_object_reference"
    COLUMN_REFERENCE = "column_reference"
    CONSTRAINT_REFERENCE = "constraint_reference"
    INDEX_REFERENCE = "index_reference"
    GRAPH_EDGE_REFERENCE = "graph_edge_reference"
    METRIC_OBSERVATION = "metric_observation"
    THRESHOLD_COMPARISON = "threshold_comparison"
    METADATA_CAPABILITY_STATE = "metadata_capability_state"
    SNAPSHOT_REFERENCE = "snapshot_reference"
    PROVENANCE_REFERENCE = "provenance_reference"


class EvidenceCompleteness(StrEnum):
    """Assessment of whether the metadata supporting this evidence is complete."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    RESTRICTED = "restricted"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


class FindingConfidence(StrEnum):
    """Categorical confidence indicating evidential soundness without statistical guessing."""

    VERIFIED = "verified"
    CONDITIONAL = "conditional"
    INCOMPLETE = "incomplete"
    UNSUPPORTED = "unsupported"

    @property
    def rank(self) -> int:
        """Deterministic numeric weight for prioritization sorting."""
        weights = {
            FindingConfidence.VERIFIED: 4,
            FindingConfidence.CONDITIONAL: 3,
            FindingConfidence.INCOMPLETE: 2,
            FindingConfidence.UNSUPPORTED: 1,
        }
        return weights[self]


@dataclass(frozen=True)
class EvidenceProvenance:
    """Audit provenance tracking the origin of an evidence record."""

    source_engine: str
    connector_version: str = "1.0.0"
    inspection_timestamp: str = ""
    snapshot_id: str | None = None
    canonical_object_id: str = ""
    capability_state: str | None = None

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "source_engine": self.source_engine,
            "connector_version": self.connector_version,
            "inspection_timestamp": self.inspection_timestamp,
            "snapshot_id": self.snapshot_id,
            "canonical_object_id": self.canonical_object_id,
            "capability_state": self.capability_state,
        }


@dataclass(frozen=True)
class DiagnosticEvidence:
    """Discrete, verifiable piece of evidence supporting a diagnostic finding."""

    object_id: str
    field_name: str
    observed_value: Any
    expected_value: Any | None = None
    message: str = ""
    provenance_reference: str | None = None
    context_data: dict[str, Any] = field(default_factory=dict)
    evidence_type: EvidenceType = EvidenceType.CANONICAL_OBJECT_REFERENCE
    completeness: EvidenceCompleteness = EvidenceCompleteness.COMPLETE
    provenance: EvidenceProvenance | None = None

    def __post_init__(self) -> None:
        if not self.object_id:
            raise ValueError("DiagnosticEvidence must specify a non-empty object_id.")
        if not self.field_name:
            raise ValueError("DiagnosticEvidence must specify a non-empty field_name.")

        # Sanitize observed_value, expected_value, and context_data
        object.__setattr__(self, "observed_value", sanitize_value(self.observed_value))
        if self.expected_value is not None:
            object.__setattr__(self, "expected_value", sanitize_value(self.expected_value))
        if self.context_data:
            object.__setattr__(self, "context_data", sanitize_value(self.context_data))

    def to_canonical_dict(self) -> dict[str, Any]:
        """Produces a deterministic dictionary representation for hashing and serialization."""
        return {
            "object_id": self.object_id,
            "field_name": self.field_name,
            "evidence_type": self.evidence_type.value,
            "observed_value": self.observed_value,
            "expected_value": self.expected_value,
            "completeness": self.completeness.value,
            "message": self.message,
            "provenance_reference": self.provenance_reference,
            "context_data": dict(sorted(self.context_data.items())),
            "provenance": self.provenance.to_canonical_dict() if self.provenance else None,
        }


# TypedDiagnosticEvidence is an alias for DiagnosticEvidence with Phase 8.5 attributes
TypedDiagnosticEvidence = DiagnosticEvidence
