"""DERA Migration — Phase 9.2 Risk Assessment Domain Models.

Defines verifiable migration risk assessments, evidence structures,
and prioritization assignments.
"""

from __future__ import annotations

import hashlib
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from dera.comparison.serializers import dumps_canonical_bytes
from dera.diagnostics.enums import DiagnosticSeverity
from dera.migration.enums import (
    ReversibilityClassification,
    ReviewPriority,
    RiskDimension,
    RiskEvidenceCertainty,
)
from dera.migration.recommendations.models import EngineeringRecommendation

RISK_FINGERPRINT_DOMAIN = "DERA:MIGRATION:RISK:V1\n"


class MigrationRiskAssessment(BaseModel):
    """Detailed evidence-backed migration risk evaluation for a schema change."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    risk_id: str = Field(description="Deterministic risk identifier (e.g. 'rsk_...').")
    source_change_id: str = Field(description="Source change ID.")
    source_change_fingerprint: str = Field(description="Fingerprint of the source change.")
    rule_id: str = Field(description="Identifier of the risk evaluation rule.")
    dimension: RiskDimension = Field(description="Risk evaluation dimension.")
    severity: DiagnosticSeverity = Field(description="Assigned diagnostic severity.")
    priority: ReviewPriority = Field(description="Engineering review priority (P1 to P5).")
    certainty: RiskEvidenceCertainty = Field(description="Evidence certainty level.")
    reversibility: ReversibilityClassification = Field(description="Reversibility classification.")
    title: str = Field(description="Brief summary title of the risk.")
    description: str = Field(description="In-depth explanation of potential migration impact.")
    evidence_summary: dict[str, Any] = Field(
        default_factory=dict,
        description="Verifiable structural properties supporting the risk.",
    )
    assumptions: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Explicit assumptions made in the evaluation.",
    )
    limitations: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Limitations of schema metadata in assessing this risk.",
    )
    recommendations: tuple[EngineeringRecommendation, ...] = Field(
        default_factory=tuple,
        description="Deterministic advisory engineering recommendations.",
    )
    fingerprint: str = Field(default="", description="Stable SHA-256 fingerprint for this risk.")

    @classmethod
    def create(
        cls,
        source_change_id: str,
        source_change_fingerprint: str,
        rule_id: str,
        dimension: RiskDimension,
        severity: DiagnosticSeverity,
        priority: ReviewPriority,
        certainty: RiskEvidenceCertainty,
        reversibility: ReversibilityClassification,
        title: str,
        description: str,
        evidence_summary: dict[str, Any],
        assumptions: tuple[str, ...] = (),
        limitations: tuple[str, ...] = (),
        recommendations: tuple[EngineeringRecommendation, ...] = (),
        policy_version: str = "dera.migration.risk.v1",
    ) -> MigrationRiskAssessment:
        """Construct risk assessment with deterministic SHA-256 fingerprint."""
        payload = {
            "source_change_fingerprint": source_change_fingerprint,
            "rule_id": rule_id,
            "dimension": dimension.value,
            "severity": severity.value,
            "priority": priority.value,
            "certainty": certainty.value,
            "reversibility": reversibility.value,
            "evidence_summary": evidence_summary,
            "policy_version": policy_version,
        }
        canonical_bytes = dumps_canonical_bytes(payload)
        hasher = hashlib.sha256()
        hasher.update(RISK_FINGERPRINT_DOMAIN.encode("utf-8"))
        hasher.update(canonical_bytes)
        fp = hasher.hexdigest().lower()
        risk_id = f"rsk_{fp[:16]}"

        return cls(
            risk_id=risk_id,
            source_change_id=source_change_id,
            source_change_fingerprint=source_change_fingerprint,
            rule_id=rule_id,
            dimension=dimension,
            severity=severity,
            priority=priority,
            certainty=certainty,
            reversibility=reversibility,
            title=title,
            description=description,
            evidence_summary=evidence_summary,
            assumptions=assumptions,
            limitations=limitations,
            recommendations=recommendations,
            fingerprint=fp,
        )
