"""DERA Diagnostics — Rule DERA-IDX-004: Index Column Reference Integrity.

Validates that all column names referenced in table index definitions actually
exist in the parent table's canonical column collection.
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


class IndexColumnIntegrityRule:
    """Verifies that all columns declared in indexes exist on the parent table."""

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-IDX-004",
            title="Index Column Reference Integrity",
            description=(
                "Validates that column names specified in table index definitions exist in the "
                "table's canonical column collection. Mismatches indicate metadata corruption or extraction failure."
            ),
            version="1.0.0",
            category=RuleCategory.INDEXES,
            default_severity=DiagnosticSeverity.HIGH,
            supported_object_kinds=("index", "table"),
            required_capabilities=("indexes", "columns"),
            applicability_summary="Applies to all inspected table indexes.",
            evidence_requirements="Requires table column names and index term columns.",
            recommendation_template=(
                "Verify whether column(s) {missing_columns} were dropped or renamed, or if "
                "metadata extraction suffered partial corruption."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-IDX-004",
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

        tables = getattr(schema, "tables", ())
        if not tables:
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.PASS,
                findings=(),
                execution_duration_ms=(time.perf_counter() - start_time) * 1000,
                message="No tables present in schema.",
            )

        findings: list[DiagnosticFinding] = []
        sorted_tables = sorted(
            tables, key=lambda t: (getattr(t, "name", ""), str(getattr(t, "id", "")))
        )

        for table in sorted_tables:
            table_name = getattr(table, "name", "<unnamed_table>")
            table_id = str(getattr(table, "id", table_name))
            existing_cols: set[str] = {
                str(getattr(c, "name", c)).strip().lower()
                for c in (getattr(table, "columns", ()) or [])
            }
            indexes = getattr(table, "indexes", ())

            sorted_indexes = sorted(
                indexes,
                key=lambda idx: (getattr(idx, "name", ""), str(getattr(idx, "id", ""))),
            )

            for idx in sorted_indexes:
                idx_name = getattr(idx, "name", "unnamed_index")
                idx_id = str(getattr(idx, "id", f"{table_id}.{idx_name}"))

                # Gather explicit column references
                idx_terms = getattr(idx, "terms", None)
                if idx_terms:
                    ref_cols = [
                        t.column_name
                        for t in idx_terms
                        if getattr(t, "column_name", None)
                        and not getattr(t, "is_expression", False)
                    ]
                else:
                    ref_cols = list(
                        getattr(idx, "columns", None) or getattr(idx, "column_names", ())
                    )

                missing_cols = [c for c in ref_cols if str(c).strip().lower() not in existing_cols]

                if missing_cols:
                    evidence = (
                        DiagnosticEvidence(
                            object_id=idx_id,
                            field_name="index_columns",
                            observed_value=missing_cols,
                            expected_value="All indexed columns exist in table.columns",
                            message=(
                                f"Index '{idx_name}' on table '{table_name}' references non-existent "
                                f"column(s): {missing_cols}."
                            ),
                            context_data={
                                "table_id": table_id,
                                "table_name": table_name,
                                "index_id": idx_id,
                                "index_name": idx_name,
                                "declared_index_columns": ref_cols,
                                "missing_columns": missing_cols,
                                "table_columns": sorted(list(existing_cols)),
                            },
                        ),
                    )

                    findings.append(
                        DiagnosticFinding(
                            rule_id=self.metadata.rule_id,
                            rule_version=self.metadata.version,
                            object_id=idx_id,
                            severity=self.metadata.default_severity,
                            title=f"Index references missing column: {table_name}.{idx_name}",
                            description=(
                                f"Index '{idx_name}' on table '{table_name}' references column(s) "
                                f"{missing_cols} which do not exist in the canonical table definition."
                            ),
                            evidence=evidence,
                            severity_rationale=(
                                "An index pointing to non-existent columns indicates a corrupted database catalog "
                                "or schema reconstruction failure, which causes DDL and query failures."
                            ),
                            recommendation=(
                                f"Review index '{idx_name}' on table '{table_name}'. Verify whether column(s) "
                                f"{missing_cols} were dropped or renamed."
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
                message=f"Detected {len(findings)} indexes referencing non-existent columns.",
            )

        return RuleEvaluation(
            rule_id=self.metadata.rule_id,
            rule_version=self.metadata.version,
            status=EvaluationStatus.PASS,
            findings=(),
            execution_duration_ms=elapsed,
            message="All indexed columns exist in table definitions.",
        )
