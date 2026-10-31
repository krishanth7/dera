"""DERA Diagnostics — Unified Diagnostic Models.

Defines the Phase 8.5 unified finding and report contracts unifying severity,
evidence traceability, deterministic recommendations, prioritization, and explainability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from dera.diagnostics.enums import DiagnosticSeverity, RuleCategory
from dera.diagnostics.evidence.models import (
    EvidenceCompleteness,
    FindingConfidence,
    TypedDiagnosticEvidence,
)
from dera.diagnostics.fingerprint import compute_finding_fingerprint
from dera.diagnostics.governance.lifecycle import FindingLifecycleState
from dera.diagnostics.prioritization.classification import FindingClassification
from dera.diagnostics.prioritization.ranking import (
    PriorityRank,
    compute_priority_score,
    derive_priority_rank,
)
from dera.diagnostics.recommendations.generator import StructuredRecommendation
from dera.diagnostics.reports.explainability import ReportExplainabilitySummary

if TYPE_CHECKING:
    from dera.diagnostics.models import (
        DiagnosticCoverage,
        DiagnosticSummaryCounts,
        RuleEvaluation,
    )


@dataclass(frozen=True)
class UnifiedDiagnosticFinding:
    """Unified, evidence-based diagnostic finding contract for Phase 8.5."""

    rule_id: str
    rule_version: str
    object_id: str
    category: RuleCategory
    classification: FindingClassification
    severity: DiagnosticSeverity  # Effective severity
    original_severity: DiagnosticSeverity
    title: str
    description: str
    evidence: tuple[TypedDiagnosticEvidence, ...]
    severity_rationale: str
    confidence: FindingConfidence = FindingConfidence.VERIFIED
    metadata_completeness: EvidenceCompleteness = EvidenceCompleteness.COMPLETE
    structured_recommendation: StructuredRecommendation | None = None
    recommendation: str | None = None
    lifecycle_state: FindingLifecycleState = FindingLifecycleState.OPEN
    is_suppressed: bool = False
    suppression_id: str | None = None
    override_id: str | None = None
    priority_score: int = 0
    priority_rank: PriorityRank = PriorityRank.P5_INFORMATIONAL
    fingerprint: str = ""
    finding_id: str = ""

    def __post_init__(self) -> None:
        if not self.fingerprint:
            computed = compute_finding_fingerprint(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                object_id=self.object_id,
                evidence=self.evidence,
            )
            object.__setattr__(self, "fingerprint", computed)

        if not self.finding_id:
            object.__setattr__(self, "finding_id", f"fnd_{self.fingerprint[:16]}")

        # Set backwards-compatible recommendation text if structured recommendation exists
        if self.structured_recommendation is not None and not self.recommendation:
            object.__setattr__(
                self, "recommendation", self.structured_recommendation.suggested_action
            )

        # Compute priority score and rank if unset
        if self.priority_score == 0:
            score = compute_priority_score(
                severity=self.severity,
                confidence=self.confidence,
                classification=self.classification,
            )
            object.__setattr__(self, "priority_score", score)
            object.__setattr__(self, "priority_rank", derive_priority_rank(self.severity))

    def to_canonical_dict(self) -> dict[str, Any]:
        """Produces a deterministic dictionary representation."""
        return {
            "finding_id": self.finding_id,
            "fingerprint": self.fingerprint,
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "object_id": self.object_id,
            "category": self.category.value,
            "classification": self.classification.value,
            "severity": self.severity.value,
            "original_severity": self.original_severity.value,
            "title": self.title,
            "description": self.description,
            "confidence": self.confidence.value,
            "metadata_completeness": self.metadata_completeness.value,
            "severity_rationale": self.severity_rationale,
            "recommendation": self.recommendation,
            "structured_recommendation": (
                self.structured_recommendation.to_canonical_dict()
                if self.structured_recommendation
                else None
            ),
            "lifecycle_state": self.lifecycle_state.value,
            "is_suppressed": self.is_suppressed,
            "suppression_id": self.suppression_id,
            "override_id": self.override_id,
            "priority_score": self.priority_score,
            "priority_rank": self.priority_rank.value,
            "evidence": [e.to_canonical_dict() for e in self.evidence],
        }


@dataclass(frozen=True)
class UnifiedDiagnosticReport:
    """Complete, immutable, and explainable diagnostic report for Phase 8.5."""

    evaluation_id: str
    evaluated_at: str
    snapshot_id: str | None
    rule_set_version: str
    severity_policy_version: str
    recommendation_catalog_version: str
    config_fingerprint: str
    findings: tuple[UnifiedDiagnosticFinding, ...]
    rule_evaluations: tuple[RuleEvaluation, ...]
    summary: DiagnosticSummaryCounts
    coverage: DiagnosticCoverage
    explainability: ReportExplainabilitySummary
    source_engine: str
    suppressions_applied: tuple[dict[str, Any], ...] = ()
    severity_overrides_applied: tuple[dict[str, Any], ...] = ()
    report_hash: str = ""

    def to_canonical_dict(self) -> dict[str, Any]:
        """Produces a deterministic dictionary representation of the report."""
        return {
            "evaluation_id": self.evaluation_id,
            "evaluated_at": self.evaluated_at,
            "snapshot_id": self.snapshot_id,
            "rule_set_version": self.rule_set_version,
            "severity_policy_version": self.severity_policy_version,
            "recommendation_catalog_version": self.recommendation_catalog_version,
            "config_fingerprint": self.config_fingerprint,
            "report_hash": self.report_hash,
            "source_engine": self.source_engine,
            "summary": self.summary.to_canonical_dict(),
            "coverage": self.coverage.to_canonical_dict(),
            "explainability": self.explainability.to_canonical_dict(),
            "suppressions_applied": list(self.suppressions_applied),
            "severity_overrides_applied": list(self.severity_overrides_applied),
            "findings": [f.to_canonical_dict() for f in self.findings],
            "rule_evaluations": [e.to_canonical_dict() for e in self.rule_evaluations],
        }
