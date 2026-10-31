"""DERA Diagnostics — Rule DERA-CON-002: Foreign Key Referential Mapping Integrity.

Validates that foreign key constraints have matching column cardinalities between
source and target, reference valid tables and columns when resolved within schema,
and preserves composite foreign keys as unified relational entities.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

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
from dera.diagnostics.rules.shared.constraint_signatures import validate_column_references_exist

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


class ForeignKeyIntegrityRule:
    """Verifies foreign key referential mapping integrity."""

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-CON-002",
            title="Foreign Key Referential Mapping Integrity",
            description=(
                "Validates referential mapping integrity of table foreign keys: ensures source and "
                "referenced column counts match, verifies child columns exist, validates referenced "
                "parent columns when the target table exists in schema, and distinguishes confirmed "
                "defects from uninspected cross-database tables."
            ),
            version="1.0.0",
            category=RuleCategory.CONSTRAINTS,
            default_severity=DiagnosticSeverity.HIGH,
            supported_object_kinds=("foreign_key", "table"),
            required_capabilities=("foreign_keys", "columns"),
            applicability_summary="Applies to all declared foreign key constraints.",
            evidence_requirements="Requires foreign key mappings, source columns, and target columns.",
            recommendation_template=(
                "Review foreign key '{fk_name}' on table '{table_name}'. "
                "Ensure source and target columns match in count and exist in their respective tables."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-CON-002",
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

        # Index tables for resolution
        table_map: dict[str, Any] = {}
        for t in sorted_tables:
            t_name = getattr(t, "name", "").lower()
            table_map[t_name] = t
            s_name = getattr(t, "schema_name", None) or getattr(t, "schema", None)
            if s_name:
                table_map[f"{str(s_name).lower()}.{t_name}"] = t

        for table in sorted_tables:
            table_name = getattr(table, "name", "<unnamed_table>")
            table_id = str(getattr(table, "id", table_name))
            table_fks = getattr(table, "foreign_keys", ())

            sorted_fks = sorted(
                table_fks,
                key=lambda fk: (getattr(fk, "name", "") or "", str(getattr(fk, "id", ""))),
            )

            for fk in sorted_fks:
                fk_name = getattr(fk, "name", "unnamed_fk")
                fk_id = str(getattr(fk, "id", f"{table_id}.{fk_name}"))

                src_cols = list(
                    getattr(fk, "source_columns", None)
                    or getattr(fk, "constrained_columns", None)
                    or getattr(fk, "column_names", ())
                )
                ref_cols = list(
                    getattr(fk, "referenced_columns", None)
                    or getattr(fk, "referred_columns", None)
                    or getattr(fk, "target_columns", ())
                )
                ref_table_name = (
                    getattr(fk, "referenced_table_name", None)
                    or getattr(fk, "referred_table", None)
                    or getattr(fk, "target_table", "")
                )
                ref_schema = getattr(fk, "referenced_schema", None) or getattr(
                    fk, "target_schema", None
                )

                # 1. Source column presence on child table
                src_valid, missing_src = validate_column_references_exist(table, src_cols)
                if not src_valid:
                    evidence = (
                        DiagnosticEvidence(
                            object_id=fk_id,
                            field_name="source_columns",
                            observed_value=list(missing_src),
                            expected_value="All source columns exist in table.columns",
                            message=(
                                f"Foreign key '{fk_name}' on table '{table_name}' references non-existent "
                                f"child column(s): {list(missing_src)}."
                            ),
                            context_data={
                                "table_name": table_name,
                                "foreign_key": fk_name,
                                "declared_source_columns": src_cols,
                                "missing_source_columns": list(missing_src),
                            },
                        ),
                    )
                    findings.append(
                        DiagnosticFinding(
                            rule_id=self.metadata.rule_id,
                            rule_version=self.metadata.version,
                            object_id=fk_id,
                            severity=DiagnosticSeverity.HIGH,
                            title=f"Foreign key child columns missing: {table_name}.{fk_name}",
                            description=(
                                f"Foreign key '{fk_name}' references child column(s) {list(missing_src)} "
                                f"which do not exist on table '{table_name}'."
                            ),
                            evidence=evidence,
                            severity_rationale="A foreign key with missing source columns cannot enforce referential integrity.",
                            recommendation="Verify table definition or repair canonical extraction.",
                        )
                    )

                # 2. Composite cardinality matching
                if ref_cols and len(src_cols) != len(ref_cols):
                    evidence = (
                        DiagnosticEvidence(
                            object_id=fk_id,
                            field_name="column_mappings",
                            observed_value={
                                "source_count": len(src_cols),
                                "referenced_count": len(ref_cols),
                            },
                            expected_value="Equal column counts",
                            message=(
                                f"Foreign key '{fk_name}' maps {len(src_cols)} source column(s) "
                                f"to {len(ref_cols)} referenced column(s)."
                            ),
                            context_data={
                                "table_name": table_name,
                                "foreign_key": fk_name,
                                "source_columns": src_cols,
                                "referenced_columns": ref_cols,
                                "referenced_table": ref_table_name,
                            },
                        ),
                    )
                    findings.append(
                        DiagnosticFinding(
                            rule_id=self.metadata.rule_id,
                            rule_version=self.metadata.version,
                            object_id=fk_id,
                            severity=DiagnosticSeverity.HIGH,
                            title=f"Foreign key column count mismatch: {table_name}.{fk_name}",
                            description=(
                                f"Foreign key '{fk_name}' maps {len(src_cols)} columns ({', '.join(src_cols)}) "
                                f"to {len(ref_cols)} columns ({', '.join(ref_cols)})."
                            ),
                            evidence=evidence,
                            severity_rationale="Composite foreign keys must have identical counts of child and parent columns.",
                            recommendation="Ensure composite foreign keys define equal numbers of source and referenced columns.",
                        )
                    )

                # 3. Referenced target table and column validation
                target_table = None
                if (
                    ref_schema
                    and f"{str(ref_schema).lower()}.{str(ref_table_name).lower()}" in table_map
                ):
                    target_table = table_map[
                        f"{str(ref_schema).lower()}.{str(ref_table_name).lower()}"
                    ]
                elif str(ref_table_name).lower() in table_map:
                    target_table = table_map[str(ref_table_name).lower()]

                if target_table is not None:
                    if ref_cols:
                        ref_valid, missing_ref = validate_column_references_exist(
                            target_table, ref_cols
                        )
                        if not ref_valid:
                            evidence = (
                                DiagnosticEvidence(
                                    object_id=fk_id,
                                    field_name="referenced_columns",
                                    observed_value=list(missing_ref),
                                    expected_value="Referenced columns exist in parent table",
                                    message=(
                                        f"Foreign key '{fk_name}' references table '{ref_table_name}', "
                                        f"but column(s) {list(missing_ref)} do not exist in '{ref_table_name}'."
                                    ),
                                    context_data={
                                        "table_name": table_name,
                                        "foreign_key": fk_name,
                                        "referenced_table": ref_table_name,
                                        "declared_referenced_columns": ref_cols,
                                        "missing_referenced_columns": list(missing_ref),
                                    },
                                ),
                            )
                            findings.append(
                                DiagnosticFinding(
                                    rule_id=self.metadata.rule_id,
                                    rule_version=self.metadata.version,
                                    object_id=fk_id,
                                    severity=DiagnosticSeverity.HIGH,
                                    title=f"Referenced parent columns missing: {table_name}.{fk_name}",
                                    description=(
                                        f"Foreign key '{fk_name}' references column(s) {list(missing_ref)} "
                                        f"that do not exist on parent table '{ref_table_name}'."
                                    ),
                                    evidence=evidence,
                                    severity_rationale="A foreign key targeting non-existent parent columns violates referential integrity.",
                                    recommendation="Verify referenced table column names and foreign key specification.",
                                )
                            )
                elif ref_table_name:
                    evidence = (
                        DiagnosticEvidence(
                            object_id=fk_id,
                            field_name="referenced_table",
                            observed_value=ref_table_name,
                            expected_value="Referenced table present in schema snapshot",
                            message=(
                                f"Foreign key '{fk_name}' references parent table '{ref_table_name}' "
                                "which is not present in the current schema snapshot."
                            ),
                            context_data={
                                "table_name": table_name,
                                "foreign_key": fk_name,
                                "referenced_table": ref_table_name,
                                "referenced_schema": ref_schema,
                            },
                        ),
                    )
                    findings.append(
                        DiagnosticFinding(
                            rule_id=self.metadata.rule_id,
                            rule_version=self.metadata.version,
                            object_id=fk_id,
                            severity=DiagnosticSeverity.LOW,
                            title=f"Unresolved referenced parent table: {table_name}.{fk_name}",
                            description=(
                                f"Foreign key '{fk_name}' targets table '{ref_table_name}' "
                                "not captured in the current schema snapshot."
                            ),
                            evidence=evidence,
                            severity_rationale="Target table may reside in an external database, uninspected schema, or restricted namespace.",
                            recommendation="Check if referenced table resides in a separate schema or uninspected catalog.",
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
                message=f"Detected {len(findings)} foreign key referential integrity findings.",
            )

        return RuleEvaluation(
            rule_id=self.metadata.rule_id,
            rule_version=self.metadata.version,
            status=EvaluationStatus.PASS,
            findings=(),
            execution_duration_ms=elapsed,
            message="All foreign keys have valid referential mappings.",
        )
