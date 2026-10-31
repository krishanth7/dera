"""DERA Diagnostics — Composite Foreign Key Mapping Integrity Rule (DERA-REL-003).

Validates composite (multi-column) foreign key relationships for ordered ordinal alignment,
column pair count equality, and cohesive logical mapping integrity.
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


class CompositeForeignKeyMappingRule(DiagnosticRule):
    """Validates multi-column foreign key mappings for structural and ordinal integrity."""

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-REL-003",
            title="Composite Foreign Key Mapping Integrity",
            description=(
                "Validates that composite foreign keys preserve ordered 1-based ordinal positions, "
                "have equal column counts, and contain distinct source and referenced column pairs."
            ),
            version="1.0.0",
            category=RuleCategory.RELATIONSHIPS,
            default_severity=DiagnosticSeverity.HIGH,
            supported_object_kinds=("foreign_key", "table"),
            required_capabilities=("foreign_keys", "composite_foreign_keys"),
            applicability_summary="Applies to schemas containing composite foreign key relationships.",
            evidence_requirements="Requires foreign key column pair mappings and ordinal positions.",
            recommendation_template="Ensure foreign key extraction preserves 1-based column pair ordinals.",
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-REL-003",
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        """Evaluates composite foreign key mappings across all relationship edges."""
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
            if not edge.is_composite and len(edge.column_pairs) <= 1:
                continue

            pairs = edge.column_pairs
            src_cols = [p.source_column_name for p in pairs]
            ref_cols = [p.referenced_column_name for p in pairs]
            ordinals = [p.ordinal_position for p in pairs]

            # 1. Check ordinal sequence contiguous 1-based
            expected_ordinals = list(range(1, len(pairs) + 1))
            if ordinals != expected_ordinals:
                ev = (
                    DiagnosticEvidence(
                        object_id=str(edge.object_id),
                        field_name="column_pair_ordinals",
                        observed_value=ordinals,
                        expected_value=expected_ordinals,
                        message=(
                            f"Composite foreign key '{edge.native_name}' on '{edge.source_table_name}' has "
                            f"non-contiguous or non-1-based column ordinals: {ordinals}."
                        ),
                        context_data={
                            "edge_id": str(edge.object_id),
                            "foreign_key_name": edge.native_name,
                            "observed_ordinals": ordinals,
                            "expected_ordinals": expected_ordinals,
                            "column_pairs": [repr(p) for p in pairs],
                            "error_kind": "NON_CONTIGUOUS_ORDINALS",
                        },
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=str(edge.object_id),
                        severity=self.metadata.default_severity,
                        title=f"Non-Contiguous Composite Column Ordinals: {edge.native_name}",
                        description=(
                            f"Composite foreign key '{edge.native_name}' on '{edge.source_table_name}' has "
                            f"non-contiguous or non-1-based column ordinals: {ordinals}."
                        ),
                        evidence=ev,
                        severity_rationale="Composite foreign key column pairs must follow strict 1-based ordinal positions.",
                        recommendation="Ensure foreign key extraction preserves 1-based column pair ordinals.",
                    )
                )

            # 2. Check for duplicate source columns in composite mapping
            src_lower = [c.lower() for c in src_cols]
            if len(set(src_lower)) != len(src_lower):
                ev = (
                    DiagnosticEvidence(
                        object_id=str(edge.object_id),
                        field_name="source_columns",
                        observed_value=src_cols,
                        expected_value="Distinct source columns in composite mapping",
                        message=(
                            f"Composite foreign key '{edge.native_name}' on '{edge.source_table_name}' maps "
                            f"the same child column multiple times: {src_cols}."
                        ),
                        context_data={
                            "edge_id": str(edge.object_id),
                            "foreign_key_name": edge.native_name,
                            "source_columns": src_cols,
                            "error_kind": "DUPLICATE_SOURCE_COLUMNS",
                        },
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=str(edge.object_id),
                        severity=DiagnosticSeverity.CRITICAL,
                        title=f"Duplicate Source Column in Composite Foreign Key: {edge.native_name}",
                        description=(
                            f"Composite foreign key '{edge.native_name}' on '{edge.source_table_name}' maps "
                            f"the same child column multiple times: {src_cols}."
                        ),
                        evidence=ev,
                        severity_rationale="A composite foreign key cannot map the same child column multiple times.",
                        recommendation="Review the database foreign key definition to eliminate duplicate column mappings.",
                    )
                )

            # 3. Check for duplicate referenced columns in composite mapping
            ref_lower = [c.lower() for c in ref_cols]
            if len(set(ref_lower)) != len(ref_lower):
                ev = (
                    DiagnosticEvidence(
                        object_id=str(edge.object_id),
                        field_name="referenced_columns",
                        observed_value=ref_cols,
                        expected_value="Distinct referenced columns in composite mapping",
                        message=(
                            f"Composite foreign key '{edge.native_name}' on '{edge.source_table_name}' maps "
                            f"to the same referenced column multiple times: {ref_cols}."
                        ),
                        context_data={
                            "edge_id": str(edge.object_id),
                            "foreign_key_name": edge.native_name,
                            "referenced_columns": ref_cols,
                            "error_kind": "DUPLICATE_REFERENCED_COLUMNS",
                        },
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=str(edge.object_id),
                        severity=DiagnosticSeverity.CRITICAL,
                        title=f"Duplicate Target Column in Composite Foreign Key: {edge.native_name}",
                        description=(
                            f"Composite foreign key '{edge.native_name}' on '{edge.source_table_name}' maps "
                            f"to the same referenced column multiple times: {ref_cols}."
                        ),
                        evidence=ev,
                        severity_rationale="A composite foreign key cannot map multiple child columns to the same referenced column.",
                        recommendation="Correct the referenced column mapping in the composite foreign key.",
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
            message=f"Evaluated {len(graph.edges)} edges; generated {len(findings)} composite mapping finding(s).",
        )
