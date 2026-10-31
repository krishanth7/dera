"""DERA Diagnostics — Prioritization Ranking Engine.

Calculates explainable, deterministic priority ranks and scores combining
effective severity, evidence confidence, finding classification, and object identity.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from dera.diagnostics.enums import DiagnosticSeverity
from dera.diagnostics.evidence.models import FindingConfidence
from dera.diagnostics.prioritization.classification import FindingClassification

if TYPE_CHECKING:
    pass


class PriorityRank(StrEnum):
    """Categorical priority rank indicating operational urgency."""

    P1_CRITICAL = "P1_CRITICAL"
    P2_HIGH = "P2_HIGH"
    P3_MEDIUM = "P3_MEDIUM"
    P4_LOW = "P4_LOW"
    P5_INFORMATIONAL = "P5_INFORMATIONAL"

    @property
    def rank_order(self) -> int:
        """Ordering rank where 1 is highest priority."""
        orders = {
            PriorityRank.P1_CRITICAL: 1,
            PriorityRank.P2_HIGH: 2,
            PriorityRank.P3_MEDIUM: 3,
            PriorityRank.P4_LOW: 4,
            PriorityRank.P5_INFORMATIONAL: 5,
        }
        return orders[self]


def compute_priority_score(
    severity: DiagnosticSeverity,
    confidence: FindingConfidence,
    classification: FindingClassification,
) -> int:
    """Calculates an explainable, deterministic priority score.

    Formula:
        Score = (Severity.rank * 1000) + (Confidence.rank * 100) + Classification.priority_weight

    Component ranges:
      - Severity.rank: 1 to 5 (Weight: 1,000 to 5,000)
      - Confidence.rank: 1 to 4 (Weight: 100 to 400)
      - Classification.priority_weight: 10 to 100

    This guarantees strict severity stratification: higher severity findings always
    outrank lower severity findings, with ties broken by verified evidence confidence,
    followed by classification criticality.
    """
    return (severity.rank * 1000) + (confidence.rank * 100) + classification.priority_weight


def derive_priority_rank(severity: DiagnosticSeverity) -> PriorityRank:
    """Derives standard PriorityRank directly from effective severity."""
    mapping = {
        DiagnosticSeverity.CRITICAL: PriorityRank.P1_CRITICAL,
        DiagnosticSeverity.HIGH: PriorityRank.P2_HIGH,
        DiagnosticSeverity.MEDIUM: PriorityRank.P3_MEDIUM,
        DiagnosticSeverity.LOW: PriorityRank.P4_LOW,
        DiagnosticSeverity.INFORMATIONAL: PriorityRank.P5_INFORMATIONAL,
    }
    return mapping.get(severity, PriorityRank.P5_INFORMATIONAL)
