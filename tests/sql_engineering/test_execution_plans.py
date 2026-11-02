"""Offline dialect fixtures, deterministic metrics, resource and security boundaries."""

import json
from unittest.mock import patch

import pytest
from dera.sql_engineering.execution_plans import PlanInputError, analyze_plan
from dera.sql_engineering.execution_plans.parser import MAX_BYTES, decode


def pg(node=None):
    return {
        "Plan": node
        or {
            "Node Type": "Seq Scan",
            "Relation Name": "订单",
            "Plan Rows": 10000,
            "Startup Cost": 0,
            "Total Cost": 250,
            "Plan Width": 24,
        },
        "Execution Time": 12,
    }


def run(data, dialect="postgresql", fmt=None, sql=None):
    formats = {
        "postgresql": "postgresql-json",
        "mysql": "mysql-json-v1",
        "mariadb": "mariadb-json",
        "sqlite": "sqlite-eqp",
    }
    return analyze_plan(json.dumps(data), dialect, fmt or formats[dialect], sql)


def rules(report):
    return {f.rule_id for f in report.diagnostics}


def test_postgres_costs_unicode_actuals_and_determinism():
    report = run(pg())
    assert report.summary.estimated_total_cost == 250
    assert report.summary.execution_time_ms == 12
    assert report.nodes[0].relation.name == "订单"
    assert report.nodes[0].estimate.unit == "postgresql_planner_units"
    assert report.summary.has_actual_metrics is True
    assert rules(report) == {"PLAN001"}
    assert run(pg()).model_dump_json() == report.model_dump_json()
    assert len(report.plan_fingerprint) == 64
    assert run([pg()]).nodes == report.nodes


@pytest.mark.parametrize(
    ("est", "act", "ratio", "case"),
    [
        (10, 100, 10, "COMPARABLE"),
        (0, 0, 1, "BOTH_ZERO"),
        (0, 1, None, "ZERO_ESTIMATE"),
        (10, 0, 0, "COMPARABLE"),
    ],
)
def test_row_formula(est, act, ratio, case):
    node = {
        "Node Type": "Index Scan",
        "Plan Rows": est,
        "Actual Rows": act,
        "Actual Loops": 20,
        "Actual Total Time": 2,
    }
    result = run(pg(node)).nodes[0].actual
    assert result.row_estimation_ratio == ratio
    assert result.row_estimation_error == act - est
    assert result.estimation_case == case
    assert result.rows == act  # No loop multiplication.


@pytest.mark.parametrize(
    "extra", [{"Actual Loops": 0}, {"Parallel Aware": True}, {"Workers": [{"Actual Rows": 100}]}]
)
def test_zero_loops_and_parallel_not_compared(extra):
    node = {"Node Type": "Seq Scan", "Plan Rows": 10, "Actual Rows": 100, **extra}
    assert run(pg(node)).nodes[0].actual.estimation_case == "NOT_EVALUATED"


def test_inclusive_costs_not_summed_and_relationships():
    data = pg(
        {
            "Node Type": "Hash Join",
            "Total Cost": 100,
            "Plans": [
                {"Node Type": "Seq Scan", "Total Cost": 60},
                {"Node Type": "Index Only Scan", "Total Cost": 50, "Index Name": "ix"},
            ],
        }
    )
    report = run(data)
    assert report.summary.estimated_total_cost == 100
    assert report.nodes[0].child_ids == ("n0001", "n0002")
    assert report.nodes[1].parent_id == "n0000"
    assert report.nodes[2].relation.covering_index
    assert report.summary.highest_inclusive_cost_node_ids == ("n0000", "n0001", "n0002")


def test_evidence_rules_and_recommendations():
    data = pg(
        {
            "Node Type": "Nested Loop",
            "Plans": [
                {"Node Type": "Seq Scan"},
                {
                    "Node Type": "Materialize",
                    "Actual Loops": 1000,
                    "Plans": [
                        {
                            "Node Type": "Sort",
                            "Sort Space Type": "Disk",
                            "Plan Rows": 100000,
                            "Plans": [{"Node Type": "Hash", "Hash Batches": 4}],
                        }
                    ],
                },
            ],
        }
    )
    report = run(data)
    assert {"PLAN003", "PLAN005", "PLAN007", "PLAN008", "PLAN010", "PLAN015"} <= rules(report)
    assert [f.rule_id for f in report.diagnostics] == sorted(f.rule_id for f in report.diagnostics)
    for f, r in zip(report.diagnostics, report.recommendations, strict=True):
        assert r.finding_id == f.finding_id
        assert r.evidence == f.evidence
        assert r.manual_review_required and f.limitations and f.runtime_verification_needed


