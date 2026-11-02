"""Dialect-specific imported-plan normalization. No SQL execution capability."""

import math
import re

from .models import ExecutionPlanNode, PlanActualMetrics, PlanCostEstimate, PlanRelation
from .parser import MAX_NODES, MAX_PLAN_DEPTH, canonical, fail, label, number
from .registry import MARIADB_CHILDREN, MYSQL_CHILDREN, PG_OPERATIONS


def actual_metrics(
    rows=None,
    loops=None,
    time=None,
    estimate=None,
    *,
    comparable=False,
    row_semantics="unavailable",
    time_semantics="unavailable",
):
    ratio = error = None
    case = "NOT_EVALUATED"
    if comparable and rows is not None and estimate is not None and loops != 0:
        error = rows - estimate
        if estimate == 0:
            case = "BOTH_ZERO" if rows == 0 else "ZERO_ESTIMATE"
            ratio = 1.0 if rows == 0 else None
        else:
            ratio = rows / estimate
            if math.isfinite(ratio):
                ratio = round(ratio, 6)
                case = "COMPARABLE"
            else:
                ratio = None
    return PlanActualMetrics(
        rows=rows,
        loops=loops,
        total_time_ms=time,
        row_semantics=row_semantics,
        time_semantics=time_semantics,
        row_estimation_ratio=ratio,
        row_estimation_error=error,
        estimation_case=case,
    )


class Builder:
    def __init__(self):
        self.nodes = []

    def add(self, parent, depth, operation, native, relation, estimate, actual, metadata):
        if depth > MAX_PLAN_DEPTH or len(self.nodes) >= MAX_NODES:
            fail()
        node = ExecutionPlanNode(
            node_id=f"n{len(self.nodes):04d}",
            parent_id=parent,
            depth=depth,
            operation=operation,
            native_operation=native,
            relation=relation,
            estimate=estimate,
            actual=actual,
            metadata_json=canonical(metadata),
        )
        self.nodes.append(node)
        return node.node_id

    def finish(self):
        children = {n.node_id: [] for n in self.nodes}
        for n in self.nodes:
            if n.parent_id:
                children[n.parent_id].append(n.node_id)
        return tuple(
            n.model_copy(update={"child_ids": tuple(children[n.node_id])}) for n in self.nodes
        )


def postgres(data):
    if isinstance(data, list):
        if len(data) != 1:
            fail()
        data = data[0]
    if not isinstance(data, dict) or not isinstance(data.get("Plan"), dict):
        fail()
    builder = Builder()

    def visit(raw, parent=None, depth=1):
        if not isinstance(raw, dict):
            fail()
        native = label(raw, "Node Type")
        if not native:
            fail()
        # Parallel Aware is metadata, not a new worker child; workers never become duplicated nodes.
        operation = PG_OPERATIONS.get(native, "UNKNOWN")
        estimate = PlanCostEstimate(
            startup=number(raw, "Startup Cost"),
            total=number(raw, "Total Cost"),
            rows=number(raw, "Plan Rows"),
            row_width=number(raw, "Plan Width"),
            unit="postgresql_planner_units",
            semantics="inclusive planner estimate; rows per invocation",
        )
        if (
            estimate.startup is not None
            and estimate.total is not None
            and estimate.startup > estimate.total
        ):
            fail()
        actual = actual_metrics(
            number(raw, "Actual Rows"),
            number(raw, "Actual Loops"),
            number(raw, "Actual Total Time"),
            estimate.rows,
            comparable=not raw.get("Parallel Aware", False) and not raw.get("Workers"),
            row_semantics="reported average rows per invocation; not multiplied by loops or workers",
            time_semantics="reported inclusive average milliseconds per invocation; not wall time",
        )
        relation = PlanRelation(
            name=label(raw, "Relation Name"),
            namespace=label(raw, "Schema"),
            alias=label(raw, "Alias"),
            index_name=label(raw, "Index Name"),
            covering_index=native == "Index Only Scan",
        )
        children = raw.get("Plans", [])
        if not isinstance(children, list):
            fail()
        node_id = builder.add(
            parent,
            depth,
            operation,
            native,
            relation,
            estimate,
            actual,
            {k: v for k, v in raw.items() if k != "Plans"},
        )
        for child in children:
            visit(child, node_id, depth + 1)

    visit(data["Plan"])
    return (
        builder.finish(),
        {k: v for k, v in data.items() if k != "Plan"},
        number(data, "Execution Time"),
    )


