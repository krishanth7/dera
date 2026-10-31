"""DERA Diagnostics — Rule DERA-MNT-006: High Relationship Structural Coupling.

Identifies tables with unusually high combined relational coupling (fan-in + fan-out degree)
that serve as centralized architectural bottlenecks.
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
from dera.diagnostics.metrics.coupling_metrics import compute_all_coupling_metrics
from dera.diagnostics.models import DiagnosticFinding, RuleEvaluation, RuleMetadata
from dera.diagnostics.protocols import DiagnosticRule
from dera.diagnostics.rules.shared.graph_helpers import resolve_dependencies, resolve_graph

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


class StructuralCouplingRule(DiagnosticRule):
    """Audits relational tables for excessive combined structural coupling."""

    DEFAULT_MAX_COUPLING = 12

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-MNT-006",
            title="High Relationship Structural Coupling",
            description=(
                "Detects relational tables with high combined foreign key relationships (sum of incoming "
                "referencing children and outgoing referenced parents). Highly coupled tables form structural "
                "chokepoints where schema alterations, index updates, or locking cascade across many entities."
            ),
            version="1.0.0",
            category=RuleCategory.MAINTAINABILITY,
            default_severity=DiagnosticSeverity.LOW,
            supported_object_kinds=("table",),
            required_capabilities=("foreign_keys",),
            applicability_summary="Applies to all tables in schemas with foreign key relationships.",
            evidence_requirements="Requires foreign key multigraph and topological dependency metrics.",
            recommendation_template=(
                "Table '{table_name}' has {total_degree} combined relationships ({out_degree} incoming children, "
                "{in_degree} outgoing parents). Evaluate decoupling options to reduce architectural blast radius."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-MNT-006",
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
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
                message="No relationship graph or dependency metrics available.",
            )

        threshold = int(
            context.config.rule_thresholds.get("max_structural_coupling", self.DEFAULT_MAX_COUPLING)
        )
        elevated_threshold = threshold * 2

        coupling_metrics = compute_all_coupling_metrics(graph, deps)
        findings: list[DiagnosticFinding] = []

        for m in coupling_metrics:
            if m.total_degree >= threshold:
                sev = (
                    DiagnosticSeverity.MEDIUM
                    if m.total_degree >= elevated_threshold
                    else DiagnosticSeverity.LOW
                )

                ev = (
                    DiagnosticEvidence(
                        object_id=m.node_id,
                        field_name="total_degree",
                        observed_value=m.total_degree,
                        expected_value=f"< {threshold}",
                        message=(
                            f"Table '{m.table_name}' has combined degree of {m.total_degree} "
                            f"({m.out_degree} incoming children, {m.in_degree} outgoing parents; threshold: {threshold})."
                        ),
                        context_data={
                            "table_id": m.node_id,
                            "table_name": m.table_name,
                            "total_degree": m.total_degree,
                            "incoming_children": m.out_degree,
                            "outgoing_parents": m.in_degree,
                            "is_in_cycle": m.is_in_cycle,
                            "transitive_dependents": m.transitive_dependents_count,
                            "threshold": threshold,
                        },
                    ),
                )

                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=m.node_id,
                        severity=sev,
                        title=f"High Structural Coupling: '{m.table_name}' ({m.total_degree} relationships)",
                        description=(
                            f"Table '{m.table_name}' participates in {m.total_degree} direct foreign key relationships "
                            f"({m.out_degree} child tables depend on it; it depends on {m.in_degree} parent tables), "
                            f"exceeding the maintainability threshold of {threshold}."
                        ),
                        evidence=ev,
                        severity_rationale=(
                            f"Table has {m.total_degree} combined relationships. Modifications to this table's schema "
                            "cascade across all connected entities, increasing testing and migration risks."
                        ),
                        recommendation=(
                            f"Review coupling on table '{m.table_name}'. Consider event-driven decoupling, "
                            "view encapsulation, or bounded context refactoring to reduce direct relational links."
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
            message=f"Evaluated structural coupling for {len(coupling_metrics)} tables; found {len(findings)} finding(s).",
        )
