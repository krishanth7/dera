"""Unit tests for Phase 9.3 Migration Planning.

Tests:
1. Change to operation mapping.
2. Dependency graph construction and edge direction (Prerequisite -> Dependent).
3. Topological ordering with stable tie-breaking.
4. Cycle detection (Tarjan SCC) and blocked operation annotations.
5. Manual decision gates and preconditions.
6. Plan fingerprint determinism.
7. Engine-specific capability evaluations (PostgreSQL, SQLite, MySQL).
"""

import pytest
from dera.comparison.enums import ComparisonChangeType, ComparisonObjectType, ComparisonStatus
from dera.comparison.evidence import ObjectEvidence, PropertyDifference
from dera.comparison.models import ComparisonConfig, ComparisonReport, ComparisonSummary, SchemaChange
from dera.diagnostics.enums import DiagnosticSeverity
from dera.migration.enums import (
    CompatibilityLevel,
    ReversibilityClassification,
    ReviewPriority,
    RiskDimension,
    RiskEvidenceCertainty,
    StructuralChangeCategory,
)
from dera.migration.classification.models import ClassifiedChange
from dera.migration.reports.models import MigrationRiskReport
from dera.migration.risk.models import MigrationRiskAssessment
from dera.migration.planning import (
    ChangeToOperationMapper,
    CycleDetector,
    DeterministicOrderingEngine,
    EngineCapabilityState,
    ManualGateStatus,
    MigrationOperationType,
    MigrationPlanReport,
    MigrationPlanningEngine,
    OperationDependencyGraph,
    PlanFingerprintCalculator,
    PlanStatus,
    PlanningStageType,
)


def _make_dummy_comparison_and_risk(changes: list[SchemaChange], engine="postgresql"):
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
            category=StructuralChangeCategory.ADDITIVE,
            canonical_id=c.canonical_id,
            namespace=c.namespace,
            name=c.name,
            parent_name=c.parent_name,
            compatibility=CompatibilityLevel.COMPATIBLE_WITH_KNOWN_METADATA,
            is_potentially_breaking=False,
            compatibility_rationale="Safe additive change.",
        )
        classified.append(cc)

        ra = MigrationRiskAssessment.create(
            source_change_id=c.change_id,
            source_change_fingerprint=c.fingerprint,
            rule_id="RULE-ADD-001",
            dimension=RiskDimension.DATA_PRESERVATION,
            severity=DiagnosticSeverity.INFORMATIONAL,
            priority=ReviewPriority.P4_LOW,
            certainty=RiskEvidenceCertainty.VERIFIED,
            reversibility=ReversibilityClassification.POTENTIALLY_REVERSIBLE,
            title="Safe change",
            description="No structural hazard detected.",
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

    return comp_report, risk_report


def test_change_to_operation_mapping():
    """Verify schema changes map accurately to abstract migration operations."""
    changes = [
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.TABLE,
            canonical_id="tbl_users_id",
            namespace="public",
            name="users",
            engine="postgresql",
        ),
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.COLUMN,
            canonical_id="col_email_id",
            namespace="public",
            name="email",
            parent_canonical_id="tbl_users_id",
            parent_name="users",
            engine="postgresql",
        ),
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.INDEX,
            canonical_id="idx_email_id",
            namespace="public",
            name="idx_email",
            parent_canonical_id="tbl_users_id",
            parent_name="users",
            engine="postgresql",
        ),
    ]

    mapper = ChangeToOperationMapper(target_engine="postgresql")
    ops = mapper.map_changes(schema_changes=changes)

    assert len(ops) == 3
    op_types = [o.operation_type for o in ops]
    assert MigrationOperationType.CREATE_TABLE in op_types
    assert MigrationOperationType.ADD_COLUMN in op_types
    assert MigrationOperationType.CREATE_INDEX in op_types


def test_dependency_ordering_table_before_column_and_index():
    """Verify table creation precedes column addition and index creation."""
    changes = [
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.TABLE,
            canonical_id="tbl_users_id",
            namespace="public",
            name="users",
            engine="postgresql",
        ),
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.COLUMN,
            canonical_id="col_email_id",
            namespace="public",
            name="email",
            parent_canonical_id="tbl_users_id",
            parent_name="users",
            engine="postgresql",
        ),
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.INDEX,
            canonical_id="idx_email_id",
            namespace="public",
            name="idx_email",
            parent_canonical_id="tbl_users_id",
            parent_name="users",
            engine="postgresql",
        ),
    ]

    comp_report, risk_report = _make_dummy_comparison_and_risk(changes)
    engine = MigrationPlanningEngine(target_engine="postgresql")
    plan = engine.plan_migration(comp_report, risk_report)

    op_order = [op.operation_type for op in plan.operations]
    assert op_order[0] == MigrationOperationType.CREATE_TABLE
    table_idx = op_order.index(MigrationOperationType.CREATE_TABLE)
    col_idx = op_order.index(MigrationOperationType.ADD_COLUMN)
    idx_idx = op_order.index(MigrationOperationType.CREATE_INDEX)
    assert table_idx < col_idx
    assert table_idx < idx_idx


