"""DERA Diagnostics — Evidence Package.

Exposes typed evidence models, validation, provenance tracking, and traceability.
"""

from __future__ import annotations

from dera.diagnostics.evidence.models import (
    DiagnosticEvidence,
    EvidenceCompleteness,
    EvidenceProvenance,
    EvidenceType,
    FindingConfidence,
    TypedDiagnosticEvidence,
    sanitize_value,
)
from dera.diagnostics.evidence.provenance import create_evidence_provenance
from dera.diagnostics.evidence.traceability import build_evidence_traceability_matrix
from dera.diagnostics.evidence.validator import (
    EvidenceValidationResult,
    validate_and_enrich_evidence,
)

__all__ = [
    "DiagnosticEvidence",
    "EvidenceCompleteness",
    "EvidenceProvenance",
    "EvidenceType",
    "EvidenceValidationResult",
    "FindingConfidence",
    "TypedDiagnosticEvidence",
    "build_evidence_traceability_matrix",
    "create_evidence_provenance",
    "sanitize_value",
    "validate_and_enrich_evidence",
]
