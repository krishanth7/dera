"""Deterministic structural and schema diagnostic behavior; zero query execution."""

from unittest.mock import patch

import pytest
import sqlglot
from dera.sql_engineering import analyze
from dera.sql_engineering.diagnostics import SqlDiagnosticsEngine
from dera.sql_engineering.diagnostics.complexity import WEIGHTS, score
from dera.sql_engineering.diagnostics.registry import REGISTRY, RuleRegistry

from tests.sql_engineering.diagnostics_fixtures import snapshot

ENGINE = SqlDiagnosticsEngine()


def ids(result):
    return {f.rule_id for f in result.findings}


@pytest.mark.parametrize("dialect", ["postgresql", "sqlite", "mysql", "mariadb"])
def test_dialect_determinism_and_shared_parse(dialect):
    sql = "SELECT a.id FROM accounts a JOIN users u ON a.id=u.id WHERE a.id=:id"
    with patch("sqlglot.parse", wraps=sqlglot.parse) as parser:
        result = ENGINE.analyze(sql, dialect)
        assert parser.call_count == 1
    assert result.analysis == analyze(sql, dialect)
    assert result.model_dump_json() == ENGINE.analyze(sql, dialect).model_dump_json()
    assert len(result.fingerprint) == 64
    assert all(
        e.status == "NOT_EVALUATED"
        for e in result.rule_evaluations
        if REGISTRY.get(e.rule_id).schema_required
    )


@pytest.mark.parametrize(
    ("sql", "expected"),
    [
        ("SELECT 1", set()),
        ("SELECT * FROM t", {"SQL001", "SQL017"}),
        ("UPDATE t SET x=1; DELETE FROM t", {"SQL002"}),
        ("SELECT a.id FROM a,b WHERE a.id=b.id", {"SQL003"}),
        ("SELECT a.id FROM a CROSS JOIN b", {"SQL004"}),
        ("SELECT id FROM t WHERE LOWER(name)='x'", {"SQL005"}),
        ("SELECT id FROM t WHERE name LIKE '%x'", {"SQL006"}),
        ("SELECT id FROM t WHERE a=1 OR a=2 OR a=3 OR a=4 OR a=5", {"SQL007"}),
        ("SELECT a.id FROM a WHERE EXISTS (SELECT 1 FROM b WHERE b.id=a.id)", {"SQL008"}),
        ("SELECT id FROM t ORDER BY id", {"SQL011"}),
        ("SELECT DISTINCT id FROM t", {"SQL012"}),
        ("SELECT a,b,c,d,e FROM t GROUP BY a,b,c,d,e", {"SQL013"}),
        ("SELECT id FROM t LIMIT 10", {"SQL018"}),
        ("SELECT id FROM t UNION SELECT id FROM u", {"SQL019"}),
        ("SELECT FROM", {"SQL020"}),
        ("SELECT * FROM t WHERE name ILIKE 'x'", set()),
    ],
)
def test_structural_rules(sql, expected):
    result = ENGINE.analyze(sql, "postgresql")
    assert expected <= ids(result)
    assert result.total_findings == len(result.findings)
    for finding, recommendation in zip(result.findings, result.recommendations, strict=True):
        assert recommendation.rule_id == finding.rule_id
        assert recommendation.evidence == finding.evidence
        assert recommendation.manual_review_required
        assert recommendation.limitations


def test_no_projection_false_positive_for_count_star():
    assert "SQL001" not in ids(ENGINE.analyze("SELECT COUNT(*) FROM t", "postgresql"))


def test_union_all_does_not_request_duplicate_elimination():
    assert "SQL019" not in ids(ENGINE.analyze("SELECT 1 UNION ALL SELECT 1", "sqlite"))


def test_nested_cte_window_and_aggregation_factors():
    sql = "WITH x AS (SELECT id FROM t) SELECT SUM(id), ROW_NUMBER() OVER (ORDER BY id) FROM (SELECT id FROM x) a GROUP BY id"
    result = ENGINE.analyze(sql, "postgresql")
    factors = {f.name: f.count for f in result.complexity.factor_breakdown}
    assert factors["ctes"] == 1
    assert factors["nested_queries"] == 1
    assert factors["aggregates"] == 1
    assert factors["windows"] == 1
    assert result.complexity.score == sum(
        f.contribution for f in result.complexity.factor_breakdown
    )
    assert result.complexity.scoring_version == "1.0.0"
    assert all(
        f.contribution == f.count * WEIGHTS[f.name] for f in result.complexity.factor_breakdown
    )
    assert score((sqlglot.parse_one("SELECT 1"),)).score == 1


