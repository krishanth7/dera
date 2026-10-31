"""Tests for DERA diagnostic domain models, metadata, evidence, and report structures."""

from __future__ import annotations

import pytest
from dera.diagnostics.enums import (
    DiagnosticSeverity,
    EvaluationStatus,
    RuleCategory,
)
from dera.diagnostics.evidence import DiagnosticEvidence
from dera.diagnostics.models import (
    DiagnosticCoverage,
    DiagnosticFinding,
    DiagnosticReport,
    DiagnosticSummaryCounts,
    RuleEvaluation,
    RuleMetadata,
)


def test_rule_metadata_validation() -> None:
    """Verifies RuleMetadata validation on invalid or missing identifiers."""
    with pytest.raises(ValueError, match="non-empty rule_id"):
        RuleMetadata(
            rule_id="",
            title="Invalid Rule",
            description="Missing ID",
            version="1.0.0",
            category=RuleCategory.STRUCTURAL_INTEGRITY,
            default_severity=DiagnosticSeverity.HIGH,
            supported_object_kinds=("table",),
        )

    with pytest.raises(ValueError, match="must specify a title"):
        RuleMetadata(
            rule_id="DERA-TEST-001",
            title="",
            description="Missing title",
            version="1.0.0",
            category=RuleCategory.STRUCTURAL_INTEGRITY,
            default_severity=DiagnosticSeverity.HIGH,
            supported_object_kinds=("table",),
        )


def test_evidence_sanitization() -> None:
    """Verifies that secrets and credentials in evidence values are sanitized."""
    raw_conn = "postgresql://dbuser:s3cr3t_p@ss!@db.internal:5432/production"
    evidence = DiagnosticEvidence(
        object_id="dera:table:users",
        field_name="connection_string",
        observed_value=raw_conn,
        context_data={"api_key": "sensitive_token_12345", "table": "users"},
    )

    canonical = evidence.to_canonical_dict()
    assert "s3cr3t_p@ss!" not in str(canonical["observed_value"])
    assert "://***:***@" in str(canonical["observed_value"])
    assert canonical["context_data"]["api_key"] == "[REDACTED]"
    assert canonical["context_data"]["table"] == "users"


def test_diagnostic_finding_fingerprint_auto_generation() -> None:
    """Verifies that DiagnosticFinding automatically generates a stable SHA-256 fingerprint."""
    evidence = (
        DiagnosticEvidence(
            object_id="dera:table:orders",
            field_name="column_count",
            observed_value=0,
            expected_value=1,
            message="Zero columns found.",
        ),
    )

    finding = DiagnosticFinding(
        rule_id="DERA-SCHEMA-004",
        rule_version="1.0.0",
        object_id="dera:table:orders",
        severity=DiagnosticSeverity.HIGH,
        title="Empty Table Definition",
        description="Table orders has zero columns.",
        evidence=evidence,
        severity_rationale="Relational tables require at least one column.",
        recommendation="Define columns on table orders.",
    )

    assert len(finding.fingerprint) == 64
    assert int(finding.fingerprint, 16) > 0

    # Ensure immutability
    with pytest.raises(AttributeError):
        finding.severity = DiagnosticSeverity.LOW  # type: ignore[misc]


def test_diagnostic_report_to_canonical_dict() -> None:
    """Verifies canonical dictionary generation for reports."""
    summary = DiagnosticSummaryCounts(
        total_rules_evaluated=1,
        rules_passed=1,
        rules_with_findings=0,
        rules_skipped=0,
        rules_unsupported=0,
        rules_insufficient_metadata=0,
        rules_errored=0,
        total_findings=0,
    )
    coverage = DiagnosticCoverage(evaluated_rules=("DERA-SCHEMA-001",))

    report = DiagnosticReport(
        evaluation_id="eval_12345",
        evaluated_at="2026-10-31T12:00:00Z",
        snapshot_id="snap_67890",
        rule_set_version="1.0.0",
        config_fingerprint="abc123hash",
        findings=(),
        rule_evaluations=(
            RuleEvaluation(
                rule_id="DERA-SCHEMA-001",
                rule_version="1.0.0",
                status=EvaluationStatus.PASS,
                message="All targets resolved.",
            ),
        ),
        summary=summary,
        coverage=coverage,
        source_engine="postgresql",
        report_hash="reporthash789",
    )

    d = report.to_canonical_dict()
    assert d["evaluation_id"] == "eval_12345"
    assert d["snapshot_id"] == "snap_67890"
    assert d["summary"]["rules_passed"] == 1
    assert d["coverage"]["evaluated_rules"] == ["DERA-SCHEMA-001"]
