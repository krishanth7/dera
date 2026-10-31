"""Unit and integration tests for Phase 8.2 Constraint Diagnostic Rules (DERA-CON-001 through 005)."""

from __future__ import annotations

from dataclasses import dataclass, field

from dera.diagnostics.context import DiagnosticContext
from dera.diagnostics.enums import (
    DiagnosticSeverity,
    EvaluationStatus,
)
from dera.diagnostics.rules.constraints import (
    CheckConstraintMetadataRule,
    ConstraintColumnIntegrityRule,
    ForeignKeyIntegrityRule,
    PrimaryKeyIntegrityRule,
    UniqueConstraintIntegrityRule,
)


@dataclass
class MockColumn:
    name: str
    object_id: str = "col_id"


@dataclass
class MockPK:
    name: str = "pk"
    id: str = "pk_id"
    columns: tuple[str, ...] = ()


@dataclass
class MockFK:
    name: str = "fk"
    id: str = "fk_id"
    source_columns: tuple[str, ...] = ()
    referenced_table_name: str = "parent_table"
    referenced_columns: tuple[str, ...] = ()
    referenced_schema: str | None = None


@dataclass
class MockUQ:
    name: str = "uq"
    id: str = "uq_id"
    columns: tuple[str, ...] = ()


@dataclass
class MockCK:
    name: str = "ck"
    id: str = "ck_id"
    check_clause: str | None = None


@dataclass
class MockTable:
    name: str
    id: str = "tbl_id"
    schema_name: str | None = None
    columns: tuple[MockColumn, ...] = field(default_factory=tuple)
    primary_key: MockPK | None = None
    foreign_keys: tuple[MockFK, ...] = field(default_factory=tuple)
    unique_constraints: tuple[MockUQ, ...] = field(default_factory=tuple)
    check_constraints: tuple[MockCK, ...] = field(default_factory=tuple)
    indexes: tuple = field(default_factory=tuple)


@dataclass
class MockSchema:
    tables: tuple[MockTable, ...] = field(default_factory=tuple)


class TestPrimaryKeyIntegrityRule:
    """Tests for DERA-CON-001: Primary Key Structural Integrity."""

    def test_table_without_pk_is_not_penalized(self) -> None:
        table = MockTable(name="audit_logs", columns=(MockColumn(name="payload"),))
        context = DiagnosticContext(schema=MockSchema(tables=(table,)))
        rule = PrimaryKeyIntegrityRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.PASS
        assert len(res.findings) == 0

    def test_detects_empty_primary_key(self) -> None:
        table = MockTable(
            name="users",
            columns=(MockColumn(name="id"),),
            primary_key=MockPK(name="pk_users", columns=()),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)))
        rule = PrimaryKeyIntegrityRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.FINDINGS_DETECTED
        assert len(res.findings) == 1
        assert res.findings[0].rule_id == "DERA-CON-001"
        assert res.findings[0].severity == DiagnosticSeverity.HIGH
        assert "Empty primary key" in res.findings[0].title

    def test_detects_duplicate_column_in_primary_key(self) -> None:
        table = MockTable(
            name="composite_tbl",
            columns=(MockColumn(name="tenant_id"), MockColumn(name="user_id")),
            primary_key=MockPK(name="pk_comp", columns=("tenant_id", "tenant_id")),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)))
        rule = PrimaryKeyIntegrityRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.FINDINGS_DETECTED
        assert len(res.findings) == 1
        assert "Duplicate column" in res.findings[0].title
        assert res.findings[0].severity == DiagnosticSeverity.MEDIUM

    def test_detects_pk_referencing_missing_column(self) -> None:
        table = MockTable(
            name="items",
            columns=(MockColumn(name="item_id"),),
            primary_key=MockPK(name="pk_items", columns=("missing_id",)),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)))
        rule = PrimaryKeyIntegrityRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.FINDINGS_DETECTED
        assert len(res.findings) == 1
        assert "non-existent column" in res.findings[0].title


