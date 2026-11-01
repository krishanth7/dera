"""Unit and Behavioral Tests for Phase 9.1 Schema Comparison Engine."""

from __future__ import annotations

import pytest

from dera.comparison.engine import SchemaComparisonEngine
from dera.comparison.enums import (
    ComparisonChangeType,
    ComparisonObjectType,
    ComparisonStatus,
    PropertyComparisonStatus,
)
from dera.comparison.errors import (
    ComparisonResourceLimitExceededError,
    IncompatibleSnapshotError,
    InvalidSnapshotError,
    UnsupportedEngineComparisonError,
)
from dera.comparison.limits import ComparisonResourceLimits
from dera.comparison.models import ComparisonConfig
from dera.comparison.tests.fixtures import (
    build_snapshot_from_payload,
    make_standard_ecommerce_payload,
    make_test_column,
    make_test_table,
)
from dera.metadata.enums import CanonicalTypeCategory, MetadataCompleteness, TableType
from dera.metadata.identity import compute_stable_object_id
from dera.reverse_engineering.snapshots.models import (
    SnapshotIndexPayload,
    SnapshotPrimaryKeyPayload,
    SnapshotStructuralPayload,
    SnapshotUniqueConstraintPayload,
    SnapshotViewPayload,
)


class TestComparisonEngineUnit:
    """Test suite for Phase 9.1 deterministic schema comparison engine."""

    def test_identical_snapshots_return_empty_diff_fast_path(self) -> None:
        """Fast-path verification: identical snapshots produce 0 diffs and IDENTICAL status."""
        payload = make_standard_ecommerce_payload()
        snap1 = build_snapshot_from_payload(payload, snapshot_id="snap_1")
        snap2 = build_snapshot_from_payload(payload, snapshot_id="snap_2")

        engine = SchemaComparisonEngine()
        report = engine.compare(snap1, snap2)

        assert report.status == ComparisonStatus.IDENTICAL
        assert report.summary.total_changes == 0
        assert report.summary.total_added == 0
        assert report.summary.total_removed == 0
        assert report.summary.total_modified == 0
        assert len(report.changes) == 0
        assert report.baseline_fingerprint == snap1.fingerprint
        assert report.target_fingerprint == snap2.fingerprint
        assert report.report_fingerprint != ""

    def test_table_addition_and_removal(self) -> None:
        """Verify table addition and removal detection with evidence."""
        base_payload = make_standard_ecommerce_payload()
        snap_base = build_snapshot_from_payload(base_payload, snapshot_id="snap_base")

        # Create target by removing 'orders' table
        target_tables = tuple(t for t in base_payload.tables if t.name != "orders")
        target_payload = base_payload.model_copy(update={"tables": target_tables, "relationships": ()})
        snap_target = build_snapshot_from_payload(target_payload, snapshot_id="snap_target")

        engine = SchemaComparisonEngine()

        # Base -> Target (orders removed)
        report_fwd = engine.compare(snap_base, snap_target)
        assert report_fwd.status == ComparisonStatus.DIFFERENCES_FOUND
        table_changes = [c for c in report_fwd.changes if c.object_type == ComparisonObjectType.TABLE]
        assert len(table_changes) == 1
        assert table_changes[0].name == "orders"
        assert table_changes[0].change_type == ComparisonChangeType.REMOVED
        assert table_changes[0].before_evidence is not None
        assert table_changes[0].after_evidence is None

        # Target -> Base (orders added, relationship added)
        report_rev = engine.compare(snap_target, snap_base)
        assert report_rev.status == ComparisonStatus.DIFFERENCES_FOUND
        rev_table_changes = [c for c in report_rev.changes if c.object_type == ComparisonObjectType.TABLE]
        assert len(rev_table_changes) == 1
        assert rev_table_changes[0].name == "orders"
        assert rev_table_changes[0].change_type == ComparisonChangeType.ADDED
        assert rev_table_changes[0].before_evidence is None
        assert rev_table_changes[0].after_evidence is not None

    def test_column_property_modifications(self) -> None:
        """Verify type change, nullability change, and default value modifications."""
        base_payload = make_standard_ecommerce_payload()
        snap_base = build_snapshot_from_payload(base_payload, snapshot_id="snap_base")

        # Modify users table: name column becomes non-nullable and varchar(100)
        users_table = next(t for t in base_payload.tables if t.name == "users")
        new_cols = []
        for c in users_table.columns:
            if c.name == "name":
                new_c = c.model_copy(
                    update={
                        "is_nullable": False,
                        "native_data_type": "varchar(100)",
                        "default_expression": "'Anonymous'",
                    }
                )
                new_cols.append(new_c)
            else:
                new_cols.append(c)

        mod_users = users_table.model_copy(update={"columns": tuple(new_cols)})
        other_tables = [t for t in base_payload.tables if t.name != "users"]
        target_payload = base_payload.model_copy(update={"tables": tuple(other_tables + [mod_users])})
        snap_target = build_snapshot_from_payload(target_payload, snapshot_id="snap_target")

        engine = SchemaComparisonEngine()
        report = engine.compare(snap_base, snap_target)

        assert report.status == ComparisonStatus.DIFFERENCES_FOUND
        col_changes = [c for c in report.changes if c.object_type == ComparisonObjectType.COLUMN and c.name == "name"]
        assert len(col_changes) == 1
        chg = col_changes[0]
        assert chg.change_type == ComparisonChangeType.MODIFIED
        assert chg.parent_name == "users"

        prop_map = {p.property_name: p for p in chg.property_differences}
        assert "is_nullable" in prop_map
        assert prop_map["is_nullable"].before_value is True
        assert prop_map["is_nullable"].after_value is False

        assert "native_data_type" in prop_map
        assert prop_map["native_data_type"].before_value == "text"
        assert prop_map["native_data_type"].after_value == "varchar(100)"

        assert "default_expression" in prop_map
        assert prop_map["default_expression"].before_value is None
        assert prop_map["default_expression"].after_value == "'Anonymous'"

    def test_column_addition_and_removal(self) -> None:
        """Verify column addition and removal in an existing table."""
        base_payload = make_standard_ecommerce_payload()
        snap_base = build_snapshot_from_payload(base_payload, snapshot_id="snap_base")

        users_table = next(t for t in base_payload.tables if t.name == "users")
        new_col = make_test_column(
            table_id=users_table.table_id,
            name="avatar_url",
            ordinal=5,
            native_type="text",
            canonical_type=CanonicalTypeCategory.TEXT,
            is_nullable=True,
        )
        mod_users = users_table.model_copy(update={"columns": users_table.columns + (new_col,)})
        other_tables = [t for t in base_payload.tables if t.name != "users"]
        target_payload = base_payload.model_copy(update={"tables": tuple(other_tables + [mod_users])})
        snap_target = build_snapshot_from_payload(target_payload, snapshot_id="snap_target")

        engine = SchemaComparisonEngine()
        report = engine.compare(snap_base, snap_target)

        col_changes = [c for c in report.changes if c.object_type == ComparisonObjectType.COLUMN and c.name == "avatar_url"]
        assert len(col_changes) == 1
        assert col_changes[0].change_type == ComparisonChangeType.ADDED
        assert col_changes[0].after_evidence is not None

    def test_primary_key_and_unique_constraint_differences(self) -> None:
        """Verify primary key modifications and unique constraint additions."""
        base_payload = make_standard_ecommerce_payload()
        snap_base = build_snapshot_from_payload(base_payload, snapshot_id="snap_base")

        users_table = next(t for t in base_payload.tables if t.name == "users")
        # Change PK columns to ("id", "email") and add a unique constraint
        mod_pk = users_table.primary_key.model_copy(update={"columns": ("id", "email")})
        new_uc = SnapshotUniqueConstraintPayload(
            constraint_id="uc_users_email",
            name="unq_users_email",
            columns=("email",),
        )
        mod_users = users_table.model_copy(
            update={
                "primary_key": mod_pk,
                "unique_constraints": (new_uc,),
            }
        )
        other_tables = [t for t in base_payload.tables if t.name != "users"]
        target_payload = base_payload.model_copy(update={"tables": tuple(other_tables + [mod_users])})
        snap_target = build_snapshot_from_payload(target_payload, snapshot_id="snap_target")

        engine = SchemaComparisonEngine()
        report = engine.compare(snap_base, snap_target)

        # PK modified
        pk_changes = [c for c in report.changes if c.object_type == ComparisonObjectType.PRIMARY_KEY]
        assert len(pk_changes) == 1
        assert pk_changes[0].change_type == ComparisonChangeType.MODIFIED
        assert pk_changes[0].property_differences[0].property_name == "columns"

        # Unique constraint added
        uc_changes = [c for c in report.changes if c.object_type == ComparisonObjectType.UNIQUE_CONSTRAINT]
        assert len(uc_changes) == 1
        assert uc_changes[0].change_type == ComparisonChangeType.ADDED
        assert uc_changes[0].name == "unq_users_email"

    def test_foreign_key_and_relationship_differences(self) -> None:
        """Verify foreign key removal and relationship edge diffs."""
        base_payload = make_standard_ecommerce_payload()
        snap_base = build_snapshot_from_payload(base_payload, snapshot_id="snap_base")

        orders_table = next(t for t in base_payload.tables if t.name == "orders")
        mod_orders = orders_table.model_copy(update={"foreign_keys": ()})
        other_tables = [t for t in base_payload.tables if t.name != "orders"]
        target_payload = base_payload.model_copy(
            update={
                "tables": tuple(other_tables + [mod_orders]),
                "relationships": (),
            }
        )
        snap_target = build_snapshot_from_payload(target_payload, snapshot_id="snap_target")

        engine = SchemaComparisonEngine()
        report = engine.compare(snap_base, snap_target)

        fk_changes = [c for c in report.changes if c.object_type == ComparisonObjectType.FOREIGN_KEY]
        assert len(fk_changes) == 1
        assert fk_changes[0].change_type == ComparisonChangeType.REMOVED

        rel_changes = [c for c in report.changes if c.object_type == ComparisonObjectType.RELATIONSHIP]
        assert len(rel_changes) == 1
        assert rel_changes[0].change_type == ComparisonChangeType.REMOVED

    def test_index_modifications(self) -> None:
        """Verify index property changes (unique, predicate, index_type)."""
        base_payload = make_standard_ecommerce_payload()
        snap_base = build_snapshot_from_payload(base_payload, snapshot_id="snap_base")

        users_table = next(t for t in base_payload.tables if t.name == "users")
        old_idx = users_table.indexes[0]
        mod_idx = old_idx.model_copy(
            update={
                "index_type": "HASH",
                "predicate": "email IS NOT NULL",
            }
        )
        mod_users = users_table.model_copy(update={"indexes": (mod_idx,)})
        other_tables = [t for t in base_payload.tables if t.name != "users"]
        target_payload = base_payload.model_copy(update={"tables": tuple(other_tables + [mod_users])})
        snap_target = build_snapshot_from_payload(target_payload, snapshot_id="snap_target")

        engine = SchemaComparisonEngine()
        report = engine.compare(snap_base, snap_target)

        idx_changes = [c for c in report.changes if c.object_type == ComparisonObjectType.INDEX]
        assert len(idx_changes) == 1
        assert idx_changes[0].change_type == ComparisonChangeType.MODIFIED
        diff_prop_names = {p.property_name for p in idx_changes[0].property_differences}
        assert "index_type" in diff_prop_names
        assert "predicate" in diff_prop_names

    def test_view_definition_changes(self) -> None:
        """Verify view definition and materialized property comparisons."""
        base_payload = make_standard_ecommerce_payload()
        snap_base = build_snapshot_from_payload(base_payload, snapshot_id="snap_base")

        old_view = base_payload.views[0]
        mod_view = old_view.model_copy(
            update={
                "definition": "SELECT id, status, total FROM orders WHERE total > 100",
                "is_materialized": True,
            }
        )
        target_payload = base_payload.model_copy(update={"views": (mod_view,)})
        snap_target = build_snapshot_from_payload(target_payload, snapshot_id="snap_target")

        engine = SchemaComparisonEngine()
        report = engine.compare(snap_base, snap_target)

        vw_changes = [c for c in report.changes if c.object_type == ComparisonObjectType.VIEW]
        assert len(vw_changes) == 1
        assert vw_changes[0].change_type == ComparisonChangeType.MODIFIED
        diff_prop_names = {p.property_name for p in vw_changes[0].property_differences}
        assert "definition" in diff_prop_names
        assert "is_materialized" in diff_prop_names

    def test_namespace_addition_and_removal(self) -> None:
        """Verify schema / namespace level additions and removals."""
        base_payload = make_standard_ecommerce_payload()
        snap_base = build_snapshot_from_payload(base_payload, snapshot_id="snap_base")

        target_payload = base_payload.model_copy(update={"namespaces": ("public", "analytics")})
        snap_target = build_snapshot_from_payload(target_payload, snapshot_id="snap_target")

        engine = SchemaComparisonEngine()
        report = engine.compare(snap_base, snap_target)

        ns_changes = [c for c in report.changes if c.object_type == ComparisonObjectType.NAMESPACE]
        assert len(ns_changes) == 1
        assert ns_changes[0].name == "analytics"
        assert ns_changes[0].change_type == ComparisonChangeType.ADDED

    def test_cross_engine_compatibility_policy(self) -> None:
        """Verify cross-engine policies: PostgreSQL <-> Supabase allowed, PostgreSQL <-> SQLite disallowed."""
        base_pg = make_standard_ecommerce_payload(engine="postgresql")
        snap_pg = build_snapshot_from_payload(base_pg, snapshot_id="snap_pg")

        target_supa = make_standard_ecommerce_payload(engine="supabase")
        snap_supa = build_snapshot_from_payload(target_supa, snapshot_id="snap_supa")

        target_sqlite = make_standard_ecommerce_payload(engine="sqlite")
        snap_sqlite = build_snapshot_from_payload(target_sqlite, snapshot_id="snap_sqlite")

        engine = SchemaComparisonEngine()

        # PG -> Supabase is allowed under compatible engine family policy
        report = engine.compare(snap_pg, snap_supa)
        assert report.engine == "postgresql"
        assert report.target_engine == "supabase"
        assert any("postgres_family" in note for note in report.metadata_limitations)

        # PG -> SQLite raises UnsupportedEngineComparisonError
        with pytest.raises(UnsupportedEngineComparisonError) as exc_info:
            engine.compare(snap_pg, snap_sqlite)
        assert exc_info.value.baseline_engine == "postgresql"
        assert exc_info.value.target_engine == "sqlite"

    def test_resource_limits_enforced(self) -> None:
        """Verify resource bounding stops execution on oversized inputs."""
        base_payload = make_standard_ecommerce_payload()
        snap_base = build_snapshot_from_payload(base_payload, snapshot_id="snap_base")
        snap_target = build_snapshot_from_payload(base_payload, snapshot_id="snap_target")

        strict_limits = ComparisonResourceLimits(max_tables=1)
        engine = SchemaComparisonEngine(limits=strict_limits)

        with pytest.raises(ComparisonResourceLimitExceededError) as exc_info:
            engine.compare(snap_base, snap_target)
        assert exc_info.value.limit_name == "max_tables"

    def test_deterministic_ordering_invariant(self) -> None:
        """Verify that regardless of change extraction order, comparison output is deterministically ordered and fingerprinted."""
        base_payload = make_standard_ecommerce_payload()
        snap_base = build_snapshot_from_payload(base_payload, snapshot_id="snap_base")

        # Create target with multiple additions and modifications
        orders_tbl = next(t for t in base_payload.tables if t.name == "orders")
        users_tbl = next(t for t in base_payload.tables if t.name == "users")

        # Modify both tables
        mod_orders = orders_tbl.model_copy(update={"comment": "Orders table comment"})
        mod_users = users_tbl.model_copy(update={"comment": "Users table comment"})

        # Canonical ordering has tables sorted by (namespace, name): orders then users
        t_payload = base_payload.model_copy(update={"tables": (orders_tbl, mod_users)})
        snap_target = build_snapshot_from_payload(t_payload, snapshot_id="snap_target")

        engine = SchemaComparisonEngine()
        report_1 = engine.compare(snap_base, snap_target)
        report_2 = engine.compare(snap_base, snap_target)

        assert report_1.report_fingerprint == report_2.report_fingerprint
        assert len(report_1.changes) == len(report_2.changes)
        for c1, c2 in zip(report_1.changes, report_2.changes, strict=True):
            assert c1.fingerprint == c2.fingerprint
            assert c1.change_id == c2.change_id
