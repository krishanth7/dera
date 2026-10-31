"""DERA Diagnostics — Typed Diagnostic Models.

Provides domain models for rule metadata, diagnostic findings, rule outcomes,
summary coverage, and immutable diagnostic reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dera.diagnostics.enums import (
    DiagnosticSeverity,
    EvaluationStatus,
    RuleCategory,
)
from dera.diagnostics.evidence import DiagnosticEvidence
from dera.diagnostics.fingerprint import compute_finding_fingerprint


@dataclass(frozen=True)
class RuleMetadata:
    """Explicit, versioned metadata declared by every diagnostic rule."""

    rule_id: str
    title: str
    description: str
    version: str
    category: RuleCategory
    default_severity: DiagnosticSeverity
    supported_object_kinds: tuple[str, ...]
    required_capabilities: tuple[str, ...] = ()
    supported_engines: tuple[str, ...] = ()  # Empty means all supported database engines
    applicability_summary: str = ""
    evidence_requirements: str = ""
    recommendation_template: str = ""
    documentation_url: str = ""

    def __post_init__(self) -> None:
        if not self.rule_id:
            raise ValueError("RuleMetadata must specify a non-empty rule_id.")
        if not self.title:
            raise ValueError(f"RuleMetadata for '{self.rule_id}' must specify a title.")
        if not self.version:
            raise ValueError(f"RuleMetadata for '{self.rule_id}' must specify a version.")


@dataclass(frozen=True)
class DiagnosticFinding:
    """Represents a structured, evidence-based diagnostic finding."""

    rule_id: str
    rule_version: str
    object_id: str
    severity: DiagnosticSeverity
    title: str
    description: str
    evidence: tuple[DiagnosticEvidence, ...]
    severity_rationale: str
    recommendation: str | None = None
    fingerprint: str = ""

    def __post_init__(self) -> None:
        if not self.fingerprint:
            computed = compute_finding_fingerprint(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                object_id=self.object_id,
                evidence=self.evidence,
            )
            object.__setattr__(self, "fingerprint", computed)

    def to_canonical_dict(self) -> dict[str, Any]:
        """Produces a deterministic dictionary representation."""
        return {
            "fingerprint": self.fingerprint,
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "object_id": self.object_id,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "evidence": [e.to_canonical_dict() for e in self.evidence],
            "severity_rationale": self.severity_rationale,
            "recommendation": self.recommendation,
        }


@dataclass(frozen=True)
class RuleEvaluation:
    """Execution result produced by evaluating a single diagnostic rule."""

    rule_id: str
    rule_version: str
    status: EvaluationStatus
    findings: tuple[DiagnosticFinding, ...] = ()
    execution_duration_ms: float = 0.0
    message: str = ""
    error_details: str | None = None

    def to_canonical_dict(self) -> dict[str, Any]:
        """Produces a deterministic dictionary representation."""
        return {
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "status": self.status.value,
            "findings": [f.to_canonical_dict() for f in self.findings],
            "execution_duration_ms": round(self.execution_duration_ms, 3),
            "message": self.message,
            "error_details": self.error_details,
        }


@dataclass(frozen=True)
class DiagnosticSummaryCounts:
    """Aggregated outcome metrics across an entire diagnostic evaluation."""

    total_rules_evaluated: int
    rules_passed: int
    rules_with_findings: int
    rules_skipped: int
    rules_unsupported: int
    rules_insufficient_metadata: int
    rules_errored: int
    total_findings: int
    findings_by_severity: dict[str, int] = field(default_factory=dict)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "total_rules_evaluated": self.total_rules_evaluated,
            "rules_passed": self.rules_passed,
            "rules_with_findings": self.rules_with_findings,
            "rules_skipped": self.rules_skipped,
            "rules_unsupported": self.rules_unsupported,
            "rules_insufficient_metadata": self.rules_insufficient_metadata,
            "rules_errored": self.rules_errored,
            "total_findings": self.total_findings,
            "findings_by_severity": dict(sorted(self.findings_by_severity.items())),
        }


@dataclass(frozen=True)
class DiagnosticCoverage:
    """Coverage report categorizing all considered rules by execution status."""

    evaluated_rules: tuple[str, ...] = ()
    skipped_rules: tuple[str, ...] = ()
    unsupported_rules: tuple[str, ...] = ()
    insufficient_metadata_rules: tuple[str, ...] = ()
    errored_rules: tuple[str, ...] = ()

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "evaluated_rules": list(self.evaluated_rules),
            "skipped_rules": list(self.skipped_rules),
            "unsupported_rules": list(self.unsupported_rules),
            "insufficient_metadata_rules": list(self.insufficient_metadata_rules),
            "errored_rules": list(self.errored_rules),
        }


@dataclass(frozen=True)
class DiagnosticReport:
    """Complete, immutable diagnostic report generated from schema evaluation."""

    evaluation_id: str
    evaluated_at: str
    snapshot_id: str | None
    rule_set_version: str
    config_fingerprint: str
    findings: tuple[DiagnosticFinding, ...]
    rule_evaluations: tuple[RuleEvaluation, ...]
    summary: DiagnosticSummaryCounts
    coverage: DiagnosticCoverage
    source_engine: str
    report_hash: str = ""

    def to_canonical_dict(self) -> dict[str, Any]:
        """Produces a deterministic dictionary representation of the report."""
        return {
            "evaluation_id": self.evaluation_id,
            "evaluated_at": self.evaluated_at,
            "snapshot_id": self.snapshot_id,
            "rule_set_version": self.rule_set_version,
            "config_fingerprint": self.config_fingerprint,
            "report_hash": self.report_hash,
            "source_engine": self.source_engine,
            "summary": self.summary.to_canonical_dict(),
            "coverage": self.coverage.to_canonical_dict(),
            "findings": [f.to_canonical_dict() for f in self.findings],
            "rule_evaluations": [e.to_canonical_dict() for e in self.rule_evaluations],
        }