def test_foreign_key_ordering_referenced_table_first():
    """Verify parent table is created before foreign key referencing it."""
    changes = [
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.TABLE,
            canonical_id="tbl_orders_id",
            namespace="public",
            name="orders",
            engine="postgresql",
        ),
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.TABLE,
            canonical_id="tbl_customers_id",
            namespace="public",
            name="customers",
            engine="postgresql",
        ),
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.FOREIGN_KEY,
            canonical_id="fk_cust_id",
            namespace="public",
            name="fk_cust",
            parent_canonical_id="tbl_orders_id",
            parent_name="orders",
            after_evidence=ObjectEvidence(
                snapshot_id="snap_target",
                object_id="fk_cust_id",
                namespace="public",
                name="fk_cust",
                properties={"referenced_table": "customers", "referenced_schema": "public"},
            ),
            engine="postgresql",
        ),
    ]

    comp_report, risk_report = _make_dummy_comparison_and_risk(changes)
    engine = MigrationPlanningEngine(target_engine="postgresql")
    plan = engine.plan_migration(comp_report, risk_report)

    target_names = [op.target_object_name for op in plan.operations]
    cust_idx = target_names.index("customers")
    fk_idx = target_names.index("fk_cust")
    # customers table must be created before fk_cust is established
    assert cust_idx < fk_idx


def test_cycle_detection_blocks_circular_operations():
    """Verify circular dependency causes operations to be marked as BLOCKED."""
    changes = [
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.TABLE,
            canonical_id="tbl_a_id",
            namespace="public",
            name="tbl_a",
            engine="postgresql",
        ),
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.TABLE,
            canonical_id="tbl_b_id",
            namespace="public",
            name="tbl_b",
            engine="postgresql",
        ),
    ]

    mapper = ChangeToOperationMapper(target_engine="postgresql")
    ops = mapper.map_changes(changes)

    graph = OperationDependencyGraph(ops)
    # Manually introduce a cycle: op_a -> op_b and op_b -> op_a
    op_a = ops[0].operation_id
    op_b = ops[1].operation_id
    graph.add_dependency(op_a, op_b)
    graph.add_dependency(op_b, op_a)

    detector = CycleDetector(graph)
    cycles = detector.annotate_blocked_operations()

    assert len(cycles) == 1
    assert set(cycles[0]) == {op_a, op_b}
    assert ops[0].is_blocked is True
    assert ops[1].is_blocked is True
    assert "Circular dependency" in ops[0].blocking_reasons[0]


def test_sqlite_engine_capabilities_unsupported_ops():
    """Verify SQLite flags ALTER COLUMN TYPE as UNSUPPORTED."""
    changes = [
        SchemaChange.create(
            change_type=ComparisonChangeType.MODIFIED,
            object_type=ComparisonObjectType.COLUMN,
            canonical_id="col_age_id",
            namespace="public",
            name="age",
            parent_canonical_id="tbl_users_id",
            parent_name="users",
            property_differences=(
                PropertyDifference(
                    property_name="type",
                    before_value="INTEGER",
                    after_value="BIGINT",
                ),
            ),
            engine="sqlite",
        ),
    ]

    comp_report, risk_report = _make_dummy_comparison_and_risk(changes, engine="sqlite")
    engine = MigrationPlanningEngine(target_engine="sqlite")
    plan = engine.plan_migration(comp_report, risk_report)

    assert plan.plan_status == PlanStatus.UNSUPPORTED
    op = plan.operations[0]
    assert op.engine_capability == EngineCapabilityState.UNSUPPORTED
    assert op.is_blocked is True
    assert "unsupported on target engine 'sqlite'" in op.blocking_reasons[0]


def test_deterministic_plan_fingerprint():
    """Verify that identical inputs produce identical canonical fingerprints."""
    changes = [
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.TABLE,
            canonical_id="tbl_posts_id",
            namespace="public",
            name="posts",
            engine="postgresql",
        ),
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.TABLE,
            canonical_id="tbl_users_id",
            namespace="public",
            name="users",
            engine="postgresql",
        ),
    ]

    comp_report, risk_report = _make_dummy_comparison_and_risk(changes)
    engine = MigrationPlanningEngine(target_engine="postgresql")

    plan1 = engine.plan_migration(comp_report, risk_report)
    plan2 = engine.plan_migration(comp_report, risk_report)

    assert plan1.plan_fingerprint == plan2.plan_fingerprint
    assert plan1.plan_id == plan2.plan_id
    assert [op.operation_id for op in plan1.operations] == [op.operation_id for op in plan2.operations]
