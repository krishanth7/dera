"""DERA Migration — Phase 9.2 Migration Risk Report Models.

Defines the complete, immutable migration risk analysis report contract.
"""

from __future__ import annotations

import hashlib
from typing import Any
from collections import Counter
from pydantic import BaseModel, ConfigDict, Field

from dera.comparison.serializers import dumps_canonical_bytes
from dera.migration.classification.models import ClassifiedChange
from dera.migration.impact.blast_radius import BlastRadiusMetrics
from dera.migration.recommendations.models import EngineeringRecommendation
from dera.migration.risk.models import MigrationRiskAssessment

MIGRATION_REPORT_DOMAIN = "DERA:MIGRATION:REPORT:V1\n"
MIGRATION_POLICY_VERSION = "dera.migration.risk.v1"


class MigrationRiskSummary(BaseModel):
    """Aggregated metrics across classified changes and risk assessments."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_changes: int = Field(default=0, description="Total count of analyzed schema changes.")
    additive_changes: int = Field(default=0, description="Count of additive structural changes.")
    removals: int = Field(default=0, description="Count of structural removals.")
    modifications: int = Field(default=0, description="Count of structural modifications.")
    potentially_breaking: int = Field(default=0, description="Count of changes rated breaking or potentially breaking.")
    requires_review: int = Field(default=0, description="Count of changes requiring manual engineering review.")
    total_risks: int = Field(default=0, description="Total count of generated risk assessments.")
    risks_by_severity: dict[str, int] = Field(default_factory=dict, description="Risks by DiagnosticSeverity.")
    risks_by_priority: dict[str, int] = Field(default_factory=dict, description="Risks by ReviewPriority.")
    risks_by_dimension: dict[str, int] = Field(default_factory=dict, description="Risks by RiskDimension.")


class MigrationRiskReport(BaseModel):
    """Immutable, evidence-backed migration risk analysis report."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    report_id: str = Field(description="Deterministic report identifier (e.g. 'mrk_...').")
    policy_version: str = Field(default=MIGRATION_POLICY_VERSION, description="Policy version.")
    baseline_snapshot_id: str = Field(description="Baseline snapshot ID.")
    baseline_fingerprint: str = Field(description="Baseline snapshot structural fingerprint.")
    target_snapshot_id: str = Field(description="Target snapshot ID.")
    target_fingerprint: str = Field(description="Target snapshot structural fingerprint.")
    comparison_report_id: str = Field(description="ID of source ComparisonReport.")
    comparison_fingerprint: str = Field(description="Report fingerprint of source ComparisonReport.")
    engine: str = Field(description="Source database engine.")
    summary: MigrationRiskSummary = Field(description="Aggregated risk metrics.")
    classified_changes: tuple[ClassifiedChange, ...] = Field(
        default_factory=tuple,
        description="Classified schema change records.",
    )
    risk_assessments: tuple[MigrationRiskAssessment, ...] = Field(
        default_factory=tuple,
        description="Priority-ordered risk assessments.",
    )
    blast_radius_reports: tuple[BlastRadiusMetrics, ...] = Field(
        default_factory=tuple,
        description="Dependency blast-radius metrics for affected tables.",
    )
    recommendations: tuple[EngineeringRecommendation, ...] = Field(
        default_factory=tuple,
        description="Consolidated list of advisory recommendations.",
    )
    limitations: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Documented metadata limitations.",
    )
    report_fingerprint: str = Field(default="", description="Stable SHA-256 fingerprint over report content.")

    @classmethod
    def create(
        cls,
        baseline_snapshot_id: str,
        baseline_fingerprint: str,
        target_snapshot_id: str,
        target_fingerprint: str,
        comparison_report_id: str,
        comparison_fingerprint: str,
        engine: str,
        classified_changes: tuple[ClassifiedChange, ...],
        risk_assessments: tuple[MigrationRiskAssessment, ...],
        blast_radius_reports: tuple[BlastRadiusMetrics, ...] = (),
        recommendations: tuple[EngineeringRecommendation, ...] = (),
        limitations: tuple[str, ...] = (),
        policy_version: str = MIGRATION_POLICY_VERSION,
    ) -> MigrationRiskReport:
        """Construct MigrationRiskReport with deterministic summary and report fingerprint."""
        # Calculate summary metrics
        total_chg = len(classified_changes)
        additive = sum(1 for c in classified_changes if c.category.value == "ADDITIVE")
        removals = sum(1 for c in classified_changes if c.category.value == "REMOVAL")
        mods = total_chg - (additive + removals)
        breaking = sum(1 for c in classified_changes if c.is_potentially_breaking)
        review = sum(1 for c in classified_changes if c.compatibility.value == "REQUIRES_REVIEW")

        sev_counter: Counter[str] = Counter()
        pri_counter: Counter[str] = Counter()
        dim_counter: Counter[str] = Counter()

        for r in risk_assessments:
            sev_counter[r.severity.value] += 1
            pri_counter[r.priority.value] += 1
            dim_counter[r.dimension.value] += 1

        summary = MigrationRiskSummary(
            total_changes=total_chg,
            additive_changes=additive,
            removals=removals,
            modifications=mods,
            potentially_breaking=breaking,
            requires_review=review,
            total_risks=len(risk_assessments),
            risks_by_severity=dict(sorted(sev_counter.items())),
            risks_by_priority=dict(sorted(pri_counter.items())),
            risks_by_dimension=dict(sorted(dim_counter.items())),
        )

        # Compute report fingerprint
        risk_fps = sorted(r.fingerprint for r in risk_assessments)
        payload = {
            "policy_version": policy_version,
            "comparison_fingerprint": comparison_fingerprint,
            "baseline_fingerprint": baseline_fingerprint,
            "target_fingerprint": target_fingerprint,
            "risk_fingerprints": risk_fps,
            "summary": summary.model_dump(mode="json"),
        }
        canonical_bytes = dumps_canonical_bytes(payload)
        hasher = hashlib.sha256()
        hasher.update(MIGRATION_REPORT_DOMAIN.encode("utf-8"))
        hasher.update(canonical_bytes)
        rpt_fp = hasher.hexdigest().lower()
        report_id = f"mrk_{rpt_fp[:16]}"

        return cls(
            report_id=report_id,
            policy_version=policy_version,
            baseline_snapshot_id=baseline_snapshot_id,
            baseline_fingerprint=baseline_fingerprint,
            target_snapshot_id=target_snapshot_id,
            target_fingerprint=target_fingerprint,
            comparison_report_id=comparison_report_id,
            comparison_fingerprint=comparison_fingerprint,
            engine=engine,
            summary=summary,
            classified_changes=classified_changes,
            risk_assessments=risk_assessments,
            blast_radius_reports=blast_radius_reports,
            recommendations=recommendations,
            limitations=limitations,
            report_fingerprint=rpt_fp,
        )
