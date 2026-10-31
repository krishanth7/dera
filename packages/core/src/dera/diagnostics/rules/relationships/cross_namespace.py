"""DERA Diagnostics — Cross-Namespace Dependencies Rule (DERA-REL-004).

Identifies and reports foreign key relationships that span distinct schemas or namespaces,
providing visibility into schema coupling and deployment boundary dependencies.
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
from dera.diagnostics.rules.shared.graph_helpers import resolve_graph

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


class CrossNamespaceDependenciesRule(DiagnosticRule):
    """Identifies foreign key relationships spanning distinct database schemas or namespaces."""

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-REL-004",
            title="Cross-Namespace Dependency Structure",
            description=(
                "Identifies foreign key constraints that cross schema or namespace boundaries, "
                "highlighting architectural coupling and cross-schema migration dependencies."
            ),
            version="1.0.0",
            category=RuleCategory.RELATIONSHIPS,
            default_severity=DiagnosticSeverity.INFORMATIONAL,
            supported_object_kinds=("foreign_key", "table"),
            required_capabilities=("foreign_keys",),
            applicability_summary="Applies to schemas containing cross-schema foreign key relationships.",
            evidence_requirements="Requires source and referenced namespace identifiers.",
            recommendation_template=(
                "Review schema boundaries to ensure cross-namespace dependencies align with "
                "deployment and permission policies."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-REL-004",
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        """Evaluates all cross-namespace foreign key edges."""
        start_time = time.perf_counter()
        graph = resolve_graph(context)

        if graph is None:
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.INSUFFICIENT_METADATA,
                findings=(),
                execution_duration_ms=(time.perf_counter() - start_time) * 1000,
                message="No relationship graph or canonical schema available.",
            )

        findings: list[DiagnosticFinding] = []

        for edge in graph.edges:
            src_ns = edge.source_namespace.lower()
            ref_ns = edge.referenced_namespace.lower()

            if src_ns != ref_ns or edge.is_cross_namespace:
                ev = (
                    DiagnosticEvidence(
                        object_id=str(edge.object_id),
                        field_name="referenced_namespace",
                        observed_value=f"{edge.source_namespace} -> {edge.referenced_namespace}",
                        expected_value=edge.source_namespace,
                        message=(
                            f"Table '{edge.source_namespace}.{edge.source_table_name}' has foreign key '{edge.native_name}' "
                            f"referencing '{edge.referenced_namespace}.{edge.referenced_table_name}' across schema boundaries."
                        ),
                        context_data={
                            "edge_id": str(edge.object_id),
                            "foreign_key_name": edge.native_name,
                            "source_namespace": edge.source_namespace,
                            "source_table": edge.source_table_name,
                            "referenced_namespace": edge.referenced_namespace,
                            "referenced_table": edge.referenced_table_name,
                            "column_pairs": [repr(p) for p in edge.column_pairs],
                        },
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=str(edge.object_id),
                        severity=self.metadata.default_severity,
                        title=f"Cross-Namespace Foreign Key Dependency: {edge.native_name}",
                        description=(
                            f"Table '{edge.source_namespace}.{edge.source_table_name}' has foreign key '{edge.native_name}' "
                            f"referencing '{edge.referenced_namespace}.{edge.referenced_table_name}' across schema boundaries."
                        ),
                        evidence=ev,
                        severity_rationale=(
                            "Cross-namespace relationships introduce coupling across database schemas, "
                            "impacting independent schema deployments and access control boundaries."
                        ),
                        recommendation=(
                            "Review schema boundaries to ensure cross-namespace dependencies align with deployment and permission policies."
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
            message=f"Analyzed {len(graph.edges)} edges; identified {len(findings)} cross-namespace dependency link(s).",
        )
