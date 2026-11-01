"""Unit and Behavioral Tests for Phase 9.2 Migration Risk Analysis Engine."""

from __future__ import annotations

import pytest
from dera.comparison.engine import SchemaComparisonEngine
from dera.comparison.tests.fixtures import (
    build_snapshot_from_payload,
    make_standard_ecommerce_payload,
    make_test_column,
)
from dera.diagnostics.enums import DiagnosticSeverity
from dera.metadata.enums import CanonicalTypeCategory
from dera.migration.engine import MigrationRiskAnalysisEngine
from dera.migration.enums import (
    CompatibilityLevel,
    ReviewPriority,
    RiskDimension,
    StructuralChangeCategory,
)
from dera.migration.errors import InvalidComparisonReportError, RiskResourceLimitExceededError
from dera.migration.limits import MigrationRiskLimits
from dera.reverse_engineering.graph.models import (
    ForeignKeyEdge,
)
from dera.reverse_engineering.graph.nodes import TableNode


class TestMigrationRiskAnalysisUnit:
    """Test suite for Phase 9.2 change classification and migration risk analysis."""

    def test_classify_and_evaluate_dropped_table(self) -> None:
        """Verify dropped table produces REMOVAL classification, POTENTIALLY_BREAKING, and P1 risk."""
        base_payload = make_standard_ecommerce_payload()
        snap_base = build_snapshot_from_payload(base_payload, snapshot_id="snap_base")

        # Target drops 'orders' table
        target_tables = tuple(t for t in base_payload.tables if t.name != "orders")
        target_payload = base_payload.model_copy(
            update={"tables": target_tables, "relationships": ()}
        )
        snap_target = build_snapshot_from_payload(target_payload, snapshot_id="snap_target")

        # 1. Diff report from Phase 9.1
        comp_engine = SchemaComparisonEngine()
        comp_report = comp_engine.compare(snap_base, snap_target)

        # 2. Risk analysis
        risk_engine = MigrationRiskAnalysisEngine()
        risk_report = risk_engine.analyze(comp_report)

        assert risk_report.summary.total_changes > 0
        assert risk_report.summary.removals >= 1
        assert risk_report.summary.potentially_breaking >= 1

        # Locate classified table removal
        table_classified = next(c for c in risk_report.classified_changes if c.name == "orders")
        assert table_classified.category == StructuralChangeCategory.REMOVAL
        assert table_classified.compatibility == CompatibilityLevel.POTENTIALLY_BREAKING
        assert table_classified.is_potentially_breaking is True

        # Check risk assessments
        data_risks = [
            r
            for r in risk_report.risk_assessments
            if r.dimension == RiskDimension.DATA_PRESERVATION
        ]
        assert len(data_risks) >= 1
        top_risk = data_risks[0]
        assert top_risk.priority == ReviewPriority.P1_CRITICAL
        assert top_risk.severity == DiagnosticSeverity.CRITICAL
        assert "orders" in top_risk.title
        assert len(top_risk.recommendations) >= 1

    def test_classify_and_evaluate_added_non_null_column(self) -> None:
        """Verify adding a NOT NULL column without a default flags execution complexity risk."""
        base_payload = make_standard_ecommerce_payload()
        snap_base = build_snapshot_from_payload(base_payload, snapshot_id="snap_base")

        # Target adds non-null column without default to users
        users_table = next(t for t in base_payload.tables if t.name == "users")
        new_col = make_test_column(
            table_id=users_table.table_id,
            name="tax_identifier",
            ordinal=5,
            native_type="varchar(50)",
            canonical_type=CanonicalTypeCategory.TEXT,
            is_nullable=False,
            default_expression=None,
        )
        mod_users = users_table.model_copy(update={"columns": users_table.columns + (new_col,)})
        other_tables = [t for t in base_payload.tables if t.name != "users"]
        target_payload = base_payload.model_copy(
            update={"tables": tuple(other_tables + [mod_users])}
        )
        snap_target = build_snapshot_from_payload(target_payload, snapshot_id="snap_target")

        comp_report = SchemaComparisonEngine().compare(snap_base, snap_target)
        risk_report = MigrationRiskAnalysisEngine().analyze(comp_report)

        col_classified = next(
            c for c in risk_report.classified_changes if c.name == "tax_identifier"
        )
        assert col_classified.category == StructuralChangeCategory.ADDITIVE
        assert col_classified.compatibility == CompatibilityLevel.BREAKING_UNDER_STATED_CONDITIONS
        assert col_classified.is_potentially_breaking is True

        # Risk assessment for NOT NULL column without default
        compat_risks = [r for r in risk_report.risk_assessments if r.rule_id == "RISK-COMPAT-001"]
        assert len(compat_risks) == 1
        assert compat_risks[0].priority == ReviewPriority.P2_HIGH
        assert len(compat_risks[0].recommendations) >= 1

    def test_type_narrowing_risk_detection(self) -> None:
        """Verify column type narrowing (text -> varchar(50)) flags potential truncation."""
        base_payload = make_standard_ecommerce_payload()
        snap_base = build_snapshot_from_payload(base_payload, snapshot_id="snap_base")

        # Users 'name' text column narrowed to varchar(50)
        users_table = next(t for t in base_payload.tables if t.name == "users")
        new_cols = []
        for c in users_table.columns:
            if c.name == "name":
                new_cols.append(c.model_copy(update={"native_data_type": "varchar(50)"}))
            else:
                new_cols.append(c)
        mod_users = users_table.model_copy(update={"columns": tuple(new_cols)})
        other_tables = [t for t in base_payload.tables if t.name != "users"]
        target_payload = base_payload.model_copy(
            update={"tables": tuple(other_tables + [mod_users])}
        )
        snap_target = build_snapshot_from_payload(target_payload, snapshot_id="snap_target")

        comp_report = SchemaComparisonEngine().compare(snap_base, snap_target)
        risk_report = MigrationRiskAnalysisEngine().analyze(comp_report)

        type_risks = [r for r in risk_report.risk_assessments if r.rule_id == "RISK-DATA-003"]
        assert len(type_risks) == 1
        assert type_risks[0].dimension == RiskDimension.DATA_PRESERVATION
        assert "varchar(50)" in type_risks[0].evidence_summary["after_type"]

    def test_dependency_blast_radius_analysis(self) -> None:
        """Verify reverse reachability discovery on foreign key graph."""
        base_payload = make_standard_ecommerce_payload()
        snap_base = build_snapshot_from_payload(base_payload, snapshot_id="snap_base")

        # Mock ForeignKeyGraph: orders references users
        users_tbl = next(t for t in base_payload.tables if t.name == "users")
        orders_tbl = next(t for t in base_payload.tables if t.name == "orders")

        from datetime import UTC, datetime

        from dera.metadata.provenance import MetadataProvenance

        prov = MetadataProvenance(
            source_engine="postgresql",
            source_version="16.0",
            connector_version="1.0.0",
            collection_timestamp=datetime(2026, 11, 1, 12, 0, 0, tzinfo=UTC),
            native_identifier="test",
        )
        node_users = TableNode(
            object_id=users_tbl.table_id,
            namespace_name=users_tbl.namespace,
            native_name=users_tbl.name,
            provenance=prov,
        )
        node_orders = TableNode(
            object_id=orders_tbl.table_id,
            namespace_name=orders_tbl.namespace,
            native_name=orders_tbl.name,
            provenance=prov,
        )
        # Edge direction: orders (child holding FK) -> users (parent)
        fk_edge = ForeignKeyEdge(
            object_id="fk_orders_user_id",
            native_name="fk_orders_user",
            source_table_id=orders_tbl.table_id,
            source_table_name=orders_tbl.name,
            referenced_table_id=users_tbl.table_id,
            referenced_table_name=users_tbl.name,
            provenance=prov,
        )
        from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder

        builder = ForeignKeyGraphBuilder(
            database_id="db_canonical_01",
            database_name="shop_db",
            engine="postgresql",
            provenance=prov,
        )
        builder.add_node(node_users)
        builder.add_node(node_orders)
        builder.add_edge(fk_edge)
        graph = builder.build()

        # Drop 'users' in target
        target_tables = (orders_tbl,)
        target_payload = base_payload.model_copy(
            update={"tables": target_tables, "relationships": ()}
        )
        snap_target = build_snapshot_from_payload(target_payload, snapshot_id="snap_target")

        comp_report = SchemaComparisonEngine().compare(snap_base, snap_target)
        risk_report = MigrationRiskAnalysisEngine().analyze(comp_report, dependency_graph=graph)

        # Check blast radius metrics
        user_blast = next(
            (
                b
                for b in risk_report.blast_radius_reports
                if b.target_table_id == users_tbl.table_id
            ),
            None,
        )
        assert user_blast is not None
        assert user_blast.direct_dependents_count == 1
        assert user_blast.dependents[0].name == "orders"

        # Check blast radius risk assessment
        blast_risks = [r for r in risk_report.risk_assessments if r.rule_id == "RISK-BLAST-001"]
        assert len(blast_risks) >= 1
        assert blast_risks[0].priority == ReviewPriority.P1_CRITICAL

    def test_input_validation_and_resource_limits(self) -> None:
        """Verify strict input validation and resource bounding."""
        engine = MigrationRiskAnalysisEngine(limits=MigrationRiskLimits(max_changes_to_analyze=0))
        base_payload = make_standard_ecommerce_payload()
        snap_base = build_snapshot_from_payload(base_payload, snapshot_id="snap_base")
        snap_target = build_snapshot_from_payload(
            base_payload.model_copy(update={"tables": ()}), snapshot_id="snap_target"
        )
        comp_report = SchemaComparisonEngine().compare(snap_base, snap_target)

        # Should raise RiskResourceLimitExceededError due to limit of 0
        with pytest.raises(RiskResourceLimitExceededError) as exc_info:
            engine.analyze(comp_report)
        assert exc_info.value.limit_name == "max_changes_to_analyze"

        # Should raise InvalidComparisonReportError on non-report input
        with pytest.raises(InvalidComparisonReportError):
            MigrationRiskAnalysisEngine().analyze(None)  # type: ignore[arg-type]

    def test_deterministic_risk_report_reproducibility(self) -> None:
        """Verify that identical inputs produce identical report fingerprints."""
        base_payload = make_standard_ecommerce_payload()
        snap_base = build_snapshot_from_payload(base_payload, snapshot_id="snap_base")
        snap_target = build_snapshot_from_payload(
            base_payload.model_copy(update={"namespaces": ("public", "analytics")}),
            snapshot_id="snap_target",
        )

        comp_report = SchemaComparisonEngine().compare(snap_base, snap_target)
        engine = MigrationRiskAnalysisEngine()

        report_1 = engine.analyze(comp_report)
        report_2 = engine.analyze(comp_report)

        assert report_1.report_fingerprint == report_2.report_fingerprint
        assert report_1.report_id == report_2.report_id
        assert len(report_1.risk_assessments) == len(report_2.risk_assessments)
        for r1, r2 in zip(report_1.risk_assessments, report_2.risk_assessments, strict=True):
            assert r1.fingerprint == r2.fingerprint
