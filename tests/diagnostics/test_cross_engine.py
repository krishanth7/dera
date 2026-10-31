"""Tests for DERA diagnostics across PostgreSQL, Supabase, SQLite, MySQL, and MariaDB fixtures."""

from __future__ import annotations

from dera.diagnostics.context import DiagnosticContext
from dera.diagnostics.evaluator import DiagnosticEvaluator
from dera.diagnostics.rules.foundational import ALL_FOUNDATIONAL_RULES
from dera.reverse_engineering.builder import SchemaBuilder

from tests.reverse_engineering.phase_6_1.fixtures import (
    build_enterprise_fixture,
    build_sqlite_fixture,
    build_unicode_and_case_sensitive_fixture,
)


def test_diagnostics_postgresql_enterprise() -> None:
    """Verifies diagnostic engine evaluation on PostgreSQL canonical schema."""
    canonical_db = build_enterprise_fixture(engine="postgresql", db_name="pg_enterprise")
    schema = SchemaBuilder.from_canonical_database(canonical_db)

    evaluator = DiagnosticEvaluator()
    context = DiagnosticContext(schema=schema)

    report = evaluator.evaluate(context, list(ALL_FOUNDATIONAL_RULES))

    assert report.source_engine == "postgresql"
    assert report.summary.total_rules_evaluated > 0
    assert report.summary.rules_errored == 0
    assert len(report.report_hash) == 64


def test_diagnostics_supabase_postgresql() -> None:
    """Verifies diagnostic engine evaluation on Supabase PostgreSQL canonical schema."""
    canonical_db = build_enterprise_fixture(engine="supabase", db_name="supabase_db")
    schema = SchemaBuilder.from_canonical_database(canonical_db)

    evaluator = DiagnosticEvaluator()
    context = DiagnosticContext(schema=schema)

    report = evaluator.evaluate(context, list(ALL_FOUNDATIONAL_RULES))

    assert report.source_engine == "supabase"
    assert report.summary.rules_errored == 0


def test_diagnostics_sqlite_schema() -> None:
    """Verifies diagnostic engine evaluation on SQLite canonical schema."""
    canonical_db = build_sqlite_fixture()
    schema = SchemaBuilder.from_canonical_database(canonical_db)

    evaluator = DiagnosticEvaluator()
    context = DiagnosticContext(schema=schema)

    report = evaluator.evaluate(context, list(ALL_FOUNDATIONAL_RULES))

    assert report.source_engine == "sqlite"
    assert report.summary.rules_errored == 0
    # Clean valid sqlite fixture should pass foundational rules
    assert report.summary.rules_passed > 0


def test_diagnostics_mysql_enterprise() -> None:
    """Verifies diagnostic engine evaluation on MySQL canonical schema."""
    canonical_db = build_enterprise_fixture(engine="mysql", db_name="mysql_db")
    schema = SchemaBuilder.from_canonical_database(canonical_db)

    evaluator = DiagnosticEvaluator()
    context = DiagnosticContext(schema=schema)

    report = evaluator.evaluate(context, list(ALL_FOUNDATIONAL_RULES))

    assert report.source_engine == "mysql"
    assert report.summary.rules_errored == 0


def test_diagnostics_mariadb_enterprise() -> None:
    """Verifies diagnostic engine evaluation on MariaDB canonical schema."""
    canonical_db = build_enterprise_fixture(engine="mariadb", db_name="mariadb_db")
    schema = SchemaBuilder.from_canonical_database(canonical_db)

    evaluator = DiagnosticEvaluator()
    context = DiagnosticContext(schema=schema)

    report = evaluator.evaluate(context, list(ALL_FOUNDATIONAL_RULES))

    assert report.source_engine == "mariadb"
    assert report.summary.rules_errored == 0


def test_diagnostics_unicode_and_case_sensitive() -> None:
    """Verifies diagnostic evaluation on schemas containing unicode and case-sensitive names."""
    canonical_db = build_unicode_and_case_sensitive_fixture(engine="postgresql")
    schema = SchemaBuilder.from_canonical_database(canonical_db)

    evaluator = DiagnosticEvaluator()
    context = DiagnosticContext(schema=schema)

    report = evaluator.evaluate(context, list(ALL_FOUNDATIONAL_RULES))

    assert report.summary.rules_errored == 0
