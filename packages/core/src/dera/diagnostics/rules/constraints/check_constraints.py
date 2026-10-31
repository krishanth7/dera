"""DERA Diagnostics — Rule DERA-CON-004: Check Constraint Metadata Integrity.

Inspects table CHECK constraints for structural metadata completeness.
Treats check expressions as untrusted passive strings without runtime SQL evaluation.
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
from dera.diagnostics.rules.shared.capability_checks import (
    engine_supports_check_constraints,
    normalize_engine_name,
)

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


class CheckConstraintMetadataRule:
    """Validates check constraint metadata completeness without SQL execution."""

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-CON-004",
            title="Check Constraint Metadata Integrity",
            description=(
                "Validates structural metadata of table CHECK constraints without executing expressions. "
                "Ensures declared check constraints define non-empty expression clauses, treats all SQL "
                "text as untrusted data with safe sanitization, and detects incomplete constraint metadata."
            ),
            version="1.0.0",
            category=RuleCategory.CONSTRAINTS,
            default_severity=DiagnosticSeverity.MEDIUM,
            supported_object_kinds=("check_constraint", "table"),
            required_capabilities=("check_constraints",),
            applicability_summary="Applies to database engines supporting CHECK constraints.",
            evidence_requirements="Requires CHECK constraint definitions and SQL expressions.",
            recommendation_template=(
                "Verify whether extraction failed to capture the expression for CHECK constraint '{ck_name}' "
                "on table '{table_name}'."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-CON-004",
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        start_time = time.perf_counter()
        engine = normalize_engine_name(
            getattr(context, "engine", getattr(context, "source_engine", "unknown"))
        )

        if not engine_supports_check_constraints(engine):
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.NOT_APPLICABLE,
                findings=(),
                execution_duration_ms=(time.perf_counter() - start_time) * 1000,
                message=f"Database engine '{engine}' does not enforce CHECK constraints.",
            )

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
            table_checks = list(getattr(table, "check_constraints", ()))
            sorted_checks = sorted(
                table_checks,
                key=lambda c: (getattr(c, "name", "") or "", str(getattr(c, "id", ""))),
            )

            for i, ck in enumerate(sorted_checks):
                ck_name = getattr(ck, "name", f"ck_{i}")
                ck_id = str(getattr(ck, "id", f"{table_id}.{ck_name}"))

                raw_expr = getattr(ck, "check_clause", None) or getattr(ck, "expression", None)
                raw_expr_str = str(raw_expr).strip() if raw_expr is not None else ""

                if not raw_expr_str:
                    evidence = (
                        DiagnosticEvidence(
                            object_id=ck_id,
                            field_name="check_clause",
                            observed_value="",
                            expected_value="Non-empty boolean SQL expression",
                            message=(
                                f"Check constraint '{ck_name}' on table '{table_name}' has an empty or "
                                "missing check expression clause in canonical metadata."
                            ),
                            context_data={
                                "table_name": table_name,
                                "check_constraint": ck_name,
                            },
                        ),
                    )
                    findings.append(
                        DiagnosticFinding(
                            rule_id=self.metadata.rule_id,
                            rule_version=self.metadata.version,
                            object_id=ck_id,
                            severity=DiagnosticSeverity.HIGH,
                            title=f"Empty check constraint clause: {table_name}.{ck_name}",
                            description=f"Check constraint '{ck_name}' contains no expression text.",
                            evidence=evidence,
                            severity_rationale="A CHECK constraint without an expression cannot be evaluated or reconstructed.",
                            recommendation="Verify whether inspection failed to extract the constraint expression.",
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
                message=f"Detected {len(findings)} check constraint metadata issues.",
            )

        return RuleEvaluation(
            rule_id=self.metadata.rule_id,
            rule_version=self.metadata.version,
            status=EvaluationStatus.PASS,
            findings=(),
            execution_duration_ms=elapsed,
            message="All declared check constraints contain valid metadata.",
        )
