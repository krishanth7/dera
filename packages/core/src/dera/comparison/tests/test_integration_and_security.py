"""Integration, Determinism, Reversibility, Security, and Scalability Tests for Phase 9.1 Comparison Engine."""

from __future__ import annotations

import time

import pytest
from dera.comparison.engine import SchemaComparisonEngine
from dera.comparison.enums import (
    ComparisonChangeType,
    ComparisonObjectType,
    ComparisonStatus,
)
from dera.comparison.errors import InvalidSnapshotError
from dera.comparison.models import ComparisonConfig
from dera.comparison.serializers import dumps_canonical_json
from dera.comparison.tests.fixtures import (
    build_snapshot_from_payload,
    make_standard_ecommerce_payload,
    make_test_column,
    make_test_table,
)
from dera.metadata.enums import CanonicalTypeCategory, MetadataCompleteness
from dera.reverse_engineering.snapshots.models import SnapshotStructuralPayload


class TestComparisonIntegrationAndProperties:
    """Comprehensive qualification test suite for Phase 9.1."""

    def test_reversibility_invariant(self) -> None:
        """Property Invariant: Comparing A -> B and B -> A should mirror additions and removals."""
        base_payload = make_standard_ecommerce_payload()
        snap_a = build_snapshot_from_payload(base_payload, snapshot_id="snap_a")

        # Create target B with one table added, one column removed
        users_table = next(t for t in base_payload.tables if t.name == "users")
        # Remove 'name' column from users
        mod_users_cols = tuple(c for c in users_table.columns if c.name != "name")
        mod_users = users_table.model_copy(update={"columns": mod_users_cols})

        # Add a new 'products' table
        products_table = make_test_table(
            namespace="public",
            name="products",
            columns=(
                make_test_column(
                    "tbl_prod", "id", 1, "integer", CanonicalTypeCategory.INTEGER, False
                ),
                make_test_column(
                    "tbl_prod", "sku", 2, "varchar(100)", CanonicalTypeCategory.TEXT, False
                ),
            ),
        )

        other_tables = [t for t in base_payload.tables if t.name != "users"]
        target_payload = base_payload.model_copy(
            update={"tables": tuple(other_tables + [mod_users, products_table])}
        )
        snap_b = build_snapshot_from_payload(target_payload, snapshot_id="snap_b")

        engine = SchemaComparisonEngine()
        report_ab = engine.compare(snap_a, snap_b)
        report_ba = engine.compare(snap_b, snap_a)

        assert report_ab.summary.total_added == report_ba.summary.total_removed
        assert report_ab.summary.total_removed == report_ba.summary.total_added
        assert report_ab.summary.total_modified == report_ba.summary.total_modified

        # Verify added products table in AB is removed table in BA
        prod_ab = next(
            c
            for c in report_ab.changes
            if c.object_type == ComparisonObjectType.TABLE and c.name == "products"
        )
        prod_ba = next(
            c
            for c in report_ba.changes
            if c.object_type == ComparisonObjectType.TABLE and c.name == "products"
        )
        assert prod_ab.change_type == ComparisonChangeType.ADDED
        assert prod_ba.change_type == ComparisonChangeType.REMOVED

    def test_configuration_filtering_namespaces_and_object_types(self) -> None:
        """Verify comparison filtering by included/excluded namespaces and object types."""
        base_payload = make_standard_ecommerce_payload()
        snap_base = build_snapshot_from_payload(base_payload, snapshot_id="snap_base")

        # Target adds table in public and table in analytics
        t_public = make_test_table(namespace="public", name="pub_tbl")
        t_analytics = make_test_table(namespace="analytics", name="an_tbl")
        target_payload = base_payload.model_copy(
            update={
                "namespaces": ("public", "analytics"),
                "tables": base_payload.tables + (t_public, t_analytics),
            }
        )
        snap_target = build_snapshot_from_payload(target_payload, snapshot_id="snap_target")

        engine = SchemaComparisonEngine()

        # Filter: only public namespace
        config_ns = ComparisonConfig(included_namespaces=("public",))
        report_ns = engine.compare(snap_base, snap_target, config=config_ns)
        assert all(c.namespace == "public" for c in report_ns.changes if c.namespace)
        assert not any(c.name == "an_tbl" for c in report_ns.changes)

        # Filter: only tables (exclude namespaces and columns)
        config_types = ComparisonConfig(included_object_types=(ComparisonObjectType.TABLE,))
        report_types = engine.compare(snap_base, snap_target, config=config_types)
        assert all(c.object_type == ComparisonObjectType.TABLE for c in report_types.changes)

    def test_metadata_completeness_handling(self) -> None:
        """Verify partial or restricted metadata completeness records limitation notes."""
        base_payload = make_standard_ecommerce_payload(completeness=MetadataCompleteness.COMPLETE)
        snap_base = build_snapshot_from_payload(base_payload, snapshot_id="snap_base")

        target_payload = make_standard_ecommerce_payload(completeness=MetadataCompleteness.PARTIAL)
        snap_target = build_snapshot_from_payload(target_payload, snapshot_id="snap_target")

        engine = SchemaComparisonEngine()
        report = engine.compare(snap_base, snap_target)

        assert any("Metadata completeness mismatch" in note for note in report.metadata_limitations)

    def test_large_schema_scalability(self) -> None:
        """Performance & Scalability: Compare schemas with 100 tables and 1000 columns."""
        tables_list = []
        for i in range(100):
            tbl_id = f"tbl_{i:03d}"
            cols = tuple(
                make_test_column(
                    tbl_id, f"col_{j:02d}", j + 1, "integer", CanonicalTypeCategory.INTEGER, True
                )
                for j in range(10)
            )
            tables_list.append(make_test_table(namespace="public", name=f"t_{i:03d}", columns=cols))

        payload_100 = SnapshotStructuralPayload(
            schema_format="dera.structural.v1",
            database_name="perf_db",
            engine="postgresql",
            namespaces=("public",),
            tables=tuple(tables_list),
            completeness=MetadataCompleteness.COMPLETE,
        )
        snap1 = build_snapshot_from_payload(payload_100, snapshot_id="perf_1")

        # Modify table 50: change a column type
        t50 = tables_list[50]
        mod_cols = list(t50.columns)
        mod_cols[0] = mod_cols[0].model_copy(update={"native_data_type": "bigint"})
        mod_t50 = t50.model_copy(update={"columns": tuple(mod_cols)})
        mod_tables = list(tables_list)
        mod_tables[50] = mod_t50

        payload_100_mod = payload_100.model_copy(update={"tables": tuple(mod_tables)})
        snap2 = build_snapshot_from_payload(payload_100_mod, snapshot_id="perf_2")

        start_time = time.perf_counter()
        engine = SchemaComparisonEngine()
        report = engine.compare(snap1, snap2)
        elapsed_s = time.perf_counter() - start_time

        assert report.status == ComparisonStatus.DIFFERENCES_FOUND
        assert report.summary.total_modified == 1
        assert report.summary.total_added == 0
        assert report.summary.total_removed == 0
        # Execution on 100 tables / 1000 columns must complete under 1.0 second
        assert elapsed_s < 1.0, f"Comparison took too long: {elapsed_s:.3f}s"

    def test_security_input_validation(self) -> None:
        """Security: Non-SchemaSnapshot inputs must be rejected immediately."""
        engine = SchemaComparisonEngine()
        with pytest.raises(InvalidSnapshotError):
            engine.compare(None, None)  # type: ignore[arg-type]

    def test_canonical_json_report_serialization(self) -> None:
        """Serialization: Reports must serialize deterministically to RFC 8785 JSON."""
        base_payload = make_standard_ecommerce_payload()
        snap1 = build_snapshot_from_payload(base_payload, snapshot_id="snap_1")
        snap2 = build_snapshot_from_payload(base_payload, snapshot_id="snap_2")

        engine = SchemaComparisonEngine()
        report = engine.compare(snap1, snap2)

        json_1 = dumps_canonical_json(report.model_dump(mode="json"))
        json_2 = dumps_canonical_json(report.model_dump(mode="json"))

        assert json_1 == json_2
        assert "report_fingerprint" in json_1
        assert "summary" in json_1
