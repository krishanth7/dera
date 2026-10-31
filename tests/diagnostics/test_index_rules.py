"""Unit and integration tests for Phase 8.2 Index Diagnostic Rules (DERA-IDX-001 through 004)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dera.diagnostics.context import DiagnosticContext
from dera.diagnostics.enums import (
    DiagnosticSeverity,
    EvaluationStatus,
)
from dera.diagnostics.rules.indexes import (
    DuplicateIndexesRule,
    FkIndexCoverageRule,
    IndexColumnIntegrityRule,
    RedundantIndexesRule,
)


@dataclass
class MockColumn:
    name: str
    object_id: str = "col_id"


@dataclass
class MockIndexTerm:
    column_name: str | None = None
    expression: str | None = None
    ordinal_position: int = 1
    is_descending: bool = False
    nulls_first: bool = False
    is_expression: bool = False


@dataclass
class MockIndex:
    name: str
    id: str = "idx_id"
    parent_table_id: str = "tbl_id"
    is_unique: bool = False
    is_primary: bool = False
    index_type: str = "BTREE"
    terms: tuple[MockIndexTerm, ...] = ()
    predicate: str | None = None


@dataclass
class MockForeignKey:
    name: str
    id: str = "fk_id"
    source_columns: tuple[str, ...] = ()
    referenced_table_name: str = "parent_table"
    referenced_columns: tuple[str, ...] = ()
    referenced_schema: str | None = None


@dataclass
class MockTable:
    name: str
    id: str = "tbl_id"
    columns: tuple[MockColumn, ...] = field(default_factory=tuple)
    indexes: tuple[MockIndex, ...] = field(default_factory=tuple)
    foreign_keys: tuple[MockForeignKey, ...] = field(default_factory=tuple)
    primary_key: Any = None
    unique_constraints: tuple = field(default_factory=tuple)


@dataclass
class MockSchema:
    tables: tuple[MockTable, ...] = field(default_factory=tuple)


class TestDuplicateIndexesRule:
    """Tests for DERA-IDX-001: Exact Duplicate Index Definition."""

    def test_detects_identical_indexes(self) -> None:
        table = MockTable(
            name="users",
            indexes=(
                MockIndex(
                    name="idx_users_email_1",
                    id="idx_1",
                    terms=(MockIndexTerm(column_name="email", ordinal_position=1),),
                ),
                MockIndex(
                    name="idx_users_email_2",
                    id="idx_2",
                    terms=(MockIndexTerm(column_name="email", ordinal_position=1),),
                ),
            ),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)))
        rule = DuplicateIndexesRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.FINDINGS_DETECTED
        assert len(res.findings) == 1
        f = res.findings[0]
        assert f.rule_id == "DERA-IDX-001"
        assert f.severity == DiagnosticSeverity.MEDIUM
        assert "idx_users_email_2" in f.title

    def test_ignores_different_index_types(self) -> None:
        table = MockTable(
            name="users",
            indexes=(
                MockIndex(
                    name="idx_btree",
                    id="idx_1",
                    index_type="BTREE",
                    terms=(MockIndexTerm(column_name="email", ordinal_position=1),),
                ),
                MockIndex(
                    name="idx_hash",
                    id="idx_2",
                    index_type="HASH",
                    terms=(MockIndexTerm(column_name="email", ordinal_position=1),),
                ),
            ),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)))
        rule = DuplicateIndexesRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.PASS
        assert len(res.findings) == 0

    def test_ignores_different_predicates(self) -> None:
        table = MockTable(
            name="orders",
            indexes=(
                MockIndex(
                    name="idx_active",
                    id="idx_1",
                    predicate="status = 'active'",
                    terms=(MockIndexTerm(column_name="created_at", ordinal_position=1),),
                ),
                MockIndex(
                    name="idx_all",
                    id="idx_2",
                    predicate=None,
                    terms=(MockIndexTerm(column_name="created_at", ordinal_position=1),),
                ),
            ),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)))
        rule = DuplicateIndexesRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.PASS


class TestRedundantIndexesRule:
    """Tests for DERA-IDX-002: Potentially Redundant B-Tree Index."""

    def test_detects_leftmost_prefix_candidate(self) -> None:
        table = MockTable(
            name="orders",
            indexes=(
                MockIndex(
                    name="idx_narrow",
                    id="idx_1",
                    terms=(MockIndexTerm(column_name="customer_id", ordinal_position=1),),
                ),
                MockIndex(
                    name="idx_wide",
                    id="idx_2",
                    terms=(
                        MockIndexTerm(column_name="customer_id", ordinal_position=1),
                        MockIndexTerm(column_name="created_at", ordinal_position=2),
                    ),
                ),
            ),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)))
        rule = RedundantIndexesRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.FINDINGS_DETECTED
        assert len(res.findings) == 1
        assert res.findings[0].rule_id == "DERA-IDX-002"
        assert res.findings[0].severity == DiagnosticSeverity.LOW

    def test_unique_narrow_index_not_redundant(self) -> None:
        table = MockTable(
            name="accounts",
            indexes=(
                MockIndex(
                    name="idx_unique_acc",
                    id="idx_1",
                    is_unique=True,
                    terms=(MockIndexTerm(column_name="account_number", ordinal_position=1),),
                ),
                MockIndex(
                    name="idx_composite_non_unique",
                    id="idx_2",
                    is_unique=False,
                    terms=(
                        MockIndexTerm(column_name="account_number", ordinal_position=1),
                        MockIndexTerm(column_name="branch_id", ordinal_position=2),
                    ),
                ),
            ),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)))
        rule = RedundantIndexesRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.PASS

    def test_non_btree_excluded_from_prefix(self) -> None:
        table = MockTable(
            name="metrics",
            indexes=(
                MockIndex(
                    name="idx_hash_narrow",
                    id="idx_1",
                    index_type="HASH",
                    terms=(MockIndexTerm(column_name="tag", ordinal_position=1),),
                ),
                MockIndex(
                    name="idx_hash_wide",
                    id="idx_2",
                    index_type="HASH",
                    terms=(
                        MockIndexTerm(column_name="tag", ordinal_position=1),
                        MockIndexTerm(column_name="ts", ordinal_position=2),
                    ),
                ),
            ),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)))
        rule = RedundantIndexesRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.PASS


class TestFkIndexCoverageRule:
    """Tests for DERA-IDX-003: Foreign Key Supporting Index Coverage."""

    def test_detects_unindexed_foreign_key_on_postgres(self) -> None:
        table = MockTable(
            name="orders",
            columns=(MockColumn(name="customer_id"),),
            foreign_keys=(
                MockForeignKey(
                    name="fk_orders_customer",
                    id="fk_1",
                    source_columns=("customer_id",),
                    referenced_table_name="customers",
                    referenced_columns=("id",),
                ),
            ),
            indexes=(),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)), source_engine="postgresql")
        rule = FkIndexCoverageRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.FINDINGS_DETECTED
        assert len(res.findings) == 1
        assert res.findings[0].rule_id == "DERA-IDX-003"
        assert res.findings[0].severity == DiagnosticSeverity.MEDIUM

    def test_passes_when_leading_prefix_index_exists(self) -> None:
        table = MockTable(
            name="orders",
            columns=(MockColumn(name="customer_id"), MockColumn(name="created_at")),
            foreign_keys=(
                MockForeignKey(
                    name="fk_orders_customer",
                    id="fk_1",
                    source_columns=("customer_id",),
                    referenced_table_name="customers",
                    referenced_columns=("id",),
                ),
            ),
            indexes=(
                MockIndex(
                    name="idx_cust_date",
                    id="idx_1",
                    terms=(
                        MockIndexTerm(column_name="customer_id", ordinal_position=1),
                        MockIndexTerm(column_name="created_at", ordinal_position=2),
                    ),
                ),
            ),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)), source_engine="postgresql")
        rule = FkIndexCoverageRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.PASS

    def test_mysql_not_applicable_due_to_innodb_auto_index(self) -> None:
        table = MockTable(
            name="orders",
            foreign_keys=(
                MockForeignKey(
                    name="fk_orders_customer",
                    id="fk_1",
                    source_columns=("customer_id",),
                    referenced_table_name="customers",
                    referenced_columns=("id",),
                ),
            ),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)), source_engine="mysql")
        rule = FkIndexCoverageRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.NOT_APPLICABLE


class TestIndexColumnIntegrityRule:
    """Tests for DERA-IDX-004: Index Column Reference Integrity."""

    def test_detects_index_referencing_non_existent_column(self) -> None:
        table = MockTable(
            name="users",
            columns=(MockColumn(name="id"), MockColumn(name="email")),
            indexes=(
                MockIndex(
                    name="idx_users_deleted_col",
                    id="idx_1",
                    terms=(MockIndexTerm(column_name="deleted_at", ordinal_position=1),),
                ),
            ),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)))
        rule = IndexColumnIntegrityRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.FINDINGS_DETECTED
        assert len(res.findings) == 1
        assert res.findings[0].rule_id == "DERA-IDX-004"
        assert res.findings[0].severity == DiagnosticSeverity.HIGH
        assert "deleted_at" in res.findings[0].description

    def test_passes_when_all_columns_exist(self) -> None:
        table = MockTable(
            name="users",
            columns=(MockColumn(name="id"), MockColumn(name="email")),
            indexes=(
                MockIndex(
                    name="idx_users_email",
                    id="idx_1",
                    terms=(MockIndexTerm(column_name="email", ordinal_position=1),),
                ),
            ),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)))
        rule = IndexColumnIntegrityRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.PASS
