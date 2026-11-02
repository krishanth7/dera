"""Pure offline execution-plan analysis and deterministic report construction."""

from collections import Counter
from hashlib import sha256

from dera.sql_engineering.diagnostics import SqlDiagnosticsEngine
from dera.sql_engineering.dialects import resolve

from .analysis import analyze_nodes
from .models import ExecutionPlan, PlanProvenance, PlanSummary
from .normalizer import normalize
from .parser import canonical, decode, fail
from .registry import CAPABILITIES


def analyze_plan(
    plan_json: str, dialect: str, source_format: str, sql: str | None = None
) -> ExecutionPlan:
    resolve(dialect)
    if source_format != CAPABILITIES[dialect][0]:
        fail()
    raw = decode(plan_json)
    nodes, metadata, execution_time = normalize(raw, dialect)
    if not nodes:
        fail()
    findings, recommendations = analyze_nodes(nodes)
    roots = tuple(n.node_id for n in nodes if n.parent_id is None)
    root = nodes[0] if len(roots) == 1 and nodes[0].parent_id is None else None
    costs = sorted(
        (n for n in nodes if n.estimate.total is not None),
        key=lambda n: (-n.estimate.total, n.node_id),
    )[:5]
    sql_report = SqlDiagnosticsEngine().analyze(sql, dialect) if sql is not None else None
    provenance = PlanProvenance(
        input_sha256=sha256(canonical(raw).encode()).hexdigest(), source_format=source_format
    )
    summary = PlanSummary(
        node_count=len(nodes),
        max_depth=max(n.depth for n in nodes),
        has_actual_metrics=execution_time is not None
        or any(
            n.actual.rows is not None
            or n.actual.total_time_ms is not None
            or n.actual.loops is not None
            for n in nodes
        ),
        estimated_total_cost=root.estimate.total if root else None,
        estimated_startup_cost=root.estimate.startup if root else None,
        execution_time_ms=execution_time,
        highest_inclusive_cost_node_ids=tuple(n.node_id for n in costs),
        operation_counts=dict(sorted(Counter(n.operation for n in nodes).items())),
    )
    partial = any(f.rule_id == "PLAN016" for f in findings)
    payload = dict(
        status="PARTIAL" if partial else "COMPLETE",
        dialect=dialect,
        root_ids=roots,
        nodes=nodes,
        summary=summary,
        diagnostics=findings,
        recommendations=recommendations,
        provenance=provenance,
        source_metadata_json=canonical(metadata),
        limitations=(
            "Imported plans only; no live acquisition or EXPLAIN execution.",
            "Unknown properties are preserved. Plan-to-SQL association is not verified.",
            "Workers and repeated loops are not summed. Exclusive costs are not inferred.",
        ),
        sql_diagnostics=sql_report,
        plan_fingerprint="",
    )
    report = ExecutionPlan(**payload)
    digest = sha256(
        b"DERA:EXECUTION-PLAN:V1\n"
        + canonical(report.model_dump(mode="json", exclude={"plan_fingerprint"})).encode()
    ).hexdigest()
    return report.model_copy(update={"plan_fingerprint": digest})
