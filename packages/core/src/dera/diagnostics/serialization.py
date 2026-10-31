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
)
from dera.diagnostics.evidence import DiagnosticEvidence
from dera.diagnostics.models import (
    DiagnosticCoverage,
    DiagnosticFinding,
    DiagnosticReport,
    DiagnosticSummaryCounts,
    RuleEvaluation,
)


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
            evidence_list.append(
                DiagnosticEvidence(
                    object_id=ev_data["object_id"],
                    field_name=ev_data["field_name"],
                    observed_value=ev_data["observed_value"],
                    expected_value=ev_data.get("expected_value"),
                    message=ev_data.get("message", ""),
                    provenance_reference=ev_data.get("provenance_reference"),
                    context_data=ev_data.get("context_data", {}),
                )
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
    )
