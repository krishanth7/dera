"""DERA Diagnostics — Deep Dependency Chains Rule (DERA-DEP-002).

Identifies database tables situated at the terminus of deep foreign key hierarchy chains,
which carry elevated migration sequencing complexity and operational sensitivity.
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


class DependencyDepthRule(DiagnosticRule):
    """Flags tables positioned at the end of deep dependency chains exceeding configured depth thresholds."""

    DEFAULT_MAX_DEPTH: int = 5

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-DEP-002",
            title="Deep Dependency Chain",
            description=(
                "Identifies database tables with long upstream dependency chains exceeding configured "
                "depth thresholds, highlighting hierarchy complexity and cascading change vulnerability."
            ),
            version="1.0.0",
            category=RuleCategory.DEPENDENCIES,
            default_severity=DiagnosticSeverity.INFORMATIONAL,
            supported_object_kinds=("table",),
            required_capabilities=("foreign_keys",),
            applicability_summary="Applies to schemas with relationship graph topology.",
            evidence_requirements="Requires dependency depth metrics and threshold settings.",
            recommendation_template=(
                "Consider evaluating if intermediate normalization or denormalization can simplify the dependency chain."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-DEP-002",
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        """Evaluates dependency depth across all nodes."""
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

        max_depth = int(
            context.config.rule_thresholds.get("max_dependency_depth", self.DEFAULT_MAX_DEPTH)
        )
        node_map = get_table_node_map(graph)
        findings: list[DiagnosticFinding] = []

        for node_id_str, metrics in deps.node_metrics.items():
            if metrics.depth_level >= max_depth:
                node = node_map.get(node_id_str)
                if node is None:
                    continue

                obj_name = f"{node.namespace_name}.{node.native_name}"
                sev = (
                    DiagnosticSeverity.LOW
                    if metrics.depth_level >= max_depth + 3
                    else DiagnosticSeverity.INFORMATIONAL
                )

                ev = (
                    DiagnosticEvidence(
                        object_id=node_id_str,
                        field_name="dependency_depth",
                        observed_value=metrics.depth_level,
                        expected_value=f"< {max_depth}",
                        message=(
                            f"Table '{obj_name}' is situated at dependency depth {metrics.depth_level} "
                            f"(configured threshold: {max_depth}), depending transitively on "
                            f"{metrics.transitive_dependency_count} upstream tables."
                        ),
                        context_data={
                            "table_id": node_id_str,
                            "table_name": node.native_name,
                            "namespace": node.namespace_name,
                            "depth_level": metrics.depth_level,
                            "threshold": max_depth,
                            "transitive_dependencies_count": metrics.transitive_dependency_count,
                            "direct_dependencies_count": metrics.in_degree,
                        },
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=node_id_str,
                        severity=sev,
                        title=f"Deep Dependency Chain: {obj_name}",
                        description=(
                            f"Table '{obj_name}' is situated at dependency depth {metrics.depth_level} "
                            f"(configured threshold: {max_depth}), depending transitively on "
                            f"{metrics.transitive_dependency_count} upstream tables."
                        ),
                        evidence=ev,
                        severity_rationale=(
                            f"Table '{obj_name}' has depth {metrics.depth_level} (threshold: {max_depth}). "
                            "Long dependency chains increase cascade delete latency, migration complexity, and fixture setup overhead."
                        ),
                        recommendation=(
                            "Consider evaluating if intermediate normalization or denormalization can simplify the dependency chain."
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
            message=f"Evaluated dependency depth for {len(deps.node_metrics)} nodes; found {len(findings)} deep hierarchy finding(s).",
        )
