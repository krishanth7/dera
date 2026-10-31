"""DERA Diagnostics — Relationship Graph Integrity Rule (DERA-REL-001).

Validates that every verified foreign key edge in the relationship graph
connects valid, registered canonical table nodes and maintains structural integrity.
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
    resolve_graph,
)

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


class RelationshipGraphIntegrityRule(DiagnosticRule):
    """Detects relationship edges with dangling endpoints or corrupted canonical node references."""

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-REL-001",
            title="Relationship Graph Structural Integrity",
            description=(
                "Validates that all foreign key edges connect registered canonical table nodes "
                "and maintain non-empty column mappings and valid graph identities."
            ),
            version="1.0.0",
            category=RuleCategory.RELATIONSHIPS,
            default_severity=DiagnosticSeverity.HIGH,
            supported_object_kinds=("foreign_key", "table"),
            required_capabilities=("foreign_keys",),
            applicability_summary="Applies to schemas with relationship graph metadata.",
            evidence_requirements="Requires foreign key edges and registered graph nodes.",
            recommendation_template="Verify metadata extraction pipeline and canonical table registration.",
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-REL-001",
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        """Evaluates graph structural integrity across all nodes and edges."""
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

        for edge in graph.edges:
            # 1. Source node validation
            if edge.source_table_id not in node_map:
                ev = (
                    DiagnosticEvidence(
                        object_id=str(edge.object_id),
                        field_name="source_table_id",
                        observed_value=str(edge.source_table_id),
                        expected_value="Registered TableNode ObjectId",
                        message=(
                            f"Foreign key '{edge.native_name}' declares source table ID '{edge.source_table_id}' "
                            f"which is not registered in canonical table nodes."
                        ),
                        context_data={
                            "edge_id": str(edge.object_id),
                            "foreign_key_name": edge.native_name,
                            "source_table_id": str(edge.source_table_id),
                            "source_table_name": edge.source_table_name,
                            "source_namespace": edge.source_namespace,
                            "error_kind": "DANGLING_SOURCE_NODE",
                        },
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=str(edge.object_id),
                        severity=self.metadata.default_severity,
                        title=f"Dangling Source Node in Relationship Graph: {edge.native_name}",
                        description=(
                            f"Foreign key '{edge.native_name}' declares source table ID '{edge.source_table_id}' "
                            f"which is not registered in canonical table nodes."
                        ),
                        evidence=ev,
                        severity_rationale="Foreign key edge references a source table that does not exist in graph nodes.",
                        recommendation="Verify metadata extraction pipeline and canonical table registration.",
                    )
                )

            # 2. Referenced node validation (when resolved)
            if edge.referenced_table_id is not None and edge.referenced_table_id not in node_map:
                ev = (
                    DiagnosticEvidence(
                        object_id=str(edge.object_id),
                        field_name="referenced_table_id",
                        observed_value=str(edge.referenced_table_id),
                        expected_value="Registered TableNode ObjectId",
                        message=(
                            f"Foreign key '{edge.native_name}' on '{edge.source_table_name}' references target "
                            f"table ID '{edge.referenced_table_id}' which does not exist in graph nodes."
                        ),
                        context_data={
                            "edge_id": str(edge.object_id),
                            "foreign_key_name": edge.native_name,
                            "referenced_table_id": str(edge.referenced_table_id),
                            "referenced_table_name": edge.referenced_table_name,
                            "referenced_namespace": edge.referenced_namespace,
                            "error_kind": "DANGLING_REFERENCED_NODE",
                        },
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=str(edge.object_id),
                        severity=self.metadata.default_severity,
                        title=f"Dangling Target Node in Relationship Graph: {edge.native_name}",
                        description=(
                            f"Foreign key '{edge.native_name}' on '{edge.source_table_name}' references target "
                            f"table ID '{edge.referenced_table_id}' which does not exist in graph nodes."
                        ),
                        evidence=ev,
                        severity_rationale="Foreign key edge references a target table ID that is missing from graph nodes.",
                        recommendation="Check if target table was omitted during partial schema inspection.",
                    )
                )

            # 3. Column pair count validation
            if len(edge.column_pairs) == 0:
                ev = (
                    DiagnosticEvidence(
                        object_id=str(edge.object_id),
                        field_name="column_pairs",
                        observed_value=0,
                        expected_value=">= 1 column pair mappings",
                        message=f"Foreign key '{edge.native_name}' on '{edge.source_table_name}' contains zero column mappings.",
                        context_data={
                            "edge_id": str(edge.object_id),
                            "foreign_key_name": edge.native_name,
                            "error_kind": "EMPTY_COLUMN_MAPPING",
                        },
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=str(edge.object_id),
                        severity=DiagnosticSeverity.CRITICAL,
                        title=f"Empty Column Mapping in Relationship Edge: {edge.native_name}",
                        description=f"Foreign key '{edge.native_name}' on '{edge.source_table_name}' contains zero column mappings.",
                        evidence=ev,
                        severity_rationale="Foreign key edge has zero column pair mappings, corrupting relationship reconstruction.",
                        recommendation="Inspect connector column mapping extraction.",
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
            message=f"Analyzed {len(graph.edges)} edges; detected {len(findings)} integrity issue(s).",
        )