class TestForeignKeyIntegrityRule:
    """Tests for DERA-CON-002: Foreign Key Referential Mapping Integrity."""

    def test_detects_missing_child_columns(self) -> None:
        table = MockTable(
            name="orders",
            columns=(MockColumn(name="id"),),
            foreign_keys=(
                MockFK(
                    name="fk_orders_cust",
                    source_columns=("customer_id",),
                    referenced_table_name="customers",
                    referenced_columns=("id",),
                ),
            ),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)))
        rule = ForeignKeyIntegrityRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.FINDINGS_DETECTED
        findings = [f for f in res.findings if "child columns missing" in f.title]
        assert len(findings) == 1
        assert findings[0].severity == DiagnosticSeverity.HIGH

    def test_detects_column_count_mismatch(self) -> None:
        table = MockTable(
            name="items",
            columns=(MockColumn(name="store_id"), MockColumn(name="sku")),
            foreign_keys=(
                MockFK(
                    name="fk_mismatch",
                    source_columns=("store_id", "sku"),
                    referenced_table_name="inventory",
                    referenced_columns=("sku",),
                ),
            ),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)))
        rule = ForeignKeyIntegrityRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.FINDINGS_DETECTED
        mismatch_findings = [f for f in res.findings if "count mismatch" in f.title]
        assert len(mismatch_findings) == 1
        assert mismatch_findings[0].severity == DiagnosticSeverity.HIGH

    def test_detects_missing_target_columns_when_parent_exists(self) -> None:
        child = MockTable(
            name="orders",
            columns=(MockColumn(name="customer_id"),),
            foreign_keys=(
                MockFK(
                    name="fk_orders_cust",
                    source_columns=("customer_id",),
                    referenced_table_name="customers",
                    referenced_columns=("non_existent_id",),
                ),
            ),
        )
        parent = MockTable(
            name="customers",
            columns=(MockColumn(name="id"), MockColumn(name="name")),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(child, parent)))
        rule = ForeignKeyIntegrityRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.FINDINGS_DETECTED
        parent_col_findings = [
            f for f in res.findings if "Referenced parent columns missing" in f.title
        ]
        assert len(parent_col_findings) == 1
        assert parent_col_findings[0].severity == DiagnosticSeverity.HIGH

    def test_reports_low_severity_for_uninspected_external_table(self) -> None:
        child = MockTable(
            name="orders",
            columns=(MockColumn(name="customer_id"),),
            foreign_keys=(
                MockFK(
                    name="fk_orders_ext",
                    source_columns=("customer_id",),
                    referenced_table_name="external_customers",
                    referenced_columns=("id",),
                ),
            ),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(child,)))
        rule = ForeignKeyIntegrityRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.FINDINGS_DETECTED
        unres_findings = [
            f for f in res.findings if "Unresolved referenced parent table" in f.title
        ]
        assert len(unres_findings) == 1
        assert unres_findings[0].severity == DiagnosticSeverity.LOW

    def test_explicit_referenced_schema_does_not_fall_back_to_unrelated_schema(self) -> None:
        """When a foreign key specifies an explicit schema, it must not match an unrelated schema."""
        child = MockTable(
            name="orders",
            columns=(MockColumn(name="customer_id"),),
            foreign_keys=(
                MockFK(
                    name="fk_orders_ext",
                    source_columns=("customer_id",),
                    referenced_schema="uninspected",
                    referenced_table_name="customers",
                    referenced_columns=("id",),
                ),
            ),
        )
        # An unrelated customers table in the 'public' schema exists
        unrelated_parent = MockTable(
            name="customers",
            schema_name="public",
            columns=(MockColumn(name="other_id"),),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(child, unrelated_parent)))
        rule = ForeignKeyIntegrityRule()
        res = rule.evaluate(context)

        # Must be treated as unresolved referenced parent table (LOW severity), NOT missing columns on public.customers
        unres_findings = [
            f for f in res.findings if "Unresolved referenced parent table" in f.title
        ]
        assert len(unres_findings) == 1
        assert unres_findings[0].severity == DiagnosticSeverity.LOW
        assert "Unresolved referenced parent table" in unres_findings[0].title
        assert "customers" in unres_findings[0].description

    def test_supports_self_referencing_foreign_keys(self) -> None:
        org_chart = MockTable(
            name="employees",
            columns=(MockColumn(name="id"), MockColumn(name="manager_id")),
            foreign_keys=(
                MockFK(
                    name="fk_manager",
                    source_columns=("manager_id",),
                    referenced_table_name="employees",
                    referenced_columns=("id",),
                ),
            ),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(org_chart,)))
        rule = ForeignKeyIntegrityRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.PASS
        assert len(res.findings) == 0


