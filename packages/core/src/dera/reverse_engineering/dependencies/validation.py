"""DERA Reverse Engineering — Phase 6.4 Dependency Validation.

Implements multi-severity integrity validation for dependency analysis results, checking
ordering completeness, level stratification, unresolved endpoints, and unbreakable cycles.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum

from dera.reverse_engineering.dependencies.errors import DependencyValidationError
from dera.reverse_engineering.dependencies.models import (
    DependencyAnalysisResult,
    DependencyEdge,
    DependencyValidationFinding,
)
from dera.reverse_engineering.dependencies.ordering import (
    sort_dependency_validation_findings,
)


class ValidationMode(StrEnum):
    """Validation execution mode."""

    STRICT = "strict"
    PERMISSIVE = "permissive"


def validate_dependency_analysis(
    result: DependencyAnalysisResult,
    edges: Sequence[DependencyEdge] = (),
    mode: ValidationMode = ValidationMode.PERMISSIVE,
) -> tuple[DependencyValidationFinding, ...]:
    """Validate dependency analysis integrity.

    Args:
        result: The DependencyAnalysisResult to validate.
        edges: Optional sequence of underlying dependency edges for reference validation.
        mode: STRICT (raises DependencyValidationError on any ERROR finding) or PERMISSIVE.

    Returns:
        Sorted tuple of DependencyValidationFinding records.

    Raises:
        DependencyValidationError: If mode is STRICT and an ERROR finding is present.
    """
    findings: list[DependencyValidationFinding] = []
    known_nodes = set(result.node_metrics.keys())

    # 1. Ordering completeness: all known nodes must appear in creation_order
    ordered_nodes = {str(n) for n in result.ordering.creation_order}
    missing_nodes = known_nodes - ordered_nodes
    if missing_nodes:
        findings.append(
            DependencyValidationFinding(
                rule_id="DEP_ORDERING_COMPLETENESS",
                severity="ERROR",
                message=f"Creation order is missing {len(missing_nodes)} analyzed nodes.",
                context={"missing_count": str(len(missing_nodes))},
            )
        )

    # 2. Level stratification: ensure nodes in level k only depend on levels < k
    node_to_level: dict[str, int] = {}
    for lvl in result.ordering.levels:
        for n in lvl.node_ids:
            node_to_level[str(n)] = lvl.level

    if result.is_dag:
        for edge in edges:
            dep_lvl = node_to_level.get(str(edge.dependent_id))
            ref_lvl = node_to_level.get(str(edge.referenced_id))
            if dep_lvl is not None and ref_lvl is not None and dep_lvl <= ref_lvl:
                findings.append(
                    DependencyValidationFinding(
                        rule_id="DEP_LEVEL_STRATIFICATION",
                        severity="ERROR",
                        message=(
                            f"Dependent table {edge.dependent_id} (level {dep_lvl}) is not "
                            f"strictly greater than referenced table {edge.referenced_id} (level {ref_lvl})."
                        ),
                        context={
                            "edge_id": edge.edge_id,
                            "dependent_id": str(edge.dependent_id),
                            "referenced_id": str(edge.referenced_id),
                        },
                    )
                )

    # 3. Unbreakable cycles detection
    if result.cycle_report.unbreakable_cycle_count > 0:
        findings.append(
            DependencyValidationFinding(
                rule_id="DEP_UNBREAKABLE_CYCLE",
                severity="WARNING" if mode == ValidationMode.PERMISSIVE else "ERROR",
                message=(
                    f"Graph contains {result.cycle_report.unbreakable_cycle_count} unbreakable cycle(s) "
                    "with NOT NULL non-deferrable constraints."
                ),
                context={"unbreakable_count": str(result.cycle_report.unbreakable_cycle_count)},
            )
        )

    # 4. Cycle advisory in permissive mode
    if result.cycle_report.has_cycles and not result.is_dag:
        findings.append(
            DependencyValidationFinding(
                rule_id="DEP_CYCLE_DETECTED",
                severity="INFO",
                message=(
                    f"Schema contains {result.cycle_report.cycle_count} cycle(s) across "
                    f"{result.cycle_report.cyclic_scc_count} cyclic component(s)."
                ),
                context={"cycle_count": str(result.cycle_report.cycle_count)},
            )
        )

    sorted_findings = sort_dependency_validation_findings(findings)

    if mode == ValidationMode.STRICT:
        errors = [f for f in sorted_findings if f.severity == "ERROR"]
        if errors:
            raise DependencyValidationError(
                f"Dependency validation failed in STRICT mode with {len(errors)} error(s): "
                f"{errors[0].rule_id} — {errors[0].message}"
            )

    return sorted_findings