@pytest.mark.parametrize(
    "operation",
    [
        "Seq Scan",
        "Index Scan",
        "Index Only Scan",
        "Bitmap Heap Scan",
        "Nested Loop",
        "Hash Join",
        "Merge Join",
        "Sort",
        "Aggregate",
        "Materialize",
        "Gather",
        "CTE Scan",
    ],
)
def test_supported_pg_operations(operation):
    assert run(pg({"Node Type": operation})).nodes[0].operation != "UNKNOWN"


def test_unknown_pg_and_missing_metrics():
    result = run(pg({"Node Type": "Future Scan", "Extension": {"foo": "bar"}}))
    assert result.status == "PARTIAL"
    assert "PLAN016" in rules(result)
    assert json.loads(result.nodes[0].metadata_json)["Extension"] == {"foo": "bar"}
    assert result.nodes[0].actual.rows is None


def test_mysql_json_v1_join_filesort_and_cost():
    result = run(
        {
            "query_block": {
                "cost_info": {"query_cost": "20.5"},
                "ordering_operation": {
                    "using_filesort": True,
                    "using_temporary_table": True,
                    "nested_loop": [
                        {
                            "table": {
                                "table_name": "a",
                                "access_type": "ALL",
                                "rows_examined_per_scan": 10000,
                                "filtered": 10,
                            }
                        },
                        {
                            "table": {
                                "table_name": "b",
                                "access_type": "ref",
                                "key": "ix",
                                "rows_examined_per_scan": 2,
                                "using_index": True,
                            }
                        },
                    ],
                },
            }
        },
        "mysql",
    )
    assert result.summary.estimated_total_cost == 20.5
    assert result.nodes[0].estimate.unit == "mysql_planner_units"
    assert "NESTED_LOOP" in result.summary.operation_counts
    assert "PLAN006" in rules(result)
    assert result.nodes[-1].relation.index_name == "ix"
    assert result.nodes[-1].actual.rows is None


def test_mariadb_own_metrics_and_wrappers():
    result = run(
        {
            "query_block": {
                "read_sorted_file": {
                    "filesort": {
                        "r_total_time_ms": 2,
                        "temporary_table": {
                            "table": {
                                "table_name": "a",
                                "access_type": "ALL",
                                "rows": 10,
                                "r_rows": 100,
                                "r_loops": 2,
                                "r_total_time_ms": 1,
                            }
                        },
                    }
                }
            }
        },
        "mariadb",
    )
    table = result.nodes[-1]
    assert table.estimate.rows == 10 and table.actual.rows == 100
    assert table.actual.row_estimation_ratio == 10
    assert table.estimate.total is None and table.estimate.unit == "unavailable"
    assert "PLAN004" in rules(result)


def test_sqlite_eqp_parent_links_covering_and_temp():
    data = [
        {
            "id": 2,
            "parent": 0,
            "notused": 0,
            "detail": "SEARCH 订单 USING COVERING INDEX ix (id=?)",
        },
        {"id": 3, "parent": 2, "notused": 0, "detail": "USE TEMP B-TREE FOR ORDER BY"},
    ]
    result = run(data, "sqlite")
    assert result.nodes[1].parent_id == "n0000"
    assert result.nodes[0].relation.covering_index
    assert result.nodes[0].relation.index_name == "ix"
    assert result.summary.estimated_total_cost is None
    assert "PLAN006" in rules(result)


@pytest.mark.parametrize(
    "data",
    [
        [],
        [{"addr": 1, "opcode": "OpenRead"}],
        [{"id": 1, "parent": 1, "notused": 0, "detail": "SCAN a"}],
        [
            {"id": 1, "parent": 2, "notused": 0, "detail": "SCAN a"},
            {"id": 2, "parent": 1, "notused": 0, "detail": "SCAN b"},
        ],
        [{"id": 1, "parent": 77, "notused": 0, "detail": "SCAN a"}],
    ],
)
def test_invalid_sqlite_graph_and_bytecode(data):
    with pytest.raises(PlanInputError):
        run(data, "sqlite")