class TestUniqueConstraintIntegrityRule:
    """Tests for DERA-CON-003: Unique Constraint Structural Integrity."""

    def test_detects_empty_unique_constraint(self) -> None:
        table = MockTable(
            name="users",
            columns=(MockColumn(name="email"),),
            unique_constraints=(MockUQ(name="uq_empty", columns=()),),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)))
        rule = UniqueConstraintIntegrityRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.FINDINGS_DETECTED
        assert len(res.findings) == 1
        assert "Empty unique constraint" in res.findings[0].title
        assert res.findings[0].severity == DiagnosticSeverity.HIGH

    def test_detects_unique_constraint_duplicating_primary_key(self) -> None:
        table = MockTable(
            name="users",
            columns=(MockColumn(name="id"), MockColumn(name="email")),
            primary_key=MockPK(name="pk_users", columns=("id",)),
            unique_constraints=(MockUQ(name="uq_id", columns=("id",)),),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)))
        rule = UniqueConstraintIntegrityRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.FINDINGS_DETECTED
        assert len(res.findings) == 1
        assert "duplicates primary key" in res.findings[0].title
        assert res.findings[0].severity == DiagnosticSeverity.LOW

    def test_detects_duplicate_unique_constraints(self) -> None:
        table = MockTable(
            name="users",
            columns=(MockColumn(name="email"),),
            unique_constraints=(
                MockUQ(name="uq_email_1", id="uq_1", columns=("email",)),
                MockUQ(name="uq_email_2", id="uq_2", columns=("email",)),
            ),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)))
        rule = UniqueConstraintIntegrityRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.FINDINGS_DETECTED
        assert len(res.findings) == 1
        assert "Duplicate unique constraint" in res.findings[0].title
        assert res.findings[0].severity == DiagnosticSeverity.MEDIUM


class TestCheckConstraintMetadataRule:
    """Tests for DERA-CON-004: Check Constraint Metadata Integrity."""

    def test_detects_empty_check_clause(self) -> None:
        table = MockTable(
            name="products",
            columns=(MockColumn(name="price"),),
            check_constraints=(MockCK(name="ck_price_positive", check_clause=""),),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)), source_engine="postgresql")
        rule = CheckConstraintMetadataRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.FINDINGS_DETECTED
        assert len(res.findings) == 1
        assert "Empty check constraint clause" in res.findings[0].title
        assert res.findings[0].severity == DiagnosticSeverity.HIGH

    def test_passes_valid_check_constraint(self) -> None:
        table = MockTable(
            name="products",
            columns=(MockColumn(name="price"),),
            check_constraints=(MockCK(name="ck_price", check_clause="price > 0"),),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)), source_engine="postgresql")
        rule = CheckConstraintMetadataRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.PASS
        assert len(res.findings) == 0


class TestConstraintColumnIntegrityRule:
    """Tests for DERA-CON-005: Constraint Column Integrity."""

    def test_detects_missing_columns_across_all_constraint_types(self) -> None:
        table = MockTable(
            name="orders",
            columns=(MockColumn(name="id"), MockColumn(name="customer_id")),
            primary_key=MockPK(name="pk_orders", columns=("missing_pk_col",)),
            unique_constraints=(MockUQ(name="uq_orders", columns=("missing_uq_col",)),),
            foreign_keys=(
                MockFK(
                    name="fk_orders",
                    source_columns=("missing_fk_col",),
                    referenced_table_name="customers",
                    referenced_columns=("id",),
                ),
            ),
        )
        context = DiagnosticContext(schema=MockSchema(tables=(table,)))
        rule = ConstraintColumnIntegrityRule()
        res = rule.evaluate(context)

        assert res.status == EvaluationStatus.FINDINGS_DETECTED
        assert len(res.findings) == 3
        for f in res.findings:
            assert f.rule_id == "DERA-CON-005"
            assert f.severity == DiagnosticSeverity.HIGH
