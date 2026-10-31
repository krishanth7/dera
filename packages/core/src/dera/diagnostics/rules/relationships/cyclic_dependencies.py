"""DERA Diagnostics — Circular Dependencies & Strongly Connected Components (DERA-DEP-001).

Identifies circular foreign key dependency groups and self-referencing loops,
evaluating their impact on topological ordering and insertion flows.
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


class CyclicDependenciesRule(DiagnosticRule):
    """Detects circular dependency groups and self-referential foreign keys using Tarjan's SCC algorithm."""

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-DEP-001",
            title="Circular Foreign Key Dependencies & SCCs",
            description=(
                "Detects cyclic dependency groups and self-referencing foreign keys using Tarjan's "
                "strongly connected components algorithm, explaining topological insertion implications."
            ),
            version="1.0.0",
            category=RuleCategory.DEPENDENCIES,
            default_severity=DiagnosticSeverity.MEDIUM,
            supported_object_kinds=("foreign_key", "table"),
            required_capabilities=("foreign_keys",),
            applicability_summary="Applies to schemas with relationship graph topology.",
            evidence_requirements="Requires strongly connected component cycle member identifiers.",
            recommendation_template=(
                "Ensure at least one foreign key in the loop is nullable or DEFERRABLE "
                "to allow transactional batch insertion."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-DEP-001",
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        """Evaluates cyclic SCCs and elementary cycles across the schema."""
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

        if len(graph.nodes) == 0:
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.PASS,
                findings=(),
                execution_duration_ms=(time.perf_counter() - start_time) * 1000,
                message="Graph contains zero table nodes.",
            )

        node_map = get_table_node_map(graph)
        findings: list[DiagnosticFinding] = []

        for scc in deps.cycle_report.sccs:
            if not scc.is_cyclic:
                continue

            member_names = [
                f"{node_map[nid].namespace_name}.{node_map[nid].native_name}"
                if nid in node_map
                else str(nid)
                for nid in scc.node_ids
            ]
            primary_object_id = str(scc.node_ids[0]) if scc.node_ids else scc.scc_id
            primary_object_name = member_names[0] if member_names else "unknown"

            is_self_loop = len(scc.node_ids) == 1 and scc.is_cyclic
            if is_self_loop:
                ev = (
                    DiagnosticEvidence(
                        object_id=primary_object_id,
                        field_name="self_referential_fk",
                        observed_value=f"Self-referencing table: {primary_object_name}",
                        expected_value="Acyclic relationship or nullable self-reference",
                        message=(
                            f"Table '{primary_object_name}' contains a self-referencing foreign key. "
                            "Ensure the parent foreign key column is nullable to allow tree root insertion."
                        ),
                        context_data={
                            "scc_id": scc.scc_id,
                            "cycle_type": "SELF_LOOP",
                            "table_name": primary_object_name,
                            "node_id": primary_object_id,
                        },
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=primary_object_id,
                        severity=DiagnosticSeverity.LOW,
                        title=f"Self-Referencing Foreign Key: {primary_object_name}",
                        description=(
                            f"Table '{primary_object_name}' contains a self-referencing foreign key. "
                            "Ensure the parent foreign key column is nullable to allow tree root insertion."
                        ),
                        evidence=ev,
                        severity_rationale="Self-referencing foreign keys require nullable columns or root rows with NULL parents.",
                        recommendation=(
                            "Ensure the foreign key column is nullable or deferrable to allow inserting initial root records."
                        ),
                    )
                )
            else:
                cycle_paths = [
                    [
                        f"{node_map[nid].namespace_name}.{node_map[nid].native_name}"
                        if nid in node_map
                        else str(nid)
                        for nid in c.node_ids
                    ]
                    for c in scc.cycles
                ]
                ev = (
                    DiagnosticEvidence(
                        object_id=primary_object_id,
                        field_name="scc_cycle_membership",
                        observed_value=f"Cycle among {len(scc.node_ids)} tables: {', '.join(member_names)}",
                        expected_value="Directed Acyclic Graph (DAG) for unconstrained topological sequencing",
                        message=(
                            f"Strongly connected component '{scc.scc_id}' forms a circular dependency among "
                            f"{len(scc.node_ids)} tables: {', '.join(member_names)}."
                        ),
                        context_data={
                            "scc_id": scc.scc_id,
                            "cycle_type": "MULTI_NODE_SCC",
                            "member_count": len(scc.node_ids),
                            "member_tables": member_names,
                            "elementary_cycles": cycle_paths,
                        },
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=primary_object_id,
                        severity=self.metadata.default_severity,
                        title=f"Circular Foreign Key Dependency: {scc.scc_id}",
                        description=(
                            f"Strongly connected component '{scc.scc_id}' forms a circular dependency among "
                            f"{len(scc.node_ids)} tables: {', '.join(member_names)}."
                        ),
                        evidence=ev,
                        severity_rationale=(
                            "Circular dependencies prevent simple linear topological sorting. "
                            "Insertion and truncation require deferrable constraints or nullable foreign key breakages."
                        ),
                        recommendation=(
                            "Review circular dependencies. Ensure at least one foreign key in the loop is nullable "
                            "or DEFERRABLE to allow transactional batch insertion and migration execution."
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
            message=f"Evaluated {len(deps.cycle_report.sccs)} strongly connected components; found {len(findings)} cycle finding(s).",
        )