def test_rule_thresholds():
    joins = "SELECT a.id FROM a " + " ".join(f"JOIN t{i} ON a.id=t{i}.id" for i in range(8))
    assert "SQL010" in ids(ENGINE.analyze(joins, "postgresql"))
    nested = "SELECT 1"
    for _ in range(9):
        nested = f"SELECT * FROM ({nested}) AS q"
    assert "SQL009" in ids(ENGINE.analyze(nested, "postgresql"))


@pytest.mark.parametrize("dialect", ["sqlite", "mysql", "mariadb"])
def test_dialect_limitation(dialect):
    result = ENGINE.analyze("SELECT id FROM t WHERE id ILIKE 'x'", dialect)
    assert "SQL014" in ids(result)
    assert result.analysis_status == "PARTIAL"


def test_schema_known_unknown_ambiguous_types_indexes_and_fk():
    sql = "SELECT id FROM accounts a JOIN users u ON a.id=u.id WHERE a.id=1"
    indexed = ENGINE.analyze(sql, "postgresql", snapshot())
    assert {"SQL015", "SQL016", "SQL105"} <= ids(indexed)
    assert "SQL103" not in ids(indexed)
    unindexed = ENGINE.analyze(sql, "postgresql", snapshot(indexed=False))
    assert {"SQL103", "SQL104"} <= ids(unindexed)
    assert "SQL101" in ids(ENGINE.analyze("SELECT * FROM missing", "postgresql", snapshot()))
    assert "SQL102" in ids(ENGINE.analyze("SELECT missing FROM accounts", "postgresql", snapshot()))
    assert "SQL102" not in ids(ENGINE.analyze("SELECT id FROM accounts", "postgresql", snapshot()))


def test_incomplete_schema_not_evaluated():
    result = ENGINE.analyze("SELECT bad FROM missing", "postgresql", snapshot(complete="PARTIAL"))
    assert "SQL101" not in ids(result)
    assert all(
        e.status == "NOT_EVALUATED"
        for e in result.rule_evaluations
        if REGISTRY.get(e.rule_id).schema_required
    )


def test_snapshot_integrity_and_dialect():
    with pytest.raises(ValueError, match="integrity"):
        ENGINE.analyze(
            "SELECT 1", "postgresql", snapshot().model_copy(update={"fingerprint": "0" * 64})
        )
    with pytest.raises(ValueError, match="dialect"):
        ENGINE.analyze("SELECT 1", "sqlite", snapshot())


def test_aliases_derived_cte_and_natural_joins_are_conservative():
    for sql in (
        "WITH x AS (SELECT id FROM accounts) SELECT id FROM x",
        "SELECT id FROM accounts NATURAL JOIN users",
        "SELECT id FROM (SELECT id FROM accounts) q",
    ):
        result = ENGINE.analyze(sql, "postgresql", snapshot())
        assert "SQL101" not in ids(result)
        assert "SQL015" not in ids(result)
        assert any(
            e.status == "NOT_EVALUATED" for e in result.rule_evaluations if e.rule_id == "SQL015"
        )


def test_options_versions_and_fingerprints():
    a = ENGINE.analyze("SELECT * FROM t", "sqlite")
    b = ENGINE.analyze(
        "SELECT * FROM t", "sqlite", include_complexity=False, include_recommendations=False
    )
    assert b.complexity is None and b.recommendations == ()
    assert b.fingerprint != a.fingerprint
    assert a.fingerprint != ENGINE.analyze("SELECT * FROM u", "sqlite").fingerprint
    assert a.model_copy(update={"rules_version": "2.0.0"}).model_dump() != a.model_dump()
    with pytest.raises(ValueError, match="Duplicate"):
        RuleRegistry((REGISTRY.rules[0], REGISTRY.rules[0]))


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT (",
        "SELECT 'unterminated",
        "SELECT " + "(" * 49 + "1" + ")" * 49,
        "x" * 16385,
        "SELECT '\ud800'",
    ],
)
def test_rejected_inputs(sql):
    result = ENGINE.analyze(sql, "sqlite")
    assert result.analysis_status == "INDETERMINATE"
    assert result.complexity is None
    assert all(e.status == "NOT_EVALUATED" for e in result.rule_evaluations)


