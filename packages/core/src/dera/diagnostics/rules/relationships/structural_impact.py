"""DERA Diagnostics — Structural Change Impact Radius Rule (DERA-DEP-004).

Explores downstream transitive blast radius (reverse reachability) for database tables
to identify high-impact structural change candidates and support schema evolution planning.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from dera.diagnostics.enums import (
    DiagnosticSeverity,
    EvaluationStatus,
    RuleCategory,
)
from dera.diagnostics.evidence import DiagnosticEvidence
from dera.diagnostics.models import DiagnosticFinding, RuleEvaluation, RuleMetadata
from dera.diagnostics.protocols import DiagnosticRule
from dera.diagnostics.rules.shared.graph_helpers import (
    compute_reverse_reachability,
    get_table_node_map,
    resolve_dependencies,
    resolve_graph,
)

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


class StructuralImpactRadiusRule(DiagnosticRule):
    """Explores reverse reachability to identify tables with high downstream structural impact."""

    DEFAULT_MAX_IMPACT_RADIUS: int = 10
    DEFAULT_MAX_DEPTH: int = 10
    DEFAULT_MAX_NODES: int = 1000

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-DEP-004",
            title="Structural Change Impact Radius",
            description=(
                "Calculates downstream transitive dependency blast radius (reverse reachability) "
                "to highlight tables where schema or constraint modifications impact numerous dependent tables."
            ),
            version="1.0.0",
            category=RuleCategory.DEPENDENCIES,
            default_severity=DiagnosticSeverity.LOW,
            supported_object_kinds=("table",),
            required_capabilities=("foreign_keys",),
            applicability_summary="Applies to schemas with relationship graph topology.",
            evidence_requirements="Requires reverse reachability and transitive dependent counts.",
            recommendation_template=(
                "Review downstream impact candidates prior to altering or dropping columns in this table."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-DEP-004",
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        """Evaluates transitive blast radius across all tables using bounded reverse reachability."""
        start_time = time.perf_counter()
        graph = resolve_graph(context)
        deps = resolve_dependencies(context)

        if graph is None or deps is None:
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.INSUFFICIENT_METADATA,
                findings=(),
                execution_duration_ms=(time.perf_counter() - start_time) * 1000,
                message="No relationship graph or dependency analysis results available.",
            )

        threshold = int(
            context.config.rule_thresholds.get("max_impact_radius", self.DEFAULT_MAX_IMPACT_RADIUS)
        )
        max_depth = int(
            context.config.rule_thresholds.get("max_impact_depth", self.DEFAULT_MAX_DEPTH)
        )
        max_nodes = int(
            context.config.rule_thresholds.get("max_impact_nodes", self.DEFAULT_MAX_NODES)
        )
        node_map = get_table_node_map(graph)

        # Build downstream adjacency mapping from graph edges (referenced parent -> referencing dependent child)
        dependent_adj: dict[str, list[str]] = {n: [] for n in node_map}
        direct_dependent_counts: dict[str, int] = {n: 0 for n in node_map}
        for edge in graph.edges:
            if edge.referenced_table_id is not None:
                src_id = str(edge.source_table_id)
                ref_id = str(edge.referenced_table_id)
                if ref_id in dependent_adj:
                    if src_id not in dependent_adj[ref_id]:
                        dependent_adj[ref_id].append(src_id)
                    direct_dependent_counts[ref_id] = len(dependent_adj[ref_id])

        findings: list[DiagnosticFinding] = []

        for node_id_str, node in node_map.items():
            reachable_dependents, _ = compute_reverse_reachability(
                target_node_id=node_id_str,
                dependent_adj=dependent_adj,
                max_depth=max_depth,
                max_nodes=max_nodes,
            )
            transitive_count = len(reachable_dependents)
            direct_count = direct_dependent_counts.get(node_id_str, 0)

            if transitive_count >= threshold:
                obj_name = f"{node.namespace_name}.{node.native_name}"
                sev = (
                    DiagnosticSeverity.MEDIUM
                    if transitive_count >= threshold * 2
                    else DiagnosticSeverity.LOW
                )

                ev = (
                    DiagnosticEvidence(
                        object_id=node_id_str,
                        field_name="transitive_dependents_count",
                        observed_value=transitive_count,
                        expected_value=f"< {threshold}",
                        message=(
                            f"Table '{obj_name}' has a high structural change blast radius: "
                            f"{transitive_count} tables transitively depend on it "
                            f"(configured threshold: {threshold})."
                        ),
                        context_data={
                            "table_id": node_id_str,
                            "table_name": node.native_name,
                            "namespace": node.namespace_name,
                            "transitive_dependents_count": transitive_count,
                            "direct_dependents_count": direct_count,
                            "threshold": threshold,
                        },
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=node_id_str,
                        severity=sev,
                        title=f"High Structural Impact Radius: {obj_name}",
                        description=(
                            f"Table '{obj_name}' has a high structural change blast radius: "
                            f"{transitive_count} tables transitively depend on it "
                            f"(configured threshold: {threshold})."
                        ),
                        evidence=ev,
                        severity_rationale=(
                            f"Table '{obj_name}' has {transitive_count} downstream transitive dependents. "
                            "Modifications to its schema or primary key will cascade across this entire dependency subtree."
                        ),
                        recommendation=(
                            "Review downstream impact candidates prior to altering or dropping columns in this table."
                        ),
                    )
                )

        status = EvaluationStatus.FINDINGS_DETECTED if findings else EvaluationStatus.PASS
        sorted_findings = tuple(sorted(findings, key=lambda f: (f.object_id, f.fingerprint)))

        return RuleEvaluation(
            rule_id=self.metadata.rule_id,
            rule_version=self.metadata.version,
            status=status,
            findings=sorted_findings,
            execution_duration_ms=(time.perf_counter() - start_time) * 1000,
            message=f"Evaluated structural impact across {len(node_map)} tables; found {len(findings)} high-impact candidate(s).",
        )
