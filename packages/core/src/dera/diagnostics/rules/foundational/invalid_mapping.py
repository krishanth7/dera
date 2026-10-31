"""DERA Diagnostics — Rule DERA-SCHEMA-003: Invalid Relationship Mapping.

Validates foreign key column mappings, ensuring equal column cardinality and
consistent composite column pairings between referencing and referenced tables.
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
from dera.diagnostics.models import (
    DiagnosticFinding,
    RuleEvaluation,
    RuleMetadata,
)

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


class InvalidRelationshipMappingRule:
    """Validates cardinality and alignment of foreign key column mappings."""

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-SCHEMA-003",
            title="Invalid Canonical Relationship Mapping",
            description=(
                "Validates foreign key column mappings, ensuring non-empty column specifications "
                "and equal cardinality between source and referenced columns."
            ),
            version="1.0.0",
            category=RuleCategory.RELATIONSHIPS,
            default_severity=DiagnosticSeverity.HIGH,
            supported_object_kinds=("foreign_key", "table"),
            required_capabilities=("foreign_keys",),
            applicability_summary="Applies to all inspected foreign key constraints.",
            evidence_requirements="Requires source columns and target columns ordered tuples.",
            recommendation_template=(
                "Ensure foreign key constraint '{fk_name}' defines matching source and target columns."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-SCHEMA-003",
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        start_time = time.perf_counter()
        schema = context.schema

        if schema is None and context.snapshot is not None:
            schema = getattr(context.snapshot, "schema_representation", None)

        if schema is None:
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.INSUFFICIENT_METADATA,
                findings=(),
                execution_duration_ms=(time.perf_counter() - start_time) * 1000,
                message="No schema representation available in diagnostic context.",
            )

        findings: list[DiagnosticFinding] = []
        fk_references = getattr(schema, "foreign_key_references", ())

        for fk_ref in fk_references:
            source_cols = tuple(getattr(fk_ref, "source_columns", ()))
            target_cols = tuple(getattr(fk_ref, "referenced_columns", ()))
            fk_name = getattr(fk_ref, "foreign_key_name", "<unnamed_fk>")
            fk_id = getattr(fk_ref, "foreign_key_id", fk_name)
            source_table = getattr(fk_ref, "source_table_name", "<unknown>")
            target_table = getattr(fk_ref, "referenced_table_name", "<unknown>")

            # Check 1: Empty column mappings
            if len(source_cols) == 0 or len(target_cols) == 0:
                evidence = (
                    DiagnosticEvidence(
                        object_id=fk_id,
                        field_name="column_mappings",
                        observed_value=f"source_cols={source_cols}, target_cols={target_cols}",
                        expected_value="At least one column pairing in foreign key mapping",
                        message=(
                            f"Foreign key '{fk_name}' on table '{source_table}' contains empty column definitions."
                        ),
                        context_data={
                            "source_columns": list(source_cols),
                            "referenced_columns": list(target_cols),
                        },
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=fk_id,
                        severity=self.metadata.default_severity,
                        title=f"Empty column mapping in foreign key '{fk_name}'",
                        description=(
                            f"Foreign key '{fk_name}' between '{source_table}' and '{target_table}' "
                            f"defines zero source or target columns."
                        ),
                        evidence=evidence,
                        severity_rationale=(
                            "A relational foreign key constraint cannot function without referencing columns."
                        ),
                        recommendation=self.metadata.recommendation_template.format(
                            fk_name=fk_name
                        ),
                    )
                )
                continue

            # Check 2: Cardinality mismatch in composite foreign key
            if len(source_cols) != len(target_cols):
                evidence = (
                    DiagnosticEvidence(
                        object_id=fk_id,
                        field_name="column_cardinality",
                        observed_value=f"{len(source_cols)} source vs {len(target_cols)} target columns",
                        expected_value=f"Equal column counts (expected {len(source_cols)})",
                        message=(
                            f"Foreign key '{fk_name}' has mismatched column counts: "
                            f"source ({list(source_cols)}) has {len(source_cols)} columns, "
                            f"target ({list(target_cols)}) has {len(target_cols)} columns."
                        ),
                        context_data={
                            "source_columns": list(source_cols),
                            "referenced_columns": list(target_cols),
                        },
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=fk_id,
                        severity=self.metadata.default_severity,
                        title=f"Mismatched column count in foreign key '{fk_name}'",
                        description=(
                            f"Composite foreign key '{fk_name}' maps {len(source_cols)} source columns "
                            f"to {len(target_cols)} target columns."
                        ),
                        evidence=evidence,
                        severity_rationale=(
                            "Composite foreign keys require an identical number of source and target columns "
                            "for relational referential integrity."
                        ),
                        recommendation=self.metadata.recommendation_template.format(
                            fk_name=fk_name
                        ),
                    )
                )

        elapsed = (time.perf_counter() - start_time) * 1000

        if findings:
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.FINDINGS_DETECTED,
                findings=tuple(findings),
                execution_duration_ms=elapsed,
                message=f"Detected {len(findings)} invalid relationship mappings.",
            )

        return RuleEvaluation(
            rule_id=self.metadata.rule_id,
            rule_version=self.metadata.version,
            status=EvaluationStatus.PASS,
            findings=(),
            execution_duration_ms=elapsed,
            message="All foreign key relationship mappings have valid, matching column specifications.",
        )
