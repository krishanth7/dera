"""DERA Diagnostics — Canonical Serialization.

Produces deterministic JSON representations of diagnostic findings, evaluations,
and complete reports, ensuring byte-level stability across platforms.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from dera.diagnostics.enums import (
    DiagnosticSeverity,
    EvaluationStatus,
    RuleCategory,
)
from dera.diagnostics.evidence import DiagnosticEvidence
from dera.diagnostics.evidence.models import (
    EvidenceCompleteness,
    EvidenceType,
    FindingConfidence,
)
from dera.diagnostics.governance.lifecycle import FindingLifecycleState
from dera.diagnostics.models import (
    DiagnosticCoverage,
    DiagnosticFinding,
    DiagnosticReport,
    DiagnosticSummaryCounts,
    RuleEvaluation,
)
from dera.diagnostics.prioritization.classification import FindingClassification
from dera.diagnostics.prioritization.ranking import PriorityRank
from dera.diagnostics.reports.explainability import ReportExplainabilitySummary


def _canonical_json_dump(data: Any) -> str:
    """Serializes data using deterministic JSON formatting."""
    return json.dumps(
        data,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    )


def compute_report_content_hash(report_dict: dict[str, Any]) -> str:
    """Computes a SHA-256 hash across the deterministic content of a report.

    Excludes volatile fields (evaluation_id, evaluated_at, report_hash itself)
    to verify structural equivalence across repeated runs.
    """
    # Normalize rule evaluations without volatile runtime durations
    stable_evaluations = [
        {
            "rule_id": ev.get("rule_id"),
            "rule_version": ev.get("rule_version"),
            "status": ev.get("status"),
            "message": ev.get("message"),
            "error_details": ev.get("error_details"),
        }
        for ev in report_dict.get("rule_evaluations", [])
    ]

    stable_content = {
        "snapshot_id": report_dict.get("snapshot_id"),
        "rule_set_version": report_dict.get("rule_set_version"),
        "severity_policy_version": report_dict.get("severity_policy_version", "1.0.0"),
        "recommendation_catalog_version": report_dict.get(
            "recommendation_catalog_version", "1.0.0"
        ),
        "config_fingerprint": report_dict.get("config_fingerprint"),
        "source_engine": report_dict.get("source_engine"),
        "summary": report_dict.get("summary"),
        "coverage": report_dict.get("coverage"),
        "findings": report_dict.get("findings"),
        "rule_evaluations": stable_evaluations,
    }
    return hashlib.sha256(_canonical_json_dump(stable_content).encode("utf-8")).hexdigest()


def serialize_diagnostic_report(report: DiagnosticReport) -> str:
    """Serializes a DiagnosticReport to a deterministic JSON string."""
    report_dict = report.to_canonical_dict()
    if not report.report_hash:
        report_dict["report_hash"] = compute_report_content_hash(report_dict)
    return _canonical_json_dump(report_dict)


def deserialize_diagnostic_report(json_str: str) -> DiagnosticReport:
    """Deserializes a JSON string into a structured DiagnosticReport instance."""
    data = json.loads(json_str)

    findings: list[DiagnosticFinding] = []
    for f_data in data.get("findings", []):
        evidence_list: list[DiagnosticEvidence] = []
        for ev_data in f_data.get("evidence", []):
            prov_data = ev_data.get("provenance")
            provenance = None
            if prov_data:
                from dera.diagnostics.evidence.models import EvidenceProvenance

                provenance = EvidenceProvenance(
                    source_engine=prov_data.get("source_engine", ""),
                    connector_version=prov_data.get("connector_version", "1.0.0"),
                    inspection_timestamp=prov_data.get("inspection_timestamp", ""),
                    snapshot_id=prov_data.get("snapshot_id"),
                    canonical_object_id=prov_data.get("canonical_object_id", ""),
                    capability_state=prov_data.get("capability_state"),
                )

            ev_type_val = ev_data.get(
                "evidence_type", EvidenceType.CANONICAL_OBJECT_REFERENCE.value
            )
            ev_comp_val = ev_data.get("completeness", EvidenceCompleteness.COMPLETE.value)

            evidence_list.append(
                DiagnosticEvidence(
                    object_id=ev_data["object_id"],
                    field_name=ev_data["field_name"],
                    observed_value=ev_data["observed_value"],
                    expected_value=ev_data.get("expected_value"),
                    message=ev_data.get("message", ""),
                    provenance_reference=ev_data.get("provenance_reference"),
                    context_data=ev_data.get("context_data", {}),
                    evidence_type=(
                        EvidenceType(ev_type_val)
                        if ev_type_val in EvidenceType._value2member_map_
                        else EvidenceType.CANONICAL_OBJECT_REFERENCE
                    ),
                    completeness=(
                        EvidenceCompleteness(ev_comp_val)
                        if ev_comp_val in EvidenceCompleteness._value2member_map_
                        else EvidenceCompleteness.COMPLETE
                    ),
                    provenance=provenance,
                )
            )

        cat_val = f_data.get("category", RuleCategory.STRUCTURAL_INTEGRITY.value)
        cls_val = f_data.get(
            "classification", FindingClassification.POTENTIAL_ENGINEERING_CONCERN.value
        )
        conf_val = f_data.get("confidence", FindingConfidence.VERIFIED.value)
        comp_val = f_data.get("metadata_completeness", EvidenceCompleteness.COMPLETE.value)
        lc_val = f_data.get("lifecycle_state", FindingLifecycleState.OPEN.value)
        pr_val = f_data.get("priority_rank", PriorityRank.P5_INFORMATIONAL.value)

        orig_sev = f_data.get("original_severity")
        original_severity = (
            DiagnosticSeverity(orig_sev) if orig_sev else DiagnosticSeverity(f_data["severity"])
        )

        rec_data = f_data.get("structured_recommendation")
        structured_rec = None
        if rec_data:
            from dera.diagnostics.recommendations.generator import StructuredRecommendation

            structured_rec = StructuredRecommendation(
                recommendation_id=rec_data.get("recommendation_id", ""),
                rule_id=rec_data.get("rule_id", f_data["rule_id"]),
                title=rec_data.get("title", ""),
                description=rec_data.get("description", ""),
                suggested_action=rec_data.get("suggested_action", ""),
                risk_considerations=rec_data.get("risk_considerations", ""),
                verification_steps=tuple(rec_data.get("verification_steps", ())),
                limitations=rec_data.get("limitations", ""),
                version=rec_data.get("version", "1.0.0"),
                is_advisory=rec_data.get("is_advisory", True),
            )

        findings.append(
            DiagnosticFinding(
                rule_id=f_data["rule_id"],
                rule_version=f_data["rule_version"],
                object_id=f_data["object_id"],
                severity=DiagnosticSeverity(f_data["severity"]),
                title=f_data["title"],
                description=f_data["description"],
                evidence=tuple(evidence_list),
                severity_rationale=f_data.get("severity_rationale", ""),
                recommendation=f_data.get("recommendation"),
                fingerprint=f_data.get("fingerprint", ""),
                category=(
                    RuleCategory(cat_val)
                    if cat_val in RuleCategory._value2member_map_
                    else RuleCategory.STRUCTURAL_INTEGRITY
                ),
                classification=(
                    FindingClassification(cls_val)
                    if cls_val in FindingClassification._value2member_map_
                    else FindingClassification.POTENTIAL_ENGINEERING_CONCERN
                ),
                original_severity=original_severity,
                confidence=(
                    FindingConfidence(conf_val)
                    if conf_val in FindingConfidence._value2member_map_
                    else FindingConfidence.VERIFIED
                ),
                metadata_completeness=(
                    EvidenceCompleteness(comp_val)
                    if comp_val in EvidenceCompleteness._value2member_map_
                    else EvidenceCompleteness.COMPLETE
                ),
                structured_recommendation=structured_rec,
                lifecycle_state=(
                    FindingLifecycleState(lc_val)
                    if lc_val in FindingLifecycleState._value2member_map_
                    else FindingLifecycleState.OPEN
                ),
                is_suppressed=f_data.get("is_suppressed", False),
                suppression_id=f_data.get("suppression_id"),
                override_id=f_data.get("override_id"),
                priority_score=f_data.get("priority_score", 0),
                priority_rank=(
                    PriorityRank(pr_val)
                    if pr_val in PriorityRank._value2member_map_
                    else PriorityRank.P5_INFORMATIONAL
                ),
                finding_id=f_data.get("finding_id", ""),
            )
        )

    evaluations: list[RuleEvaluation] = []
    for ev in data.get("rule_evaluations", []):
        evaluations.append(
            RuleEvaluation(
                rule_id=ev["rule_id"],
                rule_version=ev["rule_version"],
                status=EvaluationStatus(ev["status"]),
                findings=tuple([f for f in findings if f.rule_id == ev["rule_id"]]),
                execution_duration_ms=float(ev.get("execution_duration_ms", 0.0)),
                message=ev.get("message", ""),
                error_details=ev.get("error_details"),
            )
        )

    summary_data = data.get("summary", {})
    summary = DiagnosticSummaryCounts(
        total_rules_evaluated=summary_data.get("total_rules_evaluated", 0),
        rules_passed=summary_data.get("rules_passed", 0),
        rules_with_findings=summary_data.get("rules_with_findings", 0),
        rules_skipped=summary_data.get("rules_skipped", 0),
        rules_unsupported=summary_data.get("rules_unsupported", 0),
        rules_insufficient_metadata=summary_data.get("rules_insufficient_metadata", 0),
        rules_errored=summary_data.get("rules_errored", 0),
        total_findings=summary_data.get("total_findings", 0),
        findings_by_severity=summary_data.get("findings_by_severity", {}),
    )

    cov_data = data.get("coverage", {})
    coverage = DiagnosticCoverage(
        evaluated_rules=tuple(cov_data.get("evaluated_rules", ())),
        skipped_rules=tuple(cov_data.get("skipped_rules", ())),
        unsupported_rules=tuple(cov_data.get("unsupported_rules", ())),
        insufficient_metadata_rules=tuple(cov_data.get("insufficient_metadata_rules", ())),
        errored_rules=tuple(cov_data.get("errored_rules", ())),
    )

    expl_data = data.get("explainability")
    explainability = None
    if expl_data:
        explainability = ReportExplainabilitySummary(
            total_rules_considered=expl_data.get("total_rules_considered", 0),
            evaluated_rules_count=expl_data.get("evaluated_rules_count", 0),
            skipped_rules_count=expl_data.get("skipped_rules_count", 0),
            unsupported_rules_count=expl_data.get("unsupported_rules_count", 0),
            insufficient_metadata_count=expl_data.get("insufficient_metadata_count", 0),
            errored_rules_count=expl_data.get("errored_rules_count", 0),
            findings_by_severity=expl_data.get("findings_by_severity", {}),
            findings_by_classification=expl_data.get("findings_by_classification", {}),
            findings_by_lifecycle=expl_data.get("findings_by_lifecycle", {}),
            findings_by_confidence=expl_data.get("findings_by_confidence", {}),
            active_suppression_count=expl_data.get("active_suppression_count", 0),
            severity_override_count=expl_data.get("severity_override_count", 0),
            rule_set_version=expl_data.get("rule_set_version", "1.0.0"),
            severity_policy_version=expl_data.get("severity_policy_version", "1.0.0"),
            recommendation_catalog_version=expl_data.get("recommendation_catalog_version", "1.0.0"),
            config_fingerprint=expl_data.get("config_fingerprint", ""),
            skipped_reasons=expl_data.get("skipped_reasons", {}),
            unsupported_reasons=expl_data.get("unsupported_reasons", {}),
        )

    return DiagnosticReport(
        evaluation_id=data["evaluation_id"],
        evaluated_at=data["evaluated_at"],
        snapshot_id=data.get("snapshot_id"),
        rule_set_version=data.get("rule_set_version", "1.0.0"),
        config_fingerprint=data.get("config_fingerprint", ""),
        findings=tuple(findings),
        rule_evaluations=tuple(evaluations),
        summary=summary,
        coverage=coverage,
        source_engine=data.get("source_engine", "unknown"),
        report_hash=data.get("report_hash", ""),
        explainability=explainability,
        severity_policy_version=data.get("severity_policy_version", "1.0.0"),
        recommendation_catalog_version=data.get("recommendation_catalog_version", "1.0.0"),
        suppressions_applied=tuple(data.get("suppressions_applied", ())),
        severity_overrides_applied=tuple(data.get("severity_overrides_applied", ())),
    )