@pytest.mark.parametrize("value", [-1, True, "bad", float("nan"), float("inf"), 1e16])
def test_invalid_numeric(value):
    with pytest.raises(PlanInputError):
        run(pg({"Node Type": "Seq Scan", "Plan Rows": value}))


@pytest.mark.parametrize(
    "raw",
    [
        "{",
        '{"Plan":{},"Plan":{}}',
        "[" * 65 + "]" * 65,
        '{"x":"' + "x" * 16385 + '"}',
        "x" * (MAX_BYTES + 1),
        '"\\ud800"',
    ],
)
def test_hostile_json(raw):
    with pytest.raises(PlanInputError):
        decode(raw)


def test_limits_unknown_formats_and_large_plans():
    with pytest.raises(PlanInputError):
        run(pg(), "postgresql", "mysql-json-v1")
    data = pg({"Node Type": "Append", "Plans": [{"Node Type": "Result"} for _ in range(999)]})
    assert run(data).summary.node_count == 1000
    data["Plan"]["Plans"].append({"Node Type": "Result"})
    with pytest.raises(PlanInputError):
        run(data)
    node = {"Node Type": "Result"}
    for _ in range(49):
        node = {"Node Type": "Result", "Plans": [node]}
    with pytest.raises(PlanInputError):
        run(pg(node))


def test_sql_diagnostics_reuse_and_no_execution():
    with patch(
        "dera_connectors.base.connector.BaseConnector.connect",
        side_effect=AssertionError("execution"),
    ):
        result = run(pg(), sql="DELETE FROM accounts")
    assert result.sql_diagnostics.analysis.safety == "unsafe"
    assert result.provenance.acquisition == "IMPORTED_UNVERIFIED"
    assert run(pg(), sql="SELECT 1").plan_fingerprint != result.plan_fingerprint


def test_tiny_estimate_ratio_does_not_emit_infinity():
    report = run(pg({"Node Type": "Result", "Plan Rows": 1e-300, "Actual Rows": 1e15}))
    assert report.nodes[0].actual.row_estimation_ratio is None
    assert "Infinity" not in report.model_dump_json()


@pytest.mark.parametrize(
    ("data", "dialect"),
    [
        ({"Plan": {"Node Type": "Result", "Plans": {}}}, "postgresql"),
        ([pg(), pg()], "postgresql"),
        ({"query_plan": {"operation": "Table scan"}}, "mysql"),
        (
            {
                "query_block": {
                    "table": {"table_name": "a", "access_type": "ALL", "rows_examined_per_scan": -1}
                }
            },
            "mysql",
        ),
        (
            {
                "query_block": {
                    "table": {"table_name": "a", "access_type": "ALL", "rows": "not numeric"}
                }
            },
            "mariadb",
        ),
    ],
)
def test_malformed_dialect_shapes(data, dialect):
    with pytest.raises(PlanInputError):
        run(data, dialect)


def test_no_low_level_database_access():
    with patch("sqlite3.connect", side_effect=AssertionError("customer SQL execution")):
        run(pg())


def test_mysql_subquery_flags_and_unknown_entry_metadata_preserved():
    result = run(
        {
            "query_block": {
                "attached_subqueries": [
                    {
                        "dependent": True,
                        "cacheable": False,
                        "query_block": {"table": {"table_name": "a", "access_type": "ALL"}},
                    }
                ]
            }
        },
        "mysql",
    )
    assert any(json.loads(n.metadata_json).get("dependent") is True for n in result.nodes)
    result = run(
        {
            "query_block": {
                "nested_loop": [
                    {
                        "table": {"table_name": "a", "access_type": "ALL"},
                        "future_operator": {"data": "preserved"},
                    }
                ]
            }
        },
        "mysql",
    )
    assert result.status == "PARTIAL"
    assert any("future_operator" in json.loads(n.metadata_json) for n in result.nodes)


def test_initplan_is_not_inferred_as_nested_loop_inner():
    result = run(
        pg(
            {
                "Node Type": "Nested Loop",
                "Plans": [
                    {"Node Type": "Result", "Parent Relationship": "Outer"},
                    {
                        "Node Type": "Result",
                        "Parent Relationship": "InitPlan",
                        "Actual Loops": 1000,
                    },
                    {"Node Type": "Result", "Parent Relationship": "Inner", "Actual Loops": 1},
                ],
            }
        )
    )
    assert "PLAN007" not in rules(result)
