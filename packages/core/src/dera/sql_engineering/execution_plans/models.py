"""Versioned immutable imported-plan contracts. Nodes are flat to bound serialization depth."""

from typing import Literal

from dera.diagnostics.enums import DiagnosticSeverity
from dera.sql_engineering.diagnostics.models import SqlDiagnosticsReport
from dera.sql_engineering.models import Dialect, Model

PlanOperation = Literal[
    "SCAN",
    "INDEX_SCAN",
    "BITMAP_SCAN",
    "NESTED_LOOP",
    "HASH_JOIN",
    "MERGE_JOIN",
    "SORT",
    "AGGREGATE",
    "MATERIALIZE",
    "PARALLEL",
    "CTE",
    "QUERY",
    "SET",
    "UNKNOWN",
]


class PlanRelation(Model):
    name: str | None = None
    namespace: str | None = None
    alias: str | None = None
    index_name: str | None = None
    covering_index: bool = False


class PlanCostEstimate(Model):
    startup: float | None = None
    total: float | None = None
    rows: float | None = None
    row_width: float | None = None
    filtered_percent: float | None = None
    unit: Literal["postgresql_planner_units", "mysql_planner_units", "unavailable"]
    semantics: str


class PlanActualMetrics(Model):
    rows: float | None = None
    loops: float | None = None
    total_time_ms: float | None = None
    row_semantics: str
    time_semantics: str
    row_estimation_ratio: float | None = None
    row_estimation_error: float | None = None
    estimation_case: Literal["COMPARABLE", "BOTH_ZERO", "ZERO_ESTIMATE", "NOT_EVALUATED"]


class ExecutionPlanNode(Model):
    node_id: str
    parent_id: str | None
    depth: int
    operation: PlanOperation
    native_operation: str
    relation: PlanRelation
    estimate: PlanCostEstimate
    actual: PlanActualMetrics
    child_ids: tuple[str, ...] = ()
    metadata_json: str


class PlanDiagnostic(Model):
    finding_id: str
    rule_id: str
    severity: DiagnosticSeverity
    node_id: str
    evidence: tuple[str, ...]
    explanation: str
    suggested_investigation: str
    limitations: tuple[str, ...]
    observation_kind: Literal["STRUCTURAL_FACT", "REVIEW_HEURISTIC"] = "REVIEW_HEURISTIC"
    runtime_verification_needed: bool = True


class PlanRecommendation(Model):
    recommendation_id: str
    finding_id: str
    rule_id: str
    node_id: str
    title: str
    evidence: tuple[str, ...]
    suggested_action: str
    expected_benefit: str = (
        "May clarify the observed plan behavior; no speed improvement is promised."
    )
    limitations: tuple[str, ...]
    manual_review_required: bool = True


class PlanSummary(Model):
    node_count: int
    max_depth: int
    has_actual_metrics: bool
    estimated_total_cost: float | None
    estimated_startup_cost: float | None
    execution_time_ms: float | None
    highest_inclusive_cost_node_ids: tuple[str, ...]
    operation_counts: dict[str, int]
    cost_limitation: str = "Costs are engine-specific inclusive estimates; never sum nodes or compare across engines. Exclusive cost and runtime bottlenecks are not inferred."


class PlanProvenance(Model):
    acquisition: Literal["IMPORTED_UNVERIFIED"] = "IMPORTED_UNVERIFIED"
    input_sha256: str
    parser_version: str = "1.0.0"
    rules_version: str = "1.0.0"
    model_version: str = "1.0.0"
    source_format: str
    association: str = (
        "Optional SQL is caller-associated; correspondence with the imported plan is not verified."
    )


class ExecutionPlan(Model):
    status: Literal["COMPLETE", "PARTIAL"]
    dialect: Dialect
    root_ids: tuple[str, ...]
    nodes: tuple[ExecutionPlanNode, ...]
    summary: PlanSummary
    diagnostics: tuple[PlanDiagnostic, ...]
    recommendations: tuple[PlanRecommendation, ...]
    provenance: PlanProvenance
    source_metadata_json: str
    limitations: tuple[str, ...]
    sql_diagnostics: SqlDiagnosticsReport | None = None
    plan_fingerprint: str
