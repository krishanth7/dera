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
    get_table_node_map,
    resolve_dependencies,
    resolve_graph,
)

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


class StructuralImpactRadiusRule(DiagnosticRule):
    """Explores reverse reachability to identify tables with high downstream structural impact."""

    DEFAULT_MAX_IMPACT_RADIUS: int = 10

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
            default_severity=DiagnosticSeverity.INFORMATIONAL,
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
        """Evaluates transitive blast radius across all tables."""
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
        node_map = get_table_node_map(graph)
        findings: list[DiagnosticFinding] = []

        for node_id_str, metrics in deps.node_metrics.items():
            if metrics.transitive_dependent_count >= threshold:
                node = node_map.get(node_id_str)
                if node is None:
                    continue

                obj_name = f"{node.namespace_name}.{node.native_name}"
                sev = (
                    DiagnosticSeverity.LOW
                    if metrics.transitive_dependent_count >= threshold * 2
                    else DiagnosticSeverity.INFORMATIONAL
                )

                ev = (
                    DiagnosticEvidence(
                        object_id=node_id_str,
                        field_name="transitive_dependents_count",
                        observed_value=metrics.transitive_dependent_count,
                        expected_value=f"< {threshold}",
                        message=(
                            f"Table '{obj_name}' has a high structural change blast radius: "
                            f"{metrics.transitive_dependent_count} tables transitively depend on it "
                            f"(configured threshold: {threshold})."
                        ),
                        context_data={
                            "table_id": node_id_str,
                            "table_name": node.native_name,
                            "namespace": node.namespace_name,
                            "transitive_dependents_count": metrics.transitive_dependent_count,
                            "direct_dependents_count": metrics.out_degree,
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
                            f"{metrics.transitive_dependent_count} tables transitively depend on it "
                            f"(configured threshold: {threshold})."
                        ),
                        evidence=ev,
                        severity_rationale=(
                            f"Table '{obj_name}' has {metrics.transitive_dependent_count} downstream transitive dependents. "
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
            message=f"Evaluated structural impact across {len(deps.node_metrics)} tables; found {len(findings)} high-impact candidate(s).",
        )
