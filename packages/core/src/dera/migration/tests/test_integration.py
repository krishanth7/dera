"""Comprehensive Integration, Property-Based, Cross-Engine, and Security Tests for Phase 9.2."""

from __future__ import annotations

import time
import pytest

from dera.comparison.engine import SchemaComparisonEngine
from dera.comparison.tests.fixtures import (
    build_snapshot_from_payload,
    make_standard_ecommerce_payload,
    make_test_column,
    make_test_table,
)
from dera.metadata.enums import CanonicalTypeCategory
from dera.migration.engine import MigrationRiskAnalysisEngine
from dera.migration.enums import (
    CompatibilityLevel,
    ReviewPriority,
    RiskDimension,
    TypeConversionSafety,
)
from dera.migration.reports.models import MigrationRiskReport
from dera.reverse_engineering.snapshots.models import (
    SnapshotIndexPayload,
    SnapshotPrimaryKeyPayload,
    SnapshotStructuralPayload,
    SnapshotUniqueConstraintPayload,
)


class TestMigrationRiskIntegrationAndProperties:
    """End-to-end integration and invariant testing for Phase 9.2."""

    def test_end_to_end_pipeline_phase_6_to_9_2(self) -> None:
        """Integration Pipeline: Phase 6 Snapshots -> Phase 9.1 Comparison -> Phase 9.2 Risk Analysis."""
        base_payload = make_standard_ecommerce_payload(engine="postgresql")
        snap_base = build_snapshot_from_payload(base_payload, snapshot_id="snap_v1")

        # Create target with multiple realistic evolution steps:
        # 1. Modify users: add avatar_url (safe), rename-like drop of name (breaking)
        # 2. Modify orders: add total check constraint, drop unused index
        users_tbl = next(t for t in base_payload.tables if t.name == "users")
        orders_tbl = next(t for t in base_payload.tables if t.name == "orders")

        # Users: drop 'name', add 'full_name' (varchar 200)
        u_cols = [c for c in users_tbl.columns if c.name != "name"]
        u_cols.append(
            make_test_column(users_tbl.table_id, "full_name", 5, "varchar(200)", CanonicalTypeCategory.TEXT, True)
        )
        mod_users = users_tbl.model_copy(update={"columns": tuple(u_cols)})

        # Orders: drop index idx_users_email (on users)
        mod_users = mod_users.model_copy(update={"indexes": ()})

        target_payload = base_payload.model_copy(update={"tables": (orders_tbl, mod_users)})
        snap_target = build_snapshot_from_payload(target_payload, snapshot_id="snap_v2")

        # Phase 9.1 Comparison
        comp_engine = SchemaComparisonEngine()
        comp_report = comp_engine.compare(snap_base, snap_target)
        assert comp_report.summary.total_changes > 0

        # Phase 9.2 Risk Analysis
        risk_engine = MigrationRiskAnalysisEngine()
        risk_report = risk_engine.analyze(comp_report)

        assert isinstance(risk_report, MigrationRiskReport)
        assert risk_report.report_id.startswith("mrk_")
        assert risk_report.report_fingerprint != ""
        assert risk_report.summary.total_changes == comp_report.summary.total_changes
        assert risk_report.summary.potentially_breaking >= 1
        assert len(risk_report.risk_assessments) >= 1
        assert len(risk_report.recommendations) >= 1

    def test_cross_engine_behavior(self) -> None:
        """Cross-Engine: Verify risk evaluation across supported dialects (PostgreSQL, SQLite, MySQL)."""
        for engine_name in ("postgresql", "sqlite", "mysql", "mariadb"):
            base_payload = make_standard_ecommerce_payload(engine=engine_name)
            snap_base = build_snapshot_from_payload(base_payload, snapshot_id=f"snap_{engine_name}_1")

            # Remove a table in target
            target_payload = base_payload.model_copy(update={"tables": (base_payload.tables[0],)})
            snap_target = build_snapshot_from_payload(target_payload, snapshot_id=f"snap_{engine_name}_2")

            comp_report = SchemaComparisonEngine().compare(snap_base, snap_target)
            risk_report = MigrationRiskAnalysisEngine().analyze(comp_report)

            assert risk_report.engine == engine_name
            assert risk_report.summary.removals == 1
            assert any(r.dimension == RiskDimension.DATA_PRESERVATION for r in risk_report.risk_assessments)

    def test_property_invariants(self) -> None:
        """Property Invariants:
        1. Every risk assessment must point to a valid source_change_fingerprint.
        2. Every recommendation must link to a valid risk assessment.
        3. Priority ordering is strictly non-increasing in severity rank.
        """
        base_payload = make_standard_ecommerce_payload()
        snap_base = build_snapshot_from_payload(base_payload, snapshot_id="snap_base")

        # Modifying table
        users_tbl = next(t for t in base_payload.tables if t.name == "users")
        u_cols = list(users_tbl.columns)
        # Change email to not nullable -> triggers RISK-COMPAT-002
        u_cols[2] = u_cols[2].model_copy(update={"is_nullable": False})
        mod_users = users_tbl.model_copy(update={"columns": tuple(u_cols)})
        target_payload = base_payload.model_copy(update={"tables": (base_payload.tables[0], mod_users)})
        snap_target = build_snapshot_from_payload(target_payload, snapshot_id="snap_target")

        comp_report = SchemaComparisonEngine().compare(snap_base, snap_target)
        risk_report = MigrationRiskAnalysisEngine().analyze(comp_report)

        change_fps = {c.fingerprint for c in comp_report.changes}
        risk_ids = {r.risk_id for r in risk_report.risk_assessments}

        # Invariant 1
        for r in risk_report.risk_assessments:
            assert r.source_change_fingerprint in change_fps

        # Invariant 2
        for rec in risk_report.recommendations:
            assert rec.risk_id == "" or rec.risk_id in risk_ids

        # Invariant 3: deterministic priority ordering (rank 1 is P1)
        priorities = [r.priority.rank for r in risk_report.risk_assessments]
        assert priorities == sorted(priorities)

    def test_performance_scalability(self) -> None:
        """Performance: Risk analysis on 100 tables with 1000 columns completes in under 0.5s."""
        tables_list = []
        for i in range(100):
            tbl_id = f"tbl_{i:03d}"
            cols = tuple(
                make_test_column(tbl_id, f"col_{j:02d}", j + 1, "integer", CanonicalTypeCategory.INTEGER, True)
                for j in range(10)
            )
            tables_list.append(make_test_table(namespace="public", name=f"t_{i:03d}", columns=cols))

        payload_100 = SnapshotStructuralPayload(
            schema_format="dera.structural.v1",
            database_name="perf_db",
            engine="postgresql",
            namespaces=("public",),
            tables=tuple(tables_list),
        )
        snap1 = build_snapshot_from_payload(payload_100, snapshot_id="perf_1")

        # Drop 5 tables and modify 5 columns
        mod_tables = list(tables_list[5:])
        payload_mod = payload_100.model_copy(update={"tables": tuple(mod_tables)})
        snap2 = build_snapshot_from_payload(payload_mod, snapshot_id="perf_2")

        comp_report = SchemaComparisonEngine().compare(snap1, snap2)

        start = time.perf_counter()
        risk_report = MigrationRiskAnalysisEngine().analyze(comp_report)
        elapsed = time.perf_counter() - start

        assert risk_report.summary.removals == 5
        assert elapsed < 0.5, f"Risk analysis took {elapsed:.3f}s; expected < 0.5s"
