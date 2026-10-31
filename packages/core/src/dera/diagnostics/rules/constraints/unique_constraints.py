"""DERA Diagnostics — Rule DERA-CON-003: Unique Constraint Structural Integrity.

Validates that unique constraints define non-empty columns, detects duplicate
unique constraint declarations on identical column sets, and identifies unique
constraints that duplicate the table's primary key.
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
from dera.diagnostics.rules.shared.constraint_signatures import (
    are_unique_constraints_duplicate,
    does_unique_constraint_duplicate_pk,
)

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


class UniqueConstraintIntegrityRule:
    """Analyzes table unique constraints for redundancy and structural validity."""

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-CON-003",
            title="Unique Constraint Structural Integrity",
            description=(
                "Validates declared table unique constraints: ensures participating columns are non-empty, "
                "detects redundant unique constraints that duplicate the primary key, "
                "and detects duplicate unique constraints declaring identical column sets."
            ),
            version="1.0.0",
            category=RuleCategory.CONSTRAINTS,
            default_severity=DiagnosticSeverity.MEDIUM,
            supported_object_kinds=("unique_constraint", "table"),
            required_capabilities=("unique_constraints", "columns"),
            applicability_summary="Applies to all declared UNIQUE constraints.",
            evidence_requirements="Requires unique constraint definitions, column lists, and primary key metadata.",
            recommendation_template=(
                "Review unique constraint '{uq_name}' on table '{table_name}'. "
                "Consolidate duplicate constraints to avoid redundant index overhead."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-CON-003",
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
            table_uqs = list(getattr(table, "unique_constraints", ()))
            sorted_uqs = sorted(
                table_uqs,
                key=lambda u: (getattr(u, "name", "") or "", str(getattr(u, "id", ""))),
            )

            # Check individual unique constraints
            for i, uq in enumerate(sorted_uqs):
                uq_name = getattr(uq, "name", f"uq_{i}")
                uq_id = str(getattr(uq, "id", f"{table_id}.{uq_name}"))
                uq_cols = list(getattr(uq, "columns", None) or getattr(uq, "column_names", ()))

                # 1. Non-empty check
                if not uq_cols:
                    evidence = (
                        DiagnosticEvidence(
                            object_id=uq_id,
                            field_name="unique_columns",
                            observed_value=0,
                            expected_value=">= 1 column",
                            message=f"Unique constraint '{uq_name}' on table '{table_name}' defines zero participating columns.",
                            context_data={"table_name": table_name, "unique_constraint": uq_name},
                        ),
                    )
                    findings.append(
                        DiagnosticFinding(
                            rule_id=self.metadata.rule_id,
                            rule_version=self.metadata.version,
                            object_id=uq_id,
                            severity=DiagnosticSeverity.HIGH,
                            title=f"Empty unique constraint definition: {table_name}.{uq_name}",
                            description=f"Unique constraint '{uq_name}' defines no columns.",
                            evidence=evidence,
                            severity_rationale="A declared UNIQUE constraint must specify at least one column.",
                            recommendation="Review table definition; unique constraint must specify at least one column.",
                        )
                    )
                    continue

                # 2. Check for duplicate of Primary Key
                if does_unique_constraint_duplicate_pk(table, uq):
                    pk_name = getattr(table.primary_key, "name", "PRIMARY KEY")
                    cols_str = ", ".join(uq_cols)
                    evidence = (
                        DiagnosticEvidence(
                            object_id=uq_id,
                            field_name="unique_columns",
                            observed_value=f"Duplicates PK ({cols_str})",
                            expected_value="Distinct key columns from primary key",
                            message=(
                                f"Unique constraint '{uq_name}' enforces uniqueness on ({cols_str}), "
                                f"which is already guaranteed by primary key '{pk_name}'."
                            ),
                            context_data={
                                "table_name": table_name,
                                "unique_constraint": uq_name,
                                "columns": uq_cols,
                                "primary_key": pk_name,
                            },
                        ),
                    )
                    findings.append(
                        DiagnosticFinding(
                            rule_id=self.metadata.rule_id,
                            rule_version=self.metadata.version,
                            object_id=uq_id,
                            severity=DiagnosticSeverity.LOW,
                            title=f"Unique constraint duplicates primary key: {table_name}.{uq_name}",
                            description=(
                                f"Unique constraint '{uq_name}' on columns ({cols_str}) "
                                f"duplicates the existing primary key '{pk_name}'."
                            ),
                            evidence=evidence,
                            severity_rationale="Primary keys inherently enforce uniqueness, rendering an identical unique constraint redundant.",
                            recommendation="Review whether this explicit unique constraint is redundant given the existing primary key.",
                        )
                    )

            # 3. Check for pairwise duplicate unique constraints
            seen_pairs: set[tuple[str, str]] = set()
            for i, uq1 in enumerate(sorted_uqs):
                for j in range(i + 1, len(sorted_uqs)):
                    uq2 = sorted_uqs[j]
                    if are_unique_constraints_duplicate(uq1, uq2):
                        name1 = getattr(uq1, "name", f"uq_{i}")
                        name2 = getattr(uq2, "name", f"uq_{j}")
                        pair_key = tuple(sorted([name1, name2]))
                        if pair_key in seen_pairs:
                            continue
                        seen_pairs.add(pair_key)

                        cols = list(
                            getattr(uq1, "columns", None) or getattr(uq1, "column_names", ())
                        )
                        cols_str = ", ".join(cols)
                        id2 = str(getattr(uq2, "id", f"{table_id}.{name2}"))

                        evidence = (
                            DiagnosticEvidence(
                                object_id=id2,
                                field_name="duplicate_unique_constraint",
                                observed_value=f"Duplicates '{name1}' ({cols_str})",
                                expected_value="Unique column sets",
                                message=(
                                    f"Table '{table_name}' has duplicate unique constraints '{name1}' and "
                                    f"'{name2}' enforcing uniqueness on identical column set ({cols_str})."
                                ),
                                context_data={
                                    "table_name": table_name,
                                    "constraint_a": name1,
                                    "constraint_b": name2,
                                    "columns": cols,
                                },
                            ),
                        )
                        findings.append(
                            DiagnosticFinding(
                                rule_id=self.metadata.rule_id,
                                rule_version=self.metadata.version,
                                object_id=id2,
                                severity=self.metadata.default_severity,
                                title=f"Duplicate unique constraint definitions: {table_name}.{name2}",
                                description=(
                                    f"Unique constraints '{name1}' and '{name2}' on table '{table_name}' "
                                    f"enforce identical columns ({cols_str})."
                                ),
                                evidence=evidence,
                                severity_rationale="Duplicate unique constraints create redundant backing indexes and increase write overhead.",
                                recommendation="Review and remove duplicate unique constraint definition to save index maintenance overhead.",
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
                message=f"Detected {len(findings)} unique constraint findings.",
            )

        return RuleEvaluation(
            rule_id=self.metadata.rule_id,
            rule_version=self.metadata.version,
            status=EvaluationStatus.PASS,
            findings=(),
            execution_duration_ms=elapsed,
            message="All declared unique constraints have valid non-redundant definitions.",
        )
