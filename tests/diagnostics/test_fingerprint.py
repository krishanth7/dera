"""Tests for DERA diagnostic fingerprinting and canonical serialization."""

from __future__ import annotations

from dera.diagnostics.enums import (
    DiagnosticSeverity,
    EvaluationStatus,
)
from dera.diagnostics.evidence import DiagnosticEvidence
from dera.diagnostics.fingerprint import (
    compute_config_fingerprint,
    compute_finding_fingerprint,
)
from dera.diagnostics.models import (
    DiagnosticCoverage,
    DiagnosticFinding,
    DiagnosticReport,
    DiagnosticSummaryCounts,
    RuleEvaluation,
)
from dera.diagnostics.serialization import (
    deserialize_diagnostic_report,
    serialize_diagnostic_report,
)


def test_fingerprint_reproducibility() -> None:
    """Verifies that identical finding inputs produce identical SHA-256 fingerprints."""
    ev1 = DiagnosticEvidence(
        object_id="dera:table:users",
        field_name="primary_key",
        observed_value=None,
        expected_value="PrimaryKeyConstraint",
    )
    ev2 = DiagnosticEvidence(
        object_id="dera:table:users",
        field_name="column_count",
        observed_value=5,
        expected_value=5,
    )

    fp1 = compute_finding_fingerprint("DERA-SCHEMA-001", "1.0.0", "dera:table:users", (ev1, ev2))
    fp2 = compute_finding_fingerprint("DERA-SCHEMA-001", "1.0.0", "dera:table:users", (ev2, ev1))

    # Evidence ordering must not alter the fingerprint
    assert fp1 == fp2
    assert len(fp1) == 64


def test_config_fingerprint_stability() -> None:
    """Verifies config fingerprint generation stability."""
    cfg1 = {"enabled_rule_ids": ["DERA-SCHEMA-001"], "disabled_rule_ids": []}
    cfg2 = {"disabled_rule_ids": [], "enabled_rule_ids": ["DERA-SCHEMA-001"]}

    hash1 = compute_config_fingerprint(cfg1)
    hash2 = compute_config_fingerprint(cfg2)

    assert hash1 == hash2


def test_report_serialization_roundtrip() -> None:
    """Verifies serialization and deserialization roundtrip preserves exact values."""
    ev = DiagnosticEvidence(
        object_id="dera:table:orders",
        field_name="columns",
        observed_value=0,
        expected_value=1,
        message="No columns.",
    )
    finding = DiagnosticFinding(
        rule_id="DERA-SCHEMA-004",
        rule_version="1.0.0",
        object_id="dera:table:orders",
        severity=DiagnosticSeverity.HIGH,
        title="Empty Table",
        description="Orders table has no columns.",
        evidence=(ev,),
        severity_rationale="Requires columns.",
        recommendation="Add columns.",
    )
    eval_record = RuleEvaluation(
        rule_id="DERA-SCHEMA-004",
        rule_version="1.0.0",
        status=EvaluationStatus.FINDINGS_DETECTED,
        findings=(finding,),
        execution_duration_ms=1.234,
        message="Findings detected.",
    )
    summary = DiagnosticSummaryCounts(
        total_rules_evaluated=1,
        rules_passed=0,
        rules_with_findings=1,
        rules_skipped=0,
        rules_unsupported=0,
        rules_insufficient_metadata=0,
        rules_errored=0,
        total_findings=1,
        findings_by_severity={"HIGH": 1},
    )
    coverage = DiagnosticCoverage(evaluated_rules=("DERA-SCHEMA-004",))

    report = DiagnosticReport(
        evaluation_id="eval_test_abc",
        evaluated_at="2026-10-31T12:00:00Z",
        snapshot_id="snap_test_xyz",
        rule_set_version="1.0.0",
        config_fingerprint="confighash123",
        findings=(finding,),
        rule_evaluations=(eval_record,),
        summary=summary,
        coverage=coverage,
        source_engine="sqlite",
        report_hash="contenthash456",
    )

    serialized = serialize_diagnostic_report(report)
    assert isinstance(serialized, str)

    deserialized = deserialize_diagnostic_report(serialized)
    assert deserialized.evaluation_id == report.evaluation_id
    assert deserialized.snapshot_id == report.snapshot_id
    assert len(deserialized.findings) == 1
    assert deserialized.findings[0].fingerprint == finding.fingerprint
    assert deserialized.findings[0].severity == DiagnosticSeverity.HIGH
    assert deserialized.summary.total_findings == 1