def test_no_customer_execution_and_no_sensitive_logging(caplog):
    with (
        patch("sqlite3.connect", side_effect=AssertionError("execution")),
        patch(
            "dera_connectors.base.connector.BaseConnector.connect",
            side_effect=AssertionError("execution"),
        ),
    ):
        result = ENGINE.analyze("CALL secret_password_987()", "mysql")
    assert "secret_password_987" not in caplog.text
    assert "secret_password_987" not in result.model_dump_json()


def test_stable_rule_and_statement_order():
    result = ENGINE.analyze("SELECT * FROM a; SELECT * FROM b", "sqlite")
    assert [(f.rule_id, f.statement_index, f.finding_id) for f in result.findings] == sorted(
        (f.rule_id, f.statement_index, f.finding_id) for f in result.findings
    )


@pytest.mark.parametrize("dialect", ["postgresql", "sqlite", "mysql", "mariadb"])
def test_schema_all_dialects(dialect):
    result = ENGINE.analyze(
        "SELECT a.id FROM accounts a JOIN users u ON a.id=u.id",
        dialect,
        snapshot(engine=dialect, indexed=False),
    )
    assert "SQL101" not in ids(result)
    assert {"SQL103", "SQL105"} <= ids(result)


def test_mysql_case_unknown_and_postgres_case_exact():
    result = ENGINE.analyze("SELECT * FROM Accounts", "mysql", snapshot(engine="mysql"))
    assert "SQL106" in ids(result) and "SQL101" not in ids(result)
    assert "SQL101" in ids(ENGINE.analyze('SELECT * FROM "Accounts"', "postgresql", snapshot()))
    assert "SQL101" not in ids(ENGINE.analyze("SELECT * FROM ACCOUNTS", "postgresql", snapshot()))


def test_schema_does_not_claim_missing_fk():
    result = ENGINE.analyze(
        "SELECT a.id FROM accounts a JOIN accounts b ON a.id=b.id", "postgresql", snapshot()
    )
    assert "SQL105" not in ids(result)
    assert "SQL103" not in ids(result)


def test_explicit_escape_like_not_assumed_wildcard():
    result = ENGINE.analyze("SELECT id FROM t WHERE name LIKE '%%foo' ESCAPE '%'", "postgresql")
    assert "SQL006" not in ids(result)


def test_scoring_version_bound_to_fingerprint():
    from dera.sql_engineering.diagnostics.fingerprints import fingerprint

    report = ENGINE.analyze("SELECT 1", "postgresql").model_dump(
        mode="json", exclude={"fingerprint"}
    )
    old = fingerprint(report)
    report["complexity"]["scoring_version"] = "2.0.0"
    assert fingerprint(report) != old


def test_postgres_unquoted_alias_case_folding():
    result = ENGINE.analyze("SELECT a.id FROM accounts AS A", "postgresql", snapshot())
    assert "SQL102" not in ids(result)
    assert all(e.status == "EVALUATED" for e in result.rule_evaluations if e.rule_id == "SQL102")


def test_unqualified_nested_correlation_is_not_a_missing_column():
    from dera.reverse_engineering.snapshots.fingerprints import compute_structural_fingerprint

    original = snapshot()
    tables = (
        original.payload.tables[0],
        original.payload.tables[1].model_copy(update={"columns": ()}),
    )
    payload = original.payload.model_copy(update={"tables": tables})
    context = original.model_copy(
        update={"payload": payload, "fingerprint": compute_structural_fingerprint(payload)}
    )
    result = ENGINE.analyze(
        "SELECT a.id FROM accounts a WHERE EXISTS (SELECT 1 FROM users u WHERE id=a.id)",
        "postgresql",
        context,
    )
    assert "SQL102" not in ids(result)
    assert any(
        e.rule_id == "SQL102" and e.status == "NOT_EVALUATED" for e in result.rule_evaluations
    )
