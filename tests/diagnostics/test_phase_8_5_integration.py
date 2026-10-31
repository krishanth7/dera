"""DERA Diagnostics — Phase 8.5 End-to-End Integration, Security & Performance Tests.

Verifies the complete diagnostic pipeline:
  Phase 8.1-8.4 Rules -> Raw Findings -> Evidence Validation -> Finding Classification ->
  Severity Evaluation -> Deterministic Recommendations -> Prioritization ->
  Suppression Governance -> Explainable Diagnostic Report.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import pytest
from dera.diagnostics.context import DiagnosticContext, DiagnosticEngineConfig
from dera.diagnostics.enums import DiagnosticSeverity
from dera.diagnostics.evaluator import DiagnosticEvaluator
from dera.diagnostics.evidence import DiagnosticEvidence
from dera.diagnostics.governance import (
    FindingLifecycleState,
    SuppressionScope,
    create_suppression,
)
from dera.diagnostics.models import DiagnosticFinding
from dera.diagnostics.rules import ALL_RULES
from dera.diagnostics.serialization import (
    deserialize_diagnostic_report,
    serialize_diagnostic_report,
)
from dera.diagnostics.severity.overrides import create_severity_override
from dera.models import (
    DatabaseColumn,
    DatabaseTable,
    ForeignKeyConstraint,
    PrimaryKeyConstraint,
    TableIndex,
)


@dataclass
class SchemaRepresentationMock:
    tables: tuple[DatabaseTable, ...] = ()
    views: tuple[Any, ...] = ()
    namespaces: tuple[Any, ...] = ()


def _build_test_schema(engine: str = "postgresql") -> SchemaRepresentationMock:
    """Builds a representative relational schema with multiple deliberate diagnostic conditions."""
    col_id = DatabaseColumn(name="id", data_type="integer", is_nullable=False)
    col_name = DatabaseColumn(name="name", data_type="varchar", is_nullable=True)
    col_created = DatabaseColumn(name="created_at", data_type="timestamp", is_nullable=False)

    # 1. users: has PK and index
    users_table = DatabaseTable(
        schema="public",
        name="users",
        columns=(col_id, col_name, col_created),
        primary_key=PrimaryKeyConstraint(name="pk_users", columns=("id",)),
        indexes=(TableIndex(name="idx_users_name", columns=("name",)),),
    )

    # 2. orders: has unindexed foreign key to users, missing PK
    col_order_id = DatabaseColumn(name="order_id", data_type="integer", is_nullable=False)
    col_user_id = DatabaseColumn(name="user_id", data_type="integer", is_nullable=False)
    orders_table = DatabaseTable(
        schema="public",
        name="orders",
        columns=(col_order_id, col_user_id),
        primary_key=None,  # Missing PK -> DERA-CON-001
        foreign_keys=(
            ForeignKeyConstraint(
                name="fk_orders_user",
                source_columns=("user_id",),
                target_schema="public",
                target_table="users",
                target_columns=("id",),
            ),
        ),  # Unindexed FK -> DERA-IDX-003
    )

    # 3. items: wide table with duplicate indexes
    item_cols = [
        DatabaseColumn(name=f"col_{i}", data_type="varchar", is_nullable=True) for i in range(40)
    ]
    item_cols.insert(0, DatabaseColumn(name="id", data_type="integer", is_nullable=False))
    items_table = DatabaseTable(
        schema="public",
        name="items",
        columns=tuple(item_cols),
        primary_key=PrimaryKeyConstraint(name="pk_items", columns=("id",)),
        indexes=(
            TableIndex(name="idx_items_col1_a", columns=("col_1",)),
            TableIndex(name="idx_items_col1_b", columns=("col_1",)),  # Duplicate -> DERA-IDX-001
        ),
    )

    return SchemaRepresentationMock(tables=(users_table, orders_table, items_table))


def test_end_to_end_phase_8_5_pipeline() -> None:
    """Tests the full Phase 8.5 pipeline: rules execution -> enriched findings -> explainable report."""
    schema = _build_test_schema()
    context = DiagnosticContext(schema=schema, source_engine="postgresql")
    evaluator = DiagnosticEvaluator()

    report = evaluator.evaluate(context, ALL_RULES)

    assert report is not None
    assert len(report.findings) > 0
    assert report.explainability is not None
    assert report.explainability.total_rules_considered == len(ALL_RULES)
    assert report.severity_policy_version == "1.0.0"
    assert report.recommendation_catalog_version == "1.0.0"

    # Verify findings are enriched with Phase 8.5 metadata
    for f in report.findings:
        assert f.fingerprint != ""
        assert f.finding_id.startswith("fnd_")
        assert f.classification is not None
        assert f.confidence is not None
        assert f.metadata_completeness is not None
        assert f.severity_rationale != ""
        assert f.priority_score > 0
        assert f.priority_rank is not None

        # Verify structured recommendation exists
        assert f.structured_recommendation is not None
        assert f.structured_recommendation.is_advisory is True


def test_suppressed_finding_visibility() -> None:
    """Verifies that suppressed findings remain auditable in reports and are never silently dropped."""
    schema = _build_test_schema()

    # Pre-evaluate to obtain fingerprint of a finding
    pre_eval = DiagnosticEvaluator().evaluate(DiagnosticContext(schema=schema), ALL_RULES)
    assert len(pre_eval.findings) > 0
    target_finding = pre_eval.findings[0]

    # Create suppression for this specific finding fingerprint
    suppression = create_suppression(
        scope=SuppressionScope.FINGERPRINT,
        fingerprint=target_finding.fingerprint,
        reason="Explicitly accepted finding for temporary staging table",
        authorized_actor="lead_architect@dera.org",
    )

    config = DiagnosticEngineConfig(suppressions=(suppression,))
    context = DiagnosticContext(schema=schema, config=config)

    report = DiagnosticEvaluator().evaluate(context, ALL_RULES)

    # Finding MUST be in report, marked as suppressed
    matching = next(
        (f for f in report.findings if f.fingerprint == target_finding.fingerprint), None
    )
    assert matching is not None
    assert matching.is_suppressed is True
    assert matching.suppression_id == suppression.suppression_id
    assert matching.lifecycle_state == FindingLifecycleState.SUPPRESSED

    # Verify explainability summary tracks suppression count
    assert report.explainability.active_suppression_count >= 1
    assert len(report.suppressions_applied) >= 1


def test_authorized_severity_override_in_evaluation() -> None:
    """Verifies that authorized severity overrides adjust effective severity and record audit state."""
    schema = _build_test_schema()

    pre_eval = DiagnosticEvaluator().evaluate(DiagnosticContext(schema=schema), ALL_RULES)
    dup_idx_finding = next(f for f in pre_eval.findings if f.rule_id == "DERA-IDX-001")

    override = create_severity_override(
        finding_fingerprint=dup_idx_finding.fingerprint,
        original_severity=dup_idx_finding.severity,
        effective_severity=DiagnosticSeverity.INFORMATIONAL,
        override_reason="Duplicate index required temporarily during blue-green deployment",
        authorized_actor="dba_lead@dera.org",
    )

    config = DiagnosticEngineConfig(severity_overrides=(override,))
    context = DiagnosticContext(schema=schema, config=config)

    report = DiagnosticEvaluator().evaluate(context, ALL_RULES)

    overridden = next(
        (f for f in report.findings if f.fingerprint == dup_idx_finding.fingerprint), None
    )
    assert overridden is not None
    assert overridden.severity == DiagnosticSeverity.INFORMATIONAL
    assert overridden.override_id == override.override_id
    assert "Overridden by authorized actor" in overridden.severity_rationale
    assert report.explainability.severity_override_count >= 1
    assert len(report.severity_overrides_applied) >= 1


@pytest.mark.parametrize(
    "engine_name",
    ["postgresql", "supabase", "sqlite", "mysql", "mariadb"],
)
def test_cross_engine_compatibility(engine_name: str) -> None:
    """Verifies Phase 8.5 pipeline executes correctly across all supported database engines."""
    schema = _build_test_schema(engine=engine_name)
    context = DiagnosticContext(schema=schema, source_engine=engine_name)
    report = DiagnosticEvaluator().evaluate(context, ALL_RULES)

    assert report.source_engine == engine_name
    assert report.report_hash != ""
    assert report.summary.total_rules_evaluated > 0


def test_serialization_roundtrip_with_phase_8_5_fields() -> None:
    """Verifies JSON serialization and deserialization preserves all Phase 8.5 fields."""
    schema = _build_test_schema()
    context = DiagnosticContext(schema=schema)
    report = DiagnosticEvaluator().evaluate(context, ALL_RULES)

    json_str = serialize_diagnostic_report(report)
    deserialized = deserialize_diagnostic_report(json_str)

    assert deserialized.evaluation_id == report.evaluation_id
    assert deserialized.report_hash == report.report_hash
    assert deserialized.severity_policy_version == "1.0.0"
    assert len(deserialized.findings) == len(report.findings)

    orig_f = report.findings[0]
    deser_f = deserialized.findings[0]
    assert deser_f.fingerprint == orig_f.fingerprint
    assert deser_f.classification == orig_f.classification
    assert deser_f.confidence == orig_f.confidence
    assert deser_f.priority_score == orig_f.priority_score
    assert deser_f.finding_id == orig_f.finding_id
    if orig_f.structured_recommendation:
        assert deser_f.structured_recommendation is not None
        assert (
            deser_f.structured_recommendation.recommendation_id
            == orig_f.structured_recommendation.recommendation_id
        )
        assert deser_f.structured_recommendation.title == orig_f.structured_recommendation.title
    if orig_f.evidence:
        assert deser_f.evidence[0].evidence_type == orig_f.evidence[0].evidence_type
        assert deser_f.evidence[0].completeness == orig_f.evidence[0].completeness

    from dera.diagnostics.serialization import compute_report_content_hash

    recomputed_hash = compute_report_content_hash(deserialized.to_canonical_dict())
    assert recomputed_hash == report.report_hash


def test_performance_benchmark_scale() -> None:
    """Benchmarks finding enrichment, prioritization, and serialization throughput."""
    ev = DiagnosticEvidence(
        object_id="public.table_test", field_name="field", observed_value="test_val"
    )

    # Generate 1,000 synthetic findings
    findings = [
        DiagnosticFinding(
            rule_id=f"DERA-CON-00{(i % 5) + 1}",
            rule_version="1.0.0",
            object_id=f"public.table_{i}",
            severity=DiagnosticSeverity.HIGH if i % 2 == 0 else DiagnosticSeverity.MEDIUM,
            title=f"Synthetic Finding {i}",
            description=f"Detailed description for synthetic finding {i}",
            evidence=(ev,),
            severity_rationale="Synthetic rationale",
        )
        for i in range(1000)
    ]

    context = DiagnosticContext()

    start = time.perf_counter()
    from dera.diagnostics.evaluator import sort_findings_deterministically
    from dera.diagnostics.evidence.validator import validate_and_enrich_evidence
    from dera.diagnostics.prioritization.classification import classify_rule_finding
    from dera.diagnostics.prioritization.ranking import compute_priority_score, derive_priority_rank
    from dera.diagnostics.recommendations.generator import generate_structured_recommendation
    from dera.diagnostics.severity.policy import derive_effective_severity

    enriched_list = []
    for f in findings:
        ev_res = validate_and_enrich_evidence(f.evidence, context)
        cls = classify_rule_finding(f.rule_id)
        sev, _ = derive_effective_severity(
            f.rule_id, f.severity, cls, ev_res.completeness, ev_res.confidence
        )
        rec = generate_structured_recommendation(f)
        score = compute_priority_score(sev, ev_res.confidence, cls)
        enriched = DiagnosticFinding(
            rule_id=f.rule_id,
            rule_version=f.rule_version,
            object_id=f.object_id,
            severity=sev,
            title=f.title,
            description=f.description,
            evidence=f.evidence,
            severity_rationale="Synthetic rationale",
            classification=cls,
            confidence=ev_res.confidence,
            structured_recommendation=rec,
            priority_score=score,
            priority_rank=derive_priority_rank(sev),
        )
        enriched_list.append(enriched)

    sorted_findings = sort_findings_deterministically(enriched_list)
    duration = time.perf_counter() - start

    assert len(sorted_findings) == 1000
    # 1,000 findings must process in under 1.5 seconds on commodity hardware
    assert duration < 1.5


def test_deserialization_explicit_unknowns_and_unrecognized_evidence_type() -> None:
    """Verifies that unknown completeness/confidence map to UNKNOWN/INCOMPLETE, and unrecognized evidence_type is rejected."""
    import pytest
    from dera.diagnostics.evidence.models import (
        EvidenceCompleteness,
        EvidenceType,
        FindingConfidence,
    )
    from dera.diagnostics.serialization import deserialize_diagnostic_report

    base_report_dict = {
        "evaluation_id": "eval_test_unknowns",
        "evaluated_at": "2026-10-31T00:00:00Z",
        "evaluator_version": "1.0.0",
        "rule_set_version": "1.0.0",
        "database_engine": "postgres",
        "report_hash": "dummy_hash",
        "summary": {
            "total_rules_evaluated": 1,
            "rules_passed": 0,
            "rules_with_findings": 1,
            "rules_skipped": 0,
            "rules_unsupported": 0,
            "rules_insufficient_metadata": 0,
            "rules_errored": 0,
            "total_findings": 1,
            "findings_by_severity": {"LOW": 1},
        },
        "coverage": {
            "evaluated_rules": ["DERA-TEST-001"],
            "skipped_rules": [],
            "unsupported_rules": [],
            "insufficient_metadata_rules": [],
            "errored_rules": [],
        },
        "evaluations": [],
        "findings": [
            {
                "rule_id": "DERA-TEST-001",
                "rule_version": "1.0.0",
                "object_id": "public.test",
                "severity": "LOW",
                "title": "Test Finding",
                "description": "Test Desc",
                "confidence": "completely_unknown_confidence",
                "metadata_completeness": "completely_unknown_completeness",
                "evidence": [
                    {
                        "object_id": "public.test",
                        "field_name": "test_col",
                        "observed_value": 1,
                        "evidence_type": "metric_observation",
                        "completeness": "completely_unknown_completeness",
                    }
                ],
            }
        ],
    }

    import json

    # Deserialization maps explicit unknown confidence and completeness
    report = deserialize_diagnostic_report(json.dumps(base_report_dict))
    f = report.findings[0]
    assert f.confidence == FindingConfidence.INCOMPLETE
    assert f.metadata_completeness == EvidenceCompleteness.UNKNOWN
    assert f.evidence[0].completeness == EvidenceCompleteness.UNKNOWN
    assert f.evidence[0].evidence_type == EvidenceType.METRIC_OBSERVATION

    # Unrecognized evidence type is rejected
    invalid_ev_dict = dict(base_report_dict)
    invalid_ev_dict["findings"] = [
        {
            **base_report_dict["findings"][0],
            "evidence": [
                {
                    "object_id": "public.test",
                    "field_name": "test_col",
                    "observed_value": 1,
                    "evidence_type": "completely_unrecognized_evidence_type",
                }
            ],
        }
    ]
    with pytest.raises(ValueError):
        deserialize_diagnostic_report(json.dumps(invalid_ev_dict))


def test_evaluator_isolates_recommendation_safety_violation() -> None:
    """Verifies evaluator catches RecommendationSafetyViolationError, marking rule as EVALUATION_ERROR and dropping finding."""
    from unittest.mock import patch

    from dera.diagnostics.context import DiagnosticContext
    from dera.diagnostics.evaluator import DiagnosticEvaluator
    from dera.diagnostics.models import (
        DiagnosticFinding,
        DiagnosticSeverity,
        EvaluationStatus,
        RuleCategory,
        RuleEvaluation,
        RuleMetadata,
    )
    from dera.diagnostics.recommendations.safety import RecommendationSafetyViolationError

    class UnsafeRule:
        metadata = RuleMetadata(
            rule_id="DERA-UNSAFE-001",
            version="1.0.0",
            title="Unsafe Rule",
            description="Emits unsafe recommendation",
            category=RuleCategory.STRUCTURAL_INTEGRITY,
            default_severity=DiagnosticSeverity.HIGH,
            supported_object_kinds=("table",),
        )

        def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
            finding = DiagnosticFinding(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                object_id="public.users",
                severity=DiagnosticSeverity.HIGH,
                title="Unsafe Rule Finding",
                description="Needs drop",
                evidence=(),
                severity_rationale="High risk",
            )
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.FINDINGS_DETECTED,
                findings=(finding,),
            )

    evaluator = DiagnosticEvaluator()
    context = DiagnosticContext()

    with patch(
        "dera.diagnostics.evaluator.generate_structured_recommendation",
        side_effect=RecommendationSafetyViolationError("Destructive action prohibited"),
    ):
        report = evaluator.evaluate(context, rules=[UnsafeRule()])

    # Affected rule must be isolated to EVALUATION_ERROR
    assert report.summary.rules_errored == 1
    assert report.summary.rules_with_findings == 0
    assert report.summary.total_findings == 0
    assert "DERA-UNSAFE-001" in report.coverage.errored_rules
    assert report.rule_evaluations[0].status == EvaluationStatus.EVALUATION_ERROR