def mysql_family(data, dialect):
    """Separate key and metric contracts for MySQL JSON v1 and MariaDB JSON."""
    if not isinstance(data, dict) or not isinstance(data.get("query_block"), dict):
        fail()
    is_maria = dialect == "mariadb"
    structural = MARIADB_CHILDREN if is_maria else MYSQL_CHILDREN
    builder = Builder()

    def visit(kind, raw, parent=None, depth=1):
        if isinstance(raw, list):
            if kind == "nested_loop":
                parent = builder.add(
                    parent,
                    depth,
                    "NESTED_LOOP",
                    kind,
                    PlanRelation(),
                    PlanCostEstimate(
                        unit="unavailable", semantics="join container; no independent cost"
                    ),
                    actual_metrics(),
                    {},
                )
                depth += 1
            for child in raw:
                visit("entry", child, parent, depth)
            return
        if not isinstance(raw, dict):
            fail()
        # Lists such as nested_loop contain wrappers, not operations themselves.
        if kind in {
            "entry",
            "nested_loop",
            "query_specifications",
            "subqueries",
            "attached_subqueries",
            "optimized_away_subqueries",
        }:
            children = [(k, v) for k, v in sorted(raw.items()) if k in structural]
            if not children:
                # Keep unrecognized wrappers explicit, not silently interpreted.
                builder.add(
                    parent,
                    depth,
                    "UNKNOWN",
                    kind,
                    PlanRelation(),
                    PlanCostEstimate(unit="unavailable", semantics="unavailable"),
                    actual_metrics(),
                    raw,
                )
            else:
                for k, v in children:
                    visit(k, v, parent, depth)
            return
        operation = {
            "query_block": "QUERY",
            "table": "SCAN",
            "ordering_operation": "SORT",
            "filesort": "SORT",
            "grouping_operation": "AGGREGATE",
            "duplicates_removal": "AGGREGATE",
            "materialized_from_subquery": "MATERIALIZE",
            "materialized": "MATERIALIZE",
            "temporary_table": "MATERIALIZE",
            "union_result": "SET",
            "block-nl-join": "NESTED_LOOP",
            "recursive_union": "CTE",
            "read_sorted_file": "SORT",
            "buffer_result": "MATERIALIZE",
            "expression_cache": "MATERIALIZE",
        }.get(kind, "UNKNOWN")
        access = label(raw, "access_type")
        if kind == "table":
            if access in {
                "const",
                "eq_ref",
                "ref",
                "ref_or_null",
                "range",
                "index",
                "index_merge",
                "system",
                "fulltext",
            }:
                operation = "INDEX_SCAN"
            elif access != "ALL":
                operation = "UNKNOWN"
        costs = raw.get("cost_info", {})
        if not isinstance(costs, dict):
            fail()
        # prefix_cost is cumulative for a join prefix, never a table's exclusive cost.
        total = number(costs, "query_cost", strings=True) if not is_maria else None
        rows = number(raw, "rows" if is_maria else "rows_examined_per_scan")
        filtered = number(raw, "filtered")
        if filtered is not None and filtered > 100:
            fail()
        estimate = PlanCostEstimate(
            total=total,
            rows=rows,
            filtered_percent=filtered,
            unit="unavailable" if is_maria else "mysql_planner_units",
            semantics="estimated examined rows per scan; costs available only for query blocks",
        )
        actual = actual_metrics(
            number(raw, "r_rows") if is_maria else None,
            number(raw, "r_loops") if is_maria else None,
            number(raw, "r_total_time_ms") if is_maria else None,
            rows,
            comparable=is_maria,
            row_semantics="reported average rows read per invocation"
            if is_maria
            else "unavailable in MySQL JSON v1",
            time_semantics="reported inclusive cumulative milliseconds"
            if is_maria
            else "unavailable",
        )
        relation = PlanRelation(
            name=label(raw, "table_name"),
            index_name=label(raw, "key"),
            covering_index=raw.get("using_index") is True,
        )
        metadata = {k: v for k, v in raw.items() if k not in structural}
        # Unexpected object-valued properties may hide a future operation. Keep a limitation marker.
        unexpected = [
            k
            for k, v in metadata.items()
            if isinstance(v, (dict, list))
            and k
            not in {
                "cost_info",
                "possible_keys",
                "used_key_parts",
                "used_columns",
                "ref",
                "r_engine_stats",
                "sort_key",
            }
        ]
        if unexpected:
            metadata["dera_unrecognized_structure"] = sorted(unexpected)
        node_id = builder.add(
            parent,
            depth,
            operation,
            kind + (":" + access if access else ""),
            relation,
            estimate,
            actual,
            metadata,
        )
        for k, v in sorted(raw.items()):
            if k in structural:
                visit(k, v, node_id, depth + 1)

    visit("query_block", data["query_block"])
    return builder.finish(), {k: v for k, v in data.items() if k != "query_block"}, None


