"""DERA Diagnostics — Rule DERA-SCHEMA-004: Missing Structural Metadata.

Detects tables lacking essential canonical structural metadata, such as tables
with zero declared columns.
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


class MissingStructuralMetadataRule:
    """Validates that relational tables define essential structural metadata."""

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-SCHEMA-004",
            title="Missing Required Canonical Structural Metadata",
            description=(
                "Detects canonical tables lacking required structural definitions, "
                "such as tables having zero columns or incomplete structural metadata."
            ),
            version="1.0.0",
            category=RuleCategory.METADATA_COMPLETENESS,
            default_severity=DiagnosticSeverity.HIGH,
            supported_object_kinds=("table",),
            required_capabilities=("tables", "columns"),
            applicability_summary="Applies to all inspected database tables.",
            evidence_requirements="Requires table column counts and table ObjectIds.",
            recommendation_template=(
                "Verify whether table '{table_name}' was corrupted during reverse-engineering "
                "or if the underlying database catalog contains an empty definition."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-SCHEMA-004",
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
        tables = getattr(schema, "tables", ())

        for tbl in tables:
            tbl_id = getattr(tbl, "object_id", None) or getattr(tbl, "name", "<unnamed>")
            tbl_name = getattr(tbl, "name", "<unnamed_table>")
            columns = getattr(tbl, "columns", ())

            # Check: Table with 0 columns
            if len(columns) == 0:
                evidence = (
                    DiagnosticEvidence(
                        object_id=tbl_id,
                        field_name="columns",
                        observed_value=0,
                        expected_value=">= 1 column",
                        message=f"Table '{tbl_name}' contains zero columns in its canonical definition.",
                        context_data={"table_name": tbl_name},
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=tbl_id,
                        severity=self.metadata.default_severity,
                        title=f"Table '{tbl_name}' has no columns",
                        description=(
                            f"Canonical table '{tbl_name}' defines zero columns. "
                            "Relational tables must have at least one column."
                        ),
                        evidence=evidence,
                        severity_rationale=(
                            "A relational table without columns is invalid and indicates "
                            "either a reverse-engineering ingestion failure or a corrupted catalog entry."
                        ),
                        recommendation=self.metadata.recommendation_template.format(
                            table_name=tbl_name
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
                message=f"Detected {len(findings)} tables with missing structural metadata.",
            )

        return RuleEvaluation(
            rule_id=self.metadata.rule_id,
            rule_version=self.metadata.version,
            status=EvaluationStatus.PASS,
            findings=(),
            execution_duration_ms=elapsed,
            message="All canonical tables contain required structural column definitions.",
        )
