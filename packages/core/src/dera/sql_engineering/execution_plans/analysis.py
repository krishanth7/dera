"""Evidence-bound rules. Thresholds are review heuristics, never measured execution cost."""

import json

from .models import PlanDiagnostic, PlanRecommendation

RULES = {
    "PLAN001": (
        "Large sequential scan",
        "Review filter selectivity and existing indexes; small scans can be optimal.",
    ),
    "PLAN003": ("High estimated row volume", "Review the required result volume and filtering."),
    "PLAN004": (
        "Estimated and actual rows differ",
        "Investigate statistics and predicate correlation; early termination can also explain differences.",
    ),
    "PLAN005": (
        "Sort spill reported",
        "Inspect sort input and memory settings with a database administrator.",
    ),
    "PLAN006": (
        "Temporary storage indicated",
        "Review sorting, grouping and temporary storage evidence.",
    ),
    "PLAN007": (
        "Repeated nested-loop input",
        "Review inner-side access and join selectivity; repetition may be appropriate.",
    ),
    "PLAN008": (
        "Multiple hash batches reported",
        "Inspect hash input volume and memory constraints.",
    ),
    "PLAN010": (
        "Repeated materialization reported",
        "Inspect reuse and invocation counts; caching may be beneficial.",
    ),
    "PLAN011": ("Deep plan structure", "Review nested operations and query structure."),
    "PLAN015": (
        "Incomplete metrics",
        "Import the required metrics from an authorized external source if available.",
    ),
    "PLAN016": (
        "Unsupported plan operation or structure",
        "Inspect preserved native metadata and confirm format compatibility.",
    ),
}
LIMITATIONS = (
    "Imported evidence is unverified and may be incomplete.",
    "This is an investigation prompt, not proof of a performance defect or an index prescription.",
)


def analyze_nodes(nodes):
    findings = []

    def emit(rule, node, evidence):
        title, action = RULES[rule]
        findings.append(
            PlanDiagnostic(
                finding_id=f"{rule}:{node.node_id}",
                rule_id=rule,
                severity="INFORMATIONAL",
                observation_kind="STRUCTURAL_FACT"
                if rule in {"PLAN015", "PLAN016"}
                else "REVIEW_HEURISTIC",
                node_id=node.node_id,
                evidence=tuple(evidence),
                explanation=title,
                suggested_investigation=action,
                limitations=LIMITATIONS,
            )
        )

    by_id = {n.node_id: n for n in nodes}
    for node in nodes:
        raw = json.loads(node.metadata_json)
        rows = node.estimate.rows
        if node.operation == "SCAN" and rows is not None and rows >= 10_000:
            emit("PLAN001", node, [f"Estimated rows per scan: {rows}."])
        if rows is not None and rows >= 100_000:
            emit("PLAN003", node, [f"Estimated rows: {rows}."])
        actual = node.actual
        ratio = actual.row_estimation_ratio
        if actual.estimation_case == "ZERO_ESTIMATE" or (
            ratio is not None and (ratio >= 10 or ratio <= 0.1)
        ):
            emit(
                "PLAN004",
                node,
                [
                    f"Estimated={rows}; reported actual={actual.rows}; ratio={ratio}; case={actual.estimation_case}.",
                    actual.row_semantics,
                ],
            )
        if raw.get("Sort Space Type") == "Disk":
            emit("PLAN005", node, ["Sort Space Type=Disk."])
        if (
            raw.get("using_temporary_table") is True
            or node.native_operation == "temporary_table"
            or node.native_operation.startswith("USE TEMP B-TREE")
        ):
            emit("PLAN006", node, ["Native plan explicitly reports temporary storage."])
        if node.operation == "NESTED_LOOP":
            inner = [by_id[k] for k in node.child_ids[1:]]
            for child in inner:
                if child.actual.loops is not None and child.actual.loops >= 1_000:
                    emit(
                        "PLAN007",
                        node,
                        [f"Inner node {child.node_id} reports {child.actual.loops} loops."],
                    )
                    break
        batches = raw.get("Hash Batches")
        if isinstance(batches, (int, float)) and not isinstance(batches, bool) and batches > 1:
            emit("PLAN008", node, [f"Hash Batches={batches}."])
        if node.operation == "MATERIALIZE" and actual.loops is not None and actual.loops >= 1_000:
            emit(
                "PLAN010",
                node,
                [f"Reported invocations={actual.loops}; underlying work is not inferred."],
            )
        if node.depth == 25:
            emit("PLAN011", node, ["Plan depth exceeds 24."])
        if rows is None or node.estimate.total is None:
            emit(
                "PLAN015",
                node,
                ["Estimated rows or inclusive cost unavailable; missing actuals are not zero."],
            )
        if node.operation == "UNKNOWN" or "dera_unrecognized_structure" in raw:
            emit(
                "PLAN016",
                node,
                ["Native operation or structural metadata is not fully normalized."],
            )
    findings.sort(key=lambda f: (f.rule_id, f.node_id))
    recommendations = tuple(
        PlanRecommendation(
            recommendation_id="REC:" + f.finding_id,
            finding_id=f.finding_id,
            rule_id=f.rule_id,
            node_id=f.node_id,
            title=f.explanation,
            evidence=f.evidence,
            suggested_action=f.suggested_investigation,
            limitations=f.limitations,
        )
        for f in findings
    )
    return tuple(findings), recommendations
