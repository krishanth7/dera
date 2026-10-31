"""DERA Diagnostics — Rule DERA-CON-005: Constraint Column Integrity.

Comprehensive audit verifying that all columns declared in any table constraint
(Primary Key, Unique Constraints, Foreign Keys) exist within the table's canonical column list.
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


class ConstraintColumnIntegrityRule:
    """Validates all constraint column references against table columns."""

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-CON-005",
            title="Constraint Column Integrity",
            description=(
                "Performs an audit ensuring all column references across all declared constraints "
                "(Primary Key, Foreign Keys, Unique Constraints) exist in the parent table's canonical "
                "column collection. Flags internal metadata desynchronization."
            ),
            version="1.0.0",
            category=RuleCategory.CONSTRAINTS,
            default_severity=DiagnosticSeverity.HIGH,
            supported_object_kinds=("constraint", "table"),
            required_capabilities=("constraints", "columns"),
            applicability_summary="Applies to all declared table constraints.",
            evidence_requirements="Requires table column definitions and constraint column references.",
            recommendation_template=(
                "Review constraint '{constraint_name}' on table '{table_name}'. "
                "Ensure referenced columns {missing_columns} exist in the table definition."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-CON-005",
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
            table_cols: set[str] = {
                str(getattr(c, "name", c)).strip().lower()
                for c in (getattr(table, "columns", ()) or [])
            }

            # 1. Primary Key columns
            pk = getattr(table, "primary_key", None)
            if pk:
                pk_cols = list(getattr(pk, "columns", None) or getattr(pk, "column_names", ()))
                missing = [col for col in pk_cols if str(col).strip().lower() not in table_cols]
                if missing:
                    pk_name = getattr(pk, "name", "pk")
                    pk_id = str(getattr(pk, "id", f"{table_id}.{pk_name}"))
                    evidence = (
                        DiagnosticEvidence(
                            object_id=pk_id,
                            field_name="primary_key_columns",
                            observed_value=missing,
                            expected_value="All PK columns exist in table.columns",
                            message=(
                                f"Primary key '{pk_name}' on table '{table_name}' references "
                                f"column(s) {missing} which do not exist in the table's column definitions."
                            ),
                            context_data={
                                "table_name": table_name,
                                "constraint_name": pk_name,
                                "constraint_type": "PRIMARY_KEY",
                                "missing_columns": missing,
                            },
                        ),
                    )
                    findings.append(
                        DiagnosticFinding(
                            rule_id=self.metadata.rule_id,
                            rule_version=self.metadata.version,
                            object_id=pk_id,
                            severity=self.metadata.default_severity,
                            title=f"Primary key references missing column: {table_name}.{pk_name}",
                            description=(
                                f"Primary key '{pk_name}' on table '{table_name}' references missing column(s): "
                                f"{', '.join(missing)}."
                            ),
                            evidence=evidence,
                            severity_rationale="A primary key referencing missing columns indicates catalog corruption.",
                            recommendation="Check for dropped or renamed table columns or metadata extraction failure.",
                        )
                    )

            # 2. Unique Constraints
            for uq in getattr(table, "unique_constraints", ()):
                uq_name = getattr(uq, "name", "uq")
                uq_id = str(getattr(uq, "id", f"{table_id}.{uq_name}"))
                uq_cols = list(getattr(uq, "columns", None) or getattr(uq, "column_names", ()))
                missing = [col for col in uq_cols if str(col).strip().lower() not in table_cols]
                if missing:
                    evidence = (
                        DiagnosticEvidence(
                            object_id=uq_id,
                            field_name="unique_columns",
                            observed_value=missing,
                            expected_value="All UNIQUE columns exist in table.columns",
                            message=(
                                f"Unique constraint '{uq_name}' on table '{table_name}' references "
                                f"column(s) {missing} which do not exist in the table's column definitions."
                            ),
                            context_data={
                                "table_name": table_name,
                                "constraint_name": uq_name,
                                "constraint_type": "UNIQUE",
                                "missing_columns": missing,
                            },
                        ),
                    )
                    findings.append(
                        DiagnosticFinding(
                            rule_id=self.metadata.rule_id,
                            rule_version=self.metadata.version,
                            object_id=uq_id,
                            severity=self.metadata.default_severity,
                            title=f"Unique constraint references missing column: {table_name}.{uq_name}",
                            description=(
                                f"Unique constraint '{uq_name}' on table '{table_name}' references missing column(s): "
                                f"{', '.join(missing)}."
                            ),
                            evidence=evidence,
                            severity_rationale="Unique constraints referencing missing columns fail enforcement and export.",
                            recommendation="Verify table column list against database catalog.",
                        )
                    )

            # 3. Foreign Keys (source columns)
            for fk in getattr(table, "foreign_keys", ()):
                fk_name = getattr(fk, "name", "fk")
                fk_id = str(getattr(fk, "id", f"{table_id}.{fk_name}"))
                fk_cols = list(
                    getattr(fk, "source_columns", None)
                    or getattr(fk, "constrained_columns", None)
                    or getattr(fk, "column_names", ())
                )
                missing = [col for col in fk_cols if str(col).strip().lower() not in table_cols]
                if missing:
                    evidence = (
                        DiagnosticEvidence(
                            object_id=fk_id,
                            field_name="foreign_key_columns",
                            observed_value=missing,
                            expected_value="All FK source columns exist in table.columns",
                            message=(
                                f"Foreign key '{fk_name}' on table '{table_name}' references child "
                                f"column(s) {missing} which do not exist in the table."
                            ),
                            context_data={
                                "table_name": table_name,
                                "constraint_name": fk_name,
                                "constraint_type": "FOREIGN_KEY",
                                "missing_columns": missing,
                            },
                        ),
                    )
                    findings.append(
                        DiagnosticFinding(
                            rule_id=self.metadata.rule_id,
                            rule_version=self.metadata.version,
                            object_id=fk_id,
                            severity=self.metadata.default_severity,
                            title=f"Foreign key references missing column: {table_name}.{fk_name}",
                            description=(
                                f"Foreign key '{fk_name}' references missing child column(s): {', '.join(missing)}."
                            ),
                            evidence=evidence,
                            severity_rationale="A foreign key with non-existent source columns violates relational model integrity.",
                            recommendation="Review child table foreign key specification.",
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
                message=f"Detected {len(findings)} constraint column integrity issues.",
            )

        return RuleEvaluation(
            rule_id=self.metadata.rule_id,
            rule_version=self.metadata.version,
            status=EvaluationStatus.PASS,
            findings=(),
            execution_duration_ms=elapsed,
            message="All constraints reference valid existing table columns.",
        )
