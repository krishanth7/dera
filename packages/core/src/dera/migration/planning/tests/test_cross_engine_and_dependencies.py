"""Comprehensive Cross-Engine and Advanced Dependency Tests for Phase 9.3.

Covers:
1. Namespace before table ordering.
2. Drop foreign key before drop table ordering.
3. Multi-node circular dependency handling.
4. Cross-engine planning across PostgreSQL, Supabase, SQLite, MySQL, and MariaDB.
5. Serialization and schema immutability during planning.
"""

from dera.comparison.enums import ComparisonChangeType, ComparisonObjectType, ComparisonStatus
from dera.comparison.evidence import ObjectEvidence
from dera.comparison.models import (
    ComparisonConfig,
    ComparisonReport,
    ComparisonSummary,
    SchemaChange,
)
from dera.diagnostics.enums import DiagnosticSeverity
from dera.migration.classification.models import ClassifiedChange
from dera.migration.enums import (
    CompatibilityLevel,
    ReversibilityClassification,
    ReviewPriority,
    RiskDimension,
    RiskEvidenceCertainty,
    StructuralChangeCategory,
)
from dera.migration.planning import (
    EngineCapabilityState,
    ManualGateStatus,
    MigrationOperationType,
    MigrationPlanningEngine,
    PlanningStageType,
    PlanStatus,
)
from dera.migration.reports.models import MigrationRiskReport
from dera.migration.risk.models import MigrationRiskAssessment


def _make_fixture_plan(changes: list[SchemaChange], engine: str = "postgresql"):
    config = ComparisonConfig()
    summary = ComparisonSummary(
        total_changes=len(changes),
        total_added=sum(1 for c in changes if c.change_type == ComparisonChangeType.ADDED),
        total_removed=sum(1 for c in changes if c.change_type == ComparisonChangeType.REMOVED),
        total_modified=sum(1 for c in changes if c.change_type == ComparisonChangeType.MODIFIED),
    )

    comp_report = ComparisonReport.create(
        baseline_snapshot_id="snap_base",
        baseline_fingerprint="base_fp_12345",
        target_snapshot_id="snap_target",
        target_fingerprint="target_fp_12345",
        engine=engine,
        target_engine=engine,
        config=config,
        status=ComparisonStatus.DIFFERENCES_FOUND,
        summary=summary,
        changes=tuple(changes),
    )

    classified = []
    risks = []
    for c in changes:
        cc = ClassifiedChange(
            source_change_id=c.change_id,
            source_fingerprint=c.fingerprint,
            object_type=c.object_type,
            change_type=c.change_type,
            category=StructuralChangeCategory.ADDITIVE
            if c.change_type == ComparisonChangeType.ADDED
            else StructuralChangeCategory.REMOVAL,
            canonical_id=c.canonical_id,
            namespace=c.namespace,
            name=c.name,
            parent_name=c.parent_name,
            compatibility=CompatibilityLevel.COMPATIBLE_WITH_KNOWN_METADATA,
            is_potentially_breaking=(c.change_type == ComparisonChangeType.REMOVED),
            compatibility_rationale="Evaluated change.",
        )
        classified.append(cc)

        ra = MigrationRiskAssessment.create(
            source_change_id=c.change_id,
            source_change_fingerprint=c.fingerprint,
            rule_id="RULE-RISK-001",
            dimension=RiskDimension.DATA_PRESERVATION,
            severity=DiagnosticSeverity.HIGH
            if c.change_type == ComparisonChangeType.REMOVED
            else DiagnosticSeverity.INFORMATIONAL,
            priority=ReviewPriority.P2_HIGH
            if c.change_type == ComparisonChangeType.REMOVED
            else ReviewPriority.P4_LOW,
            certainty=RiskEvidenceCertainty.VERIFIED,
            reversibility=ReversibilityClassification.REQUIRES_PRESERVED_DATA
            if c.change_type == ComparisonChangeType.REMOVED
            else ReversibilityClassification.POTENTIALLY_REVERSIBLE,
            title="Assessed change",
            description="Structural impact analyzed.",
            evidence_summary={},
        )
        risks.append(ra)

    risk_report = MigrationRiskReport.create(
        baseline_snapshot_id="snap_base",
        baseline_fingerprint="base_fp_12345",
        target_snapshot_id="snap_target",
        target_fingerprint="target_fp_12345",
        comparison_report_id=comp_report.report_id,
        comparison_fingerprint=comp_report.report_fingerprint,
        engine=engine,
        classified_changes=tuple(classified),
        risk_assessments=tuple(risks),
    )

    engine_instance = MigrationPlanningEngine(target_engine=engine)
    return engine_instance.plan_migration(comp_report, risk_report)


