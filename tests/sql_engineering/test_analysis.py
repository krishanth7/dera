"""Offline analysis and adversarial security regression corpus."""

from unittest.mock import patch

import pytest
from dera.sql_engineering import analyze


@pytest.mark.parametrize("dialect", ["postgresql", "sqlite", "mysql", "mariadb"])
def test_dialects_and_determinism(dialect):
    sql = "SELECT a.id FROM accounts a JOIN users u ON u.id=a.id WHERE a.id=:id"
    result = analyze(sql, dialect)
    assert result.statement_count == 1
    assert result.safety == "read_only_candidate"
    assert result.statements[0].joins
    assert result.statements[0].parameters
    assert result.statements[0].predicates
    assert result.canonical_json() == analyze(sql, dialect).canonical_json()


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO t VALUES (1)",
        "UPDATE t SET x=1",
        "DELETE FROM t",
        "MERGE INTO t USING s ON t.id=s.id WHEN MATCHED THEN DELETE",
        "CREATE TABLE t (id INT)",
        "ALTER TABLE t ADD x INT",
        "DROP TABLE t",
        "TRUNCATE TABLE t",
        "BEGIN",
        "COMMIT",
        "ROLLBACK",
        "GRANT SELECT ON t TO u",
        "SELECT * INTO new_t FROM t",
        "SELECT * FROM t FOR UPDATE",
        "WITH x AS (DELETE FROM t RETURNING *) SELECT * FROM x",
    ],
)
def test_mutations_and_controls(sql):
    assert analyze(sql, "postgresql").safety == "unsafe"


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT nextval('seq')",
        "SELECT pg_advisory_lock(1)",
        "SELECT load_extension('x')",
        "SELECT custom_effect()",
        "SELECT GET_LOCK('x', 1)",
        "/*! DELETE FROM t */ SELECT 1",
        "/*M! DELETE FROM t */ SELECT 1",
        "VACUUM",
        "FROBNICATE t",
    ],
)
def test_unverified_constructs_never_candidate(sql):
    assert analyze(sql, "mysql").safety != "read_only_candidate"


@pytest.mark.parametrize(
    "sql", ["SELECT FROM", "SELECT (", "SELECT 'unterminated", "\x00", "-- comment"]
)
def test_invalid(sql):
    result = analyze(sql, "sqlite")
    assert result.safety == "unknown"
    assert result.diagnostics
    assert result.diagnostics[0].span.end == len(sql)


def test_ctes_subqueries_unicode_and_comments():
    result = analyze(
        'WITH x AS (SELECT "名前" FROM "顧客") SELECT * FROM x WHERE EXISTS (SELECT 1 FROM orders) -- DELETE',
        "postgresql",
    )
    assert result.statement_count == 1
    assert result.safety == "read_only_candidate"
    assert '"顧客"' in result.statements[0].objects
    assert "x" not in result.statements[0].objects


def test_multiple_statements():
    result = analyze("SELECT ';'; /* ; */ DELETE FROM t", "sqlite")
    assert result.statement_count == 2
    assert result.safety == "unsafe"


@pytest.mark.parametrize(
    "sql",
    [
        "x" * 16385,
        "SELECT " + "(" * 49 + "1" + ")" * 49,
        "SELECT " + "1+" * 2048 + "1",
        "SELECT 1;" * 33,
    ],
)
def test_resource_bounds(sql):
    assert "resource_limit" in analyze(sql, "sqlite").unsupported_constructs


def test_no_database_execution():
    with (
        patch("sqlite3.connect", side_effect=AssertionError("customer execution")),
        patch("sqlalchemy.create_engine", side_effect=AssertionError("customer execution")),
    ):
        assert analyze("DELETE FROM customer", "sqlite").safety == "unsafe"


def test_unknown_dialect():
    with pytest.raises(ValueError):
        analyze("SELECT 1", "oracle")


def test_no_sql_in_logs(caplog):
    analyze("SOMETHING secret_password_123", "mysql")
    assert "secret_password_123" not in caplog.text


@pytest.mark.parametrize("dialect", ["sqlite", "mysql", "mariadb"])
def test_unsupported_ilike(dialect):
    result = analyze("SELECT * FROM t WHERE name ILIKE 'x'", dialect)
    assert result.safety == "unknown"
    assert "dialect_feature:ILike" in result.unsupported_constructs


def test_deep_expression_chain():
    assert analyze("SELECT " + "+".join(["1"] * 100), "sqlite").safety == "unknown"


def test_core_has_no_execution_imports():
    import ast
    from pathlib import Path

    import dera.sql_engineering as package

    for file in Path(package.__file__).parent.glob("*.py"):
        for node in ast.walk(ast.parse(file.read_text())):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith(
                    ("dera_connectors", "sqlalchemy", "sqlite3")
                )
            if isinstance(node, ast.Import):
                assert all(
                    not alias.name.startswith(("dera_connectors", "sqlalchemy", "sqlite3"))
                    for alias in node.names
                )


def test_select_variable_assignment_is_unsafe():
    assert analyze("SELECT @x := 1", "mysql").safety == "unsafe"


def test_invalid_unicode():
    assert analyze("SELECT '\ud800'", "sqlite").safety == "unknown"
