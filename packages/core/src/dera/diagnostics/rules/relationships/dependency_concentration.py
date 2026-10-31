"""DERA Diagnostics — High Dependency Concentration Rule (DERA-DEP-003).

Identifies focal database tables exhibiting high dependency concentration:
either high incoming fan-in (central hub entities referenced by many tables)
or high outgoing fan-out (orchestration entities depending on many tables).
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


class DependencyConcentrationRule(DiagnosticRule):
    """Identifies tables with unusually high foreign key fan-in or fan-out concentration."""

    DEFAULT_MAX_FAN_IN: int = 8
    DEFAULT_MAX_FAN_OUT: int = 8

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-DEP-003",
            title="High Dependency Concentration",
            description=(
                "Identifies focal database tables exhibiting high incoming fan-in (central entities "
                "depended on by many tables) or high outgoing fan-out (entities referencing many tables)."
            ),
            version="1.0.0",
            category=RuleCategory.DEPENDENCIES,
            default_severity=DiagnosticSeverity.INFORMATIONAL,
            supported_object_kinds=("table",),
            required_capabilities=("foreign_keys",),
            applicability_summary="Applies to schemas with relationship graph topology.",
            evidence_requirements="Requires in-degree and out-degree dependency metrics.",
            recommendation_template=(
                "Review central hub and high fan-out consumer tables to understand architectural coupling."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-DEP-003",
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        """Evaluates fan-in and fan-out concentration across all tables."""
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

        max_fan_in = int(context.config.rule_thresholds.get("max_fan_in", self.DEFAULT_MAX_FAN_IN))
        max_fan_out = int(
            context.config.rule_thresholds.get("max_fan_out", self.DEFAULT_MAX_FAN_OUT)
        )
        node_map = get_table_node_map(graph)
        findings: list[DiagnosticFinding] = []

        for node_id_str, metrics in deps.node_metrics.items():
            node = node_map.get(node_id_str)
            if node is None:
                continue

            obj_name = f"{node.namespace_name}.{node.native_name}"

            # High Fan-In: Many tables reference this table (metrics.out_degree = dependents)
            fan_in_count = metrics.out_degree
            if fan_in_count >= max_fan_in:
                sev = (
                    DiagnosticSeverity.LOW
                    if fan_in_count >= max_fan_in * 2
                    else DiagnosticSeverity.INFORMATIONAL
                )
                ev = (
                    DiagnosticEvidence(
                        object_id=node_id_str,
                        field_name="fan_in_count",
                        observed_value=fan_in_count,
                        expected_value=f"< {max_fan_in}",
                        message=(
                            f"Table '{obj_name}' has high dependency fan-in: referenced directly by {fan_in_count} "
                            f"child tables (configured threshold: {max_fan_in})."
                        ),
                        context_data={
                            "table_id": node_id_str,
                            "table_name": node.native_name,
                            "concentration_type": "HIGH_FAN_IN",
                            "fan_in_count": fan_in_count,
                            "threshold": max_fan_in,
                            "transitive_dependents_count": metrics.transitive_dependent_count,
                        },
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=node_id_str,
                        severity=sev,
                        title=f"High Dependency Concentration (Fan-In Hub): {obj_name}",
                        description=(
                            f"Table '{obj_name}' has high dependency fan-in: referenced directly by {fan_in_count} "
                            f"child tables (configured threshold: {max_fan_in})."
                        ),
                        evidence=ev,
                        severity_rationale=(
                            f"Table '{obj_name}' is referenced by {fan_in_count} child tables. "
                            "Central hub tables are critical architectural anchors where schema alterations require coordinated downstream testing."
                        ),
                        recommendation=(
                            "Note that modifications to primary keys or column definitions in this hub table "
                            "will require validation across all referencing child tables."
                        ),
                    )
                )

            # High Fan-Out: This table references many parent tables (metrics.in_degree = dependencies)
            fan_out_count = metrics.in_degree
            if fan_out_count >= max_fan_out:
                sev = (
                    DiagnosticSeverity.LOW
                    if fan_out_count >= max_fan_out * 2
                    else DiagnosticSeverity.INFORMATIONAL
                )
                ev = (
                    DiagnosticEvidence(
                        object_id=node_id_str,
                        field_name="fan_out_count",
                        observed_value=fan_out_count,
                        expected_value=f"< {max_fan_out}",
                        message=(
                            f"Table '{obj_name}' has high dependency fan-out: references {fan_out_count} "
                            f"parent tables (configured threshold: {max_fan_out})."
                        ),
                        context_data={
                            "table_id": node_id_str,
                            "table_name": node.native_name,
                            "concentration_type": "HIGH_FAN_OUT",
                            "fan_out_count": fan_out_count,
                            "threshold": max_fan_out,
                            "transitive_dependencies_count": metrics.transitive_dependency_count,
                        },
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=node_id_str,
                        severity=sev,
                        title=f"High Dependency Concentration (Fan-Out Consumer): {obj_name}",
                        description=(
                            f"Table '{obj_name}' has high dependency fan-out: references {fan_out_count} "
                            f"parent tables (configured threshold: {max_fan_out})."
                        ),
                        evidence=ev,
                        severity_rationale=(
                            f"Table '{obj_name}' references {fan_out_count} parent tables. "
                            "High fan-out tables aggregate foreign keys from many entities, increasing insertion transaction complexity."
                        ),
                        recommendation=(
                            "Review table design to determine if multiple foreign keys represent distinct domains "
                            "or if entity responsibilities can be decomposed."
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
            message=f"Evaluated degree concentration across {len(deps.node_metrics)} tables; found {len(findings)} finding(s).",
        )