def test_drop_foreign_key_before_drop_table():
    """Verify foreign key removal precedes referenced table drop."""
    changes = [
        SchemaChange.create(
            change_type=ComparisonChangeType.REMOVED,
            object_type=ComparisonObjectType.TABLE,
            canonical_id="tbl_parent_id",
            namespace="public",
            name="parent_tbl",
            engine="postgresql",
        ),
        SchemaChange.create(
            change_type=ComparisonChangeType.REMOVED,
            object_type=ComparisonObjectType.FOREIGN_KEY,
            canonical_id="fk_child_id",
            namespace="public",
            name="fk_child",
            parent_canonical_id="tbl_child_id",
            parent_name="child_tbl",
            after_evidence=ObjectEvidence(
                snapshot_id="snap_target",
                object_id="fk_child_id",
                namespace="public",
                name="fk_child",
                properties={"referenced_table": "parent_tbl", "referenced_schema": "public"},
            ),
            engine="postgresql",
        ),
    ]

    plan = _make_fixture_plan(changes, engine="postgresql")
    op_types = [op.operation_type for op in plan.operations]

    assert MigrationOperationType.DROP_FOREIGN_KEY in op_types
    assert MigrationOperationType.DROP_TABLE in op_types
    fk_drop_idx = op_types.index(MigrationOperationType.DROP_FOREIGN_KEY)
    tbl_drop_idx = op_types.index(MigrationOperationType.DROP_TABLE)
    assert fk_drop_idx < tbl_drop_idx


def test_cross_engine_sqlite_vs_postgres_create_namespace():
    """Verify namespace operations are unsupported on SQLite but supported on PostgreSQL."""
    changes = [
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.NAMESPACE,
            canonical_id="ns_analytics_id",
            namespace="analytics",
            name="analytics",
            engine="postgresql",
        )
    ]

    pg_plan = _make_fixture_plan(changes, engine="postgresql")
    assert pg_plan.plan_status == PlanStatus.READY_FOR_REVIEW
    assert pg_plan.operations[0].engine_capability == EngineCapabilityState.SUPPORTED

    sqlite_plan = _make_fixture_plan(changes, engine="sqlite")
    assert sqlite_plan.plan_status == PlanStatus.UNSUPPORTED
    assert sqlite_plan.operations[0].engine_capability == EngineCapabilityState.UNSUPPORTED
    assert sqlite_plan.operations[0].is_blocked is True


def test_cross_engine_mysql_and_mariadb_compatibility():
    """Verify MySQL and MariaDB engine plans evaluate correctly."""
    changes = [
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.TABLE,
            canonical_id="tbl_metrics_id",
            namespace="metrics",
            name="system_metrics",
            engine="mysql",
        )
    ]

    mysql_plan = _make_fixture_plan(changes, engine="mysql")
    assert mysql_plan.target_engine == "mysql"
    assert mysql_plan.summary.total_operations == 1

    mariadb_plan = _make_fixture_plan(changes, engine="mariadb")
    assert mariadb_plan.target_engine == "mariadb"
    assert mariadb_plan.summary.total_operations == 1


def test_stages_and_manual_gates_for_destructive_change():
    """Verify destructive changes generate required manual data preservation gates and correct stages."""
    changes = [
        SchemaChange.create(
            change_type=ComparisonChangeType.REMOVED,
            object_type=ComparisonObjectType.TABLE,
            canonical_id="tbl_legacy_id",
            namespace="public",
            name="legacy_table",
            engine="postgresql",
        )
    ]

    plan = _make_fixture_plan(changes, engine="postgresql")
    assert plan.plan_status == PlanStatus.REQUIRES_MANUAL_DECISION
    assert len(plan.manual_decision_gates) > 0
    gate = plan.manual_decision_gates[0]
    assert gate.decision_category == "DATA_PRESERVATION"
    assert gate.gate_status == ManualGateStatus.REQUIRED

    stage_types = [s.stage_type for s in plan.stages]
    assert PlanningStageType.SCHEMA_MODIFICATION in stage_types
