"""DERA Diagnostics — Rule DERA-MNT-007: Complex Dependency Topology.

Identifies multi-table cyclic dependency components and complex topological
structures that hinder schema migrations, transactional seeding, and long-term maintainability.
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


class ComplexDependencyTopologyRule(DiagnosticRule):
    """Audits schemas for large or intertwined cyclic dependency components."""

    DEFAULT_MIN_COMPLEX_SCC_SIZE = 3

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-MNT-007",
            title="Complex Dependency Topology",
            description=(
                "Detects strongly connected components containing 3 or more mutually dependent tables, "
                "or multi-cycle dependency groups. Complex cyclic dependencies prevent clean linear "
                "database migrations, complicate data seeding, and indicate tight schema-level coupling."
            ),
            version="1.0.0",
            category=RuleCategory.MAINTAINABILITY,
            default_severity=DiagnosticSeverity.LOW,
            supported_object_kinds=("scc", "cycle"),
            required_capabilities=("foreign_keys",),
            applicability_summary="Applies to schemas containing cyclic dependency components.",
            evidence_requirements="Requires foreign key multigraph and Tarjan SCC decomposition.",
            recommendation_template=(
                "Component '{scc_id}' forms an intertwined circular dependency among {member_count} tables: "
                "{tables}. Consider breaking the loop with a nullable foreign key or decoupling table roles."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-MNT-007",
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
                message="No relationship graph or dependency analysis available.",
            )

        cycle_report = getattr(deps, "cycle_report", None)
        if cycle_report is None or not getattr(cycle_report, "has_cycles", False):
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.PASS,
                findings=(),
                execution_duration_ms=(time.perf_counter() - start_time) * 1000,
                message="No circular dependency components exist in schema.",
            )

        min_complex_size = int(
            context.config.rule_thresholds.get(
                "min_complex_scc_size", self.DEFAULT_MIN_COMPLEX_SCC_SIZE
            )
        )
        node_map = get_table_node_map(graph)
        findings: list[DiagnosticFinding] = []

        for scc in getattr(cycle_report, "sccs", ()):
            if not getattr(scc, "is_cyclic", False):
                continue

            member_ids = list(getattr(scc, "node_ids", ()))
            member_count = len(member_ids)

            # We focus on complex multi-node cycles (size >= 3) or multi-cycle components
            cycles = list(getattr(scc, "cycles", ()))
            if member_count >= min_complex_size or len(cycles) > 1:
                sev = (
                    DiagnosticSeverity.MEDIUM
                    if member_count >= 5 or len(cycles) >= 3
                    else DiagnosticSeverity.LOW
                )

                member_names = [
                    f"{node_map[nid].namespace_name}.{node_map[nid].native_name}"
                    if nid in node_map
                    else str(nid)
                    for nid in member_ids
                ]

                primary_id = str(member_ids[0]) if member_ids else scc.scc_id
                scc_id = getattr(scc, "scc_id", primary_id)

                ev = (
                    DiagnosticEvidence(
                        object_id=primary_id,
                        field_name="complex_scc_membership",
                        observed_value=f"SCC with {member_count} tables and {len(cycles)} elementary cycles",
                        expected_value=f"Acyclic or simple component (< {min_complex_size} tables)",
                        message=(
                            f"Strongly connected component '{scc_id}' binds {member_count} tables "
                            f"({', '.join(member_names)}) into a complex circular dependency."
                        ),
                        context_data={
                            "scc_id": scc_id,
                            "member_count": member_count,
                            "member_tables": member_names,
                            "elementary_cycle_count": len(cycles),
                            "threshold": min_complex_size,
                        },
                    ),
                )

                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=primary_id,
                        severity=sev,
                        title=f"Complex Dependency Component: '{scc_id}' ({member_count} tables)",
                        description=(
                            f"Component '{scc_id}' couples {member_count} tables ({', '.join(member_names)}) "
                            f"in {len(cycles)} intertwined circular foreign key cycle(s)."
                        ),
                        evidence=ev,
                        severity_rationale=(
                            f"Component contains {member_count} tables in circular dependencies. Multi-table cycles "
                            "impede transactional migrations, prevent pure topological ordering, and indicate high coupling."
                        ),
                        recommendation=(
                            f"Refactor circular references among tables ({', '.join(member_names)}). "
                            "Make at least one foreign key nullable or introduce an intermediate link table."
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
            message=f"Evaluated cyclic components; found {len(findings)} complex dependency finding(s).",
        )
