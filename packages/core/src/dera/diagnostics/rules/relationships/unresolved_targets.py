"""DERA Diagnostics — Unresolved Relationship Targets Rule (DERA-REL-002).

Analyzes declared foreign key constraints referencing tables or namespaces
that were not resolved during catalog inspection, preserving transparency.
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


class UnresolvedRelationshipTargetsRule(DiagnosticRule):
    """Identifies declared foreign keys whose referenced target entities could not be resolved."""

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-REL-002",
            title="Unresolved Foreign Key Relationship Target",
            description=(
                "Detects foreign key constraints whose referenced parent table or namespace "
                "is absent from the inspected canonical metadata or restricted by catalog visibility."
            ),
            version="1.0.0",
            category=RuleCategory.RELATIONSHIPS,
            default_severity=DiagnosticSeverity.MEDIUM,
            supported_object_kinds=("foreign_key", "table"),
            required_capabilities=("foreign_keys",),
            applicability_summary="Applies to schemas with relationship graph metadata.",
            evidence_requirements="Requires unresolved foreign key references and target catalog details.",
            recommendation_template=(
                "Verify whether the referenced table '{referenced_table}' exists in an uninspected schema "
                "or has restricted permissions."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-REL-002",
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        """Evaluates all unresolved foreign key references in the graph."""
        start_time = time.perf_counter()
        from dera.reverse_engineering.graph.models import UnresolvedReason

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

        for ref in graph.unresolved_references:
            # Adjust severity according to reason
            if ref.reason in (
                UnresolvedReason.METADATA_RESTRICTED,
                UnresolvedReason.METADATA_INCOMPLETE,
                UnresolvedReason.UNSUPPORTED_CAPABILITY,
            ):
                sev = DiagnosticSeverity.LOW
                rationale = "Target entity is omitted due to partial inspection scope or database catalog permissions."
            elif ref.reason == UnresolvedReason.INVALID_METADATA:
                sev = DiagnosticSeverity.HIGH
                rationale = "Foreign key mapping metadata is invalid or structurally contradictory."
            else:
                sev = DiagnosticSeverity.MEDIUM
                rationale = "Declared foreign key points to a referenced table that was not found in catalog."

            target_str = f"{ref.referenced_namespace}.{ref.referenced_table_name}"
            ev = (
                DiagnosticEvidence(
                    object_id=str(ref.foreign_key_id),
                    field_name="referenced_table",
                    observed_value=f"Target '{target_str}' unresolved ({ref.reason.value})",
                    expected_value="Verified target table in canonical catalog",
                    message=(
                        f"Foreign key '{ref.native_name}' on table '{ref.source_table_name}' references target "
                        f"'{target_str}', which could not be resolved: {ref.details}"
                    ),
                    context_data={
                        "foreign_key_id": str(ref.foreign_key_id),
                        "native_name": ref.native_name,
                        "source_table": f"{ref.source_namespace}.{ref.source_table_name}",
                        "referenced_target": target_str,
                        "declared_source_columns": list(ref.declared_source_columns),
                        "declared_referenced_columns": list(ref.declared_referenced_columns),
                        "unresolved_reason": ref.reason.value,
                        "details": ref.details,
                    },
                ),
            )

            findings.append(
                DiagnosticFinding(
                    rule_id=self.metadata.rule_id,
                    rule_version=self.metadata.version,
                    object_id=str(ref.foreign_key_id),
                    severity=sev,
                    title=f"Unresolved Foreign Key Relationship Target: {ref.native_name}",
                    description=(
                        f"Foreign key '{ref.native_name}' on table '{ref.source_table_name}' references target "
                        f"'{target_str}', which could not be resolved: {ref.details}"
                    ),
                    evidence=ev,
                    severity_rationale=rationale,
                    recommendation=(
                        f"Verify whether the referenced table '{ref.referenced_table_name}' exists in an "
                        "uninspected schema or has restricted permissions."
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
            message=f"Analyzed {len(graph.unresolved_references)} unresolved reference(s); generated {len(findings)} finding(s).",
        )