def sqlite(data):
    if not isinstance(data, list) or not data or len(data) > MAX_NODES:
        fail()
    rows = {}
    for row in data:
        if not isinstance(row, dict) or set(row) != {"id", "parent", "notused", "detail"}:
            fail()
        if any(type(row[k]) is not int for k in ("id", "parent", "notused")) or row["id"] in rows:
            fail()
        if not label(row, "detail"):
            fail()
        rows[row["id"]] = row
    # Validate parent chains and cycles; SQLite root sentinel 0/-1 is allowed only when absent.
    depths = {}

    def depth(key, seen):
        if key in seen:
            fail()
        if key in depths:
            return depths[key]
        if len(seen) >= MAX_PLAN_DEPTH:
            fail()
        parent = rows[key]["parent"]
        if parent not in rows and parent not in {0, -1}:
            fail()
        result = 1 if parent not in rows else depth(parent, seen | {key}) + 1
        depths[key] = result
        return result

    for key in rows:
        depth(key, set())
    ids = {key: f"n{i:04d}" for i, key in enumerate(rows)}
    builder = Builder()
    for key, raw in rows.items():
        detail = raw["detail"]
        operation = "UNKNOWN"
        relation = PlanRelation()
        match = re.fullmatch(r"(SCAN|SEARCH) (.+?)(?: USING (.+))?", detail)
        if match:
            method, name, using = match.groups()
            operation = "INDEX_SCAN" if method == "SEARCH" else "SCAN"
            index = re.match(r"(?:COVERING )?INDEX ([^ ]+)", using or "")
            relation = PlanRelation(
                name=name,
                index_name=index.group(1) if index else None,
                covering_index=bool(using and "COVERING INDEX" in using),
            )
        elif detail.startswith("USE TEMP B-TREE FOR "):
            operation = "SORT"
        elif detail.startswith(("MATERIALIZE ", "CO-ROUTINE ")):
            operation = "MATERIALIZE"
        elif detail.startswith(("COMPOUND QUERY", "UNION", "MERGE", "LEFT-MOST SUBQUERY")):
            operation = "SET"
        builder.add(
            ids.get(raw["parent"]),
            depths[key],
            operation,
            detail,
            relation,
            PlanCostEstimate(
                unit="unavailable", semantics="SQLite EQP supplies no cost or row estimates"
            ),
            actual_metrics(),
            raw,
        )
    return builder.finish(), {}, None


def normalize(data, dialect):
    if dialect == "postgresql":
        return postgres(data)
    if dialect in {"mysql", "mariadb"}:
        return mysql_family(data, dialect)
    return sqlite(data)
