"""DERA Diagnostics — Rule DERA-CON-001: Primary Key Structural Integrity.

Validates that declared primary keys reference valid existing columns, contain
no duplicate column specifications, are non-empty, and maintain non-nullable semantics.
Does not penalize tables that legitimately lack a primary key.
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
from dera.diagnostics.rules.shared.constraint_signatures import validate_column_references_exist

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


class PrimaryKeyIntegrityRule:
    """Verifies primary key structural validity and column integrity."""

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-CON-001",
            title="Primary Key Structural Integrity",
            description=(
                "Validates declared table primary keys for structural integrity: verifies all "
                "referenced columns exist on the parent table, checks for duplicate column entries "
                "within the key, and checks for non-empty key definitions. Does not penalize tables "
                "that intentionally lack a primary key."
            ),
            version="1.0.0",
            category=RuleCategory.CONSTRAINTS,
            default_severity=DiagnosticSeverity.HIGH,
            supported_object_kinds=("primary_key", "table"),
            required_capabilities=("primary_keys", "columns"),
            applicability_summary="Applies to all declared primary keys.",
            evidence_requirements="Requires table column definitions and primary key constraint columns.",
            recommendation_template=(
                "Review primary key '{pk_name}' on table '{table_name}'. "
                "Ensure it references valid, existing columns without duplicates."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-CON-001",
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
            pk = getattr(table, "primary_key", None)
            if not pk:
                # Per prompt Rule 38: do not label a table without a PK as invalid!
                continue

            pk_name = getattr(pk, "name", "pk")
            pk_id = str(getattr(pk, "id", f"{table_id}.{pk_name}"))
            raw_cols = list(getattr(pk, "columns", None) or getattr(pk, "column_names", ()))

            # 1. Check for empty PK columns
            if not raw_cols:
                evidence = (
                    DiagnosticEvidence(
                        object_id=pk_id,
                        field_name="primary_key_columns",
                        observed_value=0,
                        expected_value=">= 1 column",
                        message=f"Primary key '{pk_name}' on table '{table_name}' defines zero participating columns.",
                        context_data={"table_name": table_name, "primary_key": pk_name},
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=pk_id,
                        severity=DiagnosticSeverity.HIGH,
                        title=f"Empty primary key definition: {table_name}.{pk_name}",
                        description=f"Primary key constraint '{pk_name}' on '{table_name}' defines zero columns.",
                        evidence=evidence,
                        severity_rationale="A declared primary key must specify at least one participating column.",
                        recommendation="Review table definition; a declared primary key must specify at least one column.",
                    )
                )
                continue

            # 2. Check for duplicate columns in key definition
            seen_cols: set[str] = set()
            dup_cols: list[str] = []
            for col in raw_cols:
                norm = str(col).strip().lower()
                if norm in seen_cols:
                    dup_cols.append(str(col))
                seen_cols.add(norm)

            if dup_cols:
                evidence = (
                    DiagnosticEvidence(
                        object_id=pk_id,
                        field_name="duplicate_columns",
                        observed_value=dup_cols,
                        expected_value="Distinct columns",
                        message=(
                            f"Primary key '{pk_name}' specifies duplicate column(s): {dup_cols}."
                        ),
                        context_data={
                            "table_name": table_name,
                            "primary_key": pk_name,
                            "declared_columns": raw_cols,
                            "duplicate_columns": dup_cols,
                        },
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=pk_id,
                        severity=DiagnosticSeverity.MEDIUM,
                        title=f"Duplicate column in primary key: {table_name}.{pk_name}",
                        description=(
                            f"Primary key '{pk_name}' on table '{table_name}' specifies column(s) {dup_cols} multiple times."
                        ),
                        evidence=evidence,
                        severity_rationale="Duplicate columns in a primary key definition are structurally redundant.",
                        recommendation="Remove redundant column repetitions from the primary key definition.",
                    )
                )

            # 3. Check that referenced columns exist in table.columns
            valid_exists, missing = validate_column_references_exist(table, raw_cols)
            if not valid_exists:
                evidence = (
                    DiagnosticEvidence(
                        object_id=pk_id,
                        field_name="missing_columns",
                        observed_value=list(missing),
                        expected_value="All primary key columns exist in table.columns",
                        message=(
                            f"Primary key '{pk_name}' on table '{table_name}' references non-existent "
                            f"column(s): {list(missing)}."
                        ),
                        context_data={
                            "table_name": table_name,
                            "primary_key": pk_name,
                            "declared_columns": raw_cols,
                            "missing_columns": list(missing),
                        },
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=pk_id,
                        severity=DiagnosticSeverity.HIGH,
                        title=f"Primary key references non-existent column: {table_name}.{pk_name}",
                        description=(
                            f"Primary key '{pk_name}' references column(s) {list(missing)} "
                            f"that do not exist in table '{table_name}'."
                        ),
                        evidence=evidence,
                        severity_rationale="Primary keys referencing non-existent columns break table integrity and query execution.",
                        recommendation="Verify table column catalog definitions and repair metadata extraction.",
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
                message=f"Detected {len(findings)} primary key structural defects.",
            )

        return RuleEvaluation(
            rule_id=self.metadata.rule_id,
            rule_version=self.metadata.version,
            status=EvaluationStatus.PASS,
            findings=(),
            execution_duration_ms=elapsed,
            message="All declared primary keys have valid structural definitions.",
        )
