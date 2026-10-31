"""DERA Diagnostics — Rule DERA-SCHEMA-001: Unresolved Relationship Target.

Detects unresolved foreign key relationship targets where the canonical model
reports missing, invalid, or restricted parent object references.
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


class UnresolvedRelationshipTargetRule:
    """Detects foreign key references pointing to unresolved target tables or schemas."""

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-SCHEMA-001",
            title="Unresolved Canonical Relationship Target",
            description=(
                "Detects foreign key constraints whose target table or referenced columns "
                "cannot be resolved within the canonical schema registry."
            ),
            version="1.0.0",
            category=RuleCategory.RELATIONSHIPS,
            default_severity=DiagnosticSeverity.HIGH,
            supported_object_kinds=("foreign_key", "table"),
            required_capabilities=("foreign_keys",),
            applicability_summary="Applies to schemas with inspected foreign key relationships.",
            evidence_requirements="Requires foreign key reference target status and table IDs.",
            recommendation_template=(
                "Verify whether the referenced table '{target_table}' was intentionally excluded "
                "from the inspection scope or represents an orphaned foreign key."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-SCHEMA-001",
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        start_time = time.perf_counter()
        schema = context.schema

        if schema is None and context.snapshot is not None:
            # If snapshot is provided without hydrated schema, check snapshot representation
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

        # If metadata completeness is restricted or partial, report insufficient metadata
        # if unresolved targets could simply stem from partial inspection scope
        completeness_str = getattr(context.completeness, "value", str(context.completeness)).lower()
        is_partial = completeness_str in ("partial", "restricted")

        fk_references = getattr(schema, "foreign_key_references", ())
        findings: list[DiagnosticFinding] = []
        has_insufficient_metadata_target = False

        for fk_ref in fk_references:
            status_val = getattr(fk_ref.status, "value", str(fk_ref.status)).lower()
            if status_val == "resolved":
                continue

            # Target is unresolved
            target_name = getattr(fk_ref, "referenced_table_name", "<unknown>")
            source_table = getattr(fk_ref, "source_table_name", "<unknown>")
            fk_name = getattr(fk_ref, "foreign_key_name", "<unnamed>")
            fk_id = getattr(fk_ref, "foreign_key_id", f"{source_table}.{fk_name}")

            if is_partial or status_val == "restricted":
                has_insufficient_metadata_target = True
                continue

            evidence = (
                DiagnosticEvidence(
                    object_id=fk_id,
                    field_name="referenced_table_name",
                    observed_value=target_name,
                    expected_value="Resolvable in schema registry",
                    message=(
                        f"Foreign key '{fk_name}' on table '{source_table}' references "
                        f"table '{target_name}' which cannot be resolved (status: {status_val})."
                    ),
                    context_data={
                        "source_table": source_table,
                        "foreign_key_name": fk_name,
                        "resolution_status": status_val,
                    },
                ),
            )

            finding = DiagnosticFinding(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                object_id=fk_id,
                severity=self.metadata.default_severity,
                title=f"Unresolved foreign key target for '{fk_name}'",
                description=(
                    f"Table '{source_table}' defines foreign key '{fk_name}' targeting "
                    f"'{target_name}', but the target is missing or invalid in the canonical registry."
                ),
                evidence=evidence,
                severity_rationale=(
                    "Dangling foreign key relationships prevent reliable DAG topological sorting "
                    "and indicate possible schema drift or orphaned constraints."
                ),
                recommendation=self.metadata.recommendation_template.format(
                    target_table=target_name
                ),
            )
            findings.append(finding)

        elapsed = (time.perf_counter() - start_time) * 1000

        if findings:
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.FINDINGS_DETECTED,
                findings=tuple(findings),
                execution_duration_ms=elapsed,
                message=f"Detected {len(findings)} unresolved relationship targets.",
            )

        if has_insufficient_metadata_target:
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.INSUFFICIENT_METADATA,
                findings=(),
                execution_duration_ms=elapsed,
                message=(
                    "Foreign key references target external or restricted schemas; "
                    "cannot confirm defect due to partial inspection scope."
                ),
            )

        return RuleEvaluation(
            rule_id=self.metadata.rule_id,
            rule_version=self.metadata.version,
            status=EvaluationStatus.PASS,
            findings=(),
            execution_duration_ms=elapsed,
            message="All foreign key references successfully resolve to registered schema objects.",
        )
