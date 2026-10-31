"""DERA Diagnostics — Report Explainability Engine.

Synthesizes comprehensive, explainable coverage and outcome metrics for diagnostic
reports, detailing evaluated vs skipped rules, policy versions, and suppression impact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from dera.diagnostics.models import EvaluationStatus

if TYPE_CHECKING:
    from dera.diagnostics.models import DiagnosticCoverage, DiagnosticSummaryCounts, RuleEvaluation
    from dera.diagnostics.reports.unified_models import UnifiedDiagnosticFinding


@dataclass(frozen=True)
class ReportExplainabilitySummary:
    """Detailed explainability metadata for a diagnostic evaluation report."""

    total_rules_considered: int
    evaluated_rules_count: int
    skipped_rules_count: int
    unsupported_rules_count: int
    insufficient_metadata_count: int
    errored_rules_count: int
    findings_by_severity: dict[str, int]
    findings_by_classification: dict[str, int]
    findings_by_lifecycle: dict[str, int]
    findings_by_confidence: dict[str, int]
    active_suppression_count: int
    severity_override_count: int
    rule_set_version: str
    severity_policy_version: str
    recommendation_catalog_version: str
    config_fingerprint: str
    skipped_reasons: dict[str, str] = field(default_factory=dict)
    unsupported_reasons: dict[str, str] = field(default_factory=dict)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "total_rules_considered": self.total_rules_considered,
            "evaluated_rules_count": self.evaluated_rules_count,
            "skipped_rules_count": self.skipped_rules_count,
            "unsupported_rules_count": self.unsupported_rules_count,
            "insufficient_metadata_count": self.insufficient_metadata_count,
            "errored_rules_count": self.errored_rules_count,
            "findings_by_severity": dict(sorted(self.findings_by_severity.items())),
            "findings_by_classification": dict(sorted(self.findings_by_classification.items())),
            "findings_by_lifecycle": dict(sorted(self.findings_by_lifecycle.items())),
            "findings_by_confidence": dict(sorted(self.findings_by_confidence.items())),
            "active_suppression_count": self.active_suppression_count,
            "severity_override_count": self.severity_override_count,
            "rule_set_version": self.rule_set_version,
            "severity_policy_version": self.severity_policy_version,
            "recommendation_catalog_version": self.recommendation_catalog_version,
            "config_fingerprint": self.config_fingerprint,
            "skipped_reasons": dict(sorted(self.skipped_reasons.items())),
            "unsupported_reasons": dict(sorted(self.unsupported_reasons.items())),
        }


def build_report_explainability(
    summary: DiagnosticSummaryCounts,
    coverage: DiagnosticCoverage,
    evaluations: tuple[RuleEvaluation, ...] | list[RuleEvaluation],
    findings: tuple[UnifiedDiagnosticFinding, ...] | list[UnifiedDiagnosticFinding],
    rule_set_version: str,
    severity_policy_version: str,
    recommendation_catalog_version: str,
    config_fingerprint: str,
) -> ReportExplainabilitySummary:
    """Builds a deterministic ReportExplainabilitySummary from report components."""
    skipped_reasons: dict[str, str] = {}
    unsupported_reasons: dict[str, str] = {}

    for ev in evaluations:
        if ev.status == EvaluationStatus.NOT_APPLICABLE and ev.message:
            skipped_reasons[ev.rule_id] = ev.message
        elif ev.status == EvaluationStatus.UNSUPPORTED and ev.message:
            unsupported_reasons[ev.rule_id] = ev.message

    by_classification: dict[str, int] = {}
    by_lifecycle: dict[str, int] = {}
    by_confidence: dict[str, int] = {}
    suppression_count = 0
    override_count = 0

    for f in findings:
        cls_key = f.classification.value
        by_classification[cls_key] = by_classification.get(cls_key, 0) + 1

        lc_key = f.lifecycle_state.value
        by_lifecycle[lc_key] = by_lifecycle.get(lc_key, 0) + 1

        conf_key = f.confidence.value
        by_confidence[conf_key] = by_confidence.get(conf_key, 0) + 1

        if f.is_suppressed:
            suppression_count += 1
        if f.override_id:
            override_count += 1

    total_considered = len(evaluations)

    return ReportExplainabilitySummary(
        total_rules_considered=total_considered,
        evaluated_rules_count=summary.total_rules_evaluated,
        skipped_rules_count=summary.rules_skipped,
        unsupported_rules_count=summary.rules_unsupported,
        insufficient_metadata_count=summary.rules_insufficient_metadata,
        errored_rules_count=summary.rules_errored,
        findings_by_severity=summary.findings_by_severity,
        findings_by_classification=by_classification,
        findings_by_lifecycle=by_lifecycle,
        findings_by_confidence=by_confidence,
        active_suppression_count=suppression_count,
        severity_override_count=override_count,
        rule_set_version=rule_set_version,
        severity_policy_version=severity_policy_version,
        recommendation_catalog_version=recommendation_catalog_version,
        config_fingerprint=config_fingerprint,
        skipped_reasons=skipped_reasons,
        unsupported_reasons=unsupported_reasons,
    )
