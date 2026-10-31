"""DERA Diagnostics — Rule DERA-MNT-004: Reserved Word Identifier Usage.

Audits table and column identifiers for collisions with engine-specific SQL
reserved keywords that mandate quoting and cause query parsing errors.
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
from dera.diagnostics.metrics.naming_metrics import is_reserved_word
from dera.diagnostics.models import DiagnosticFinding, RuleEvaluation, RuleMetadata
from dera.diagnostics.protocols import DiagnosticRule
from dera.diagnostics.rules.shared.graph_helpers import resolve_tables

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


class ReservedWordUsageRule(DiagnosticRule):
    """Audits database schema identifiers for SQL reserved word collisions."""

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-MNT-004",
            title="Reserved Word Identifier Usage",
            description=(
                "Detects table and column identifiers that match engine-specific SQL reserved keywords "
                "(such as 'user', 'order', 'group', 'table', 'where'). Unquoted usage in application "
                "queries causes syntax errors, requires constant delimiter escaping, and complicates ORM integration."
            ),
            version="1.0.0",
            category=RuleCategory.MAINTAINABILITY,
            default_severity=DiagnosticSeverity.LOW,
            supported_object_kinds=("table", "column"),
            required_capabilities=("columns",),
            applicability_summary="Applies to all table and column names across all relational engines.",
            evidence_requirements="Requires identifier strings and database engine identity.",
            recommendation_template=(
                "Avoid using SQL reserved keyword '{keyword}' as an identifier. Rename the object or "
                "ensure all queries and migrations enclose it in dialect quotes."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-MNT-004",
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        start_time = time.perf_counter()
        tables = resolve_tables(context)

        if not tables:
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.INSUFFICIENT_METADATA,
                findings=(),
                execution_duration_ms=(time.perf_counter() - start_time) * 1000,
                message="No tables available in diagnostic context.",
            )

        engine = context.source_engine
        findings: list[DiagnosticFinding] = []

        for table in tables:
            table_id = str(getattr(table, "id", getattr(table, "name", "<unnamed>")))
            table_name = str(getattr(table, "name", "<unnamed>"))
            namespace = str(getattr(table, "schema_name", getattr(table, "namespace", "public")))
            full_table_name = f"{namespace}.{table_name}"

            # 1. Check Table Name
            if is_reserved_word(table_name, engine):
                ev = (
                    DiagnosticEvidence(
                        object_id=table_id,
                        field_name="table_name",
                        observed_value=table_name,
                        expected_value="Non-reserved identifier",
                        message=(
                            f"Table '{full_table_name}' matches a reserved SQL keyword in {engine}."
                        ),
                        context_data={
                            "table_id": table_id,
                            "table_name": table_name,
                            "namespace": namespace,
                            "engine": engine,
                            "reserved_keyword": table_name.lower(),
                        },
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=table_id,
                        severity=DiagnosticSeverity.MEDIUM,
                        title=f"Reserved Word Table Name: '{table_name}' ({engine})",
                        description=(
                            f"Table '{full_table_name}' uses the reserved SQL keyword '{table_name.lower()}'. "
                            "Unquoted references in raw SQL or analytical queries will fail syntax validation."
                        ),
                        evidence=ev,
                        severity_rationale=f"Table identifier matches a core reserved keyword in {engine}.",
                        recommendation=(
                            f"Consider renaming table '{table_name}' to a domain-specific plural or composite identifier "
                            f"(e.g. '{table_name}_records' or 'app_{table_name}') to avoid mandatory quoting."
                        ),
                    )
                )

            # 2. Check Column Names
            columns = getattr(table, "columns", ())
            for col in columns:
                col_name = str(getattr(col, "name", ""))
                col_id = str(getattr(col, "id", f"{table_id}.{col_name}"))

                if is_reserved_word(col_name, engine):
                    ev = (
                        DiagnosticEvidence(
                            object_id=col_id,
                            field_name="column_name",
                            observed_value=col_name,
                            expected_value="Non-reserved identifier",
                            message=(
                                f"Column '{full_table_name}.{col_name}' matches a reserved SQL keyword in {engine}."
                            ),
                            context_data={
                                "column_id": col_id,
                                "column_name": col_name,
                                "table_name": table_name,
                                "namespace": namespace,
                                "engine": engine,
                                "reserved_keyword": col_name.lower(),
                            },
                        ),
                    )
                    findings.append(
                        DiagnosticFinding(
                            rule_id=self.metadata.rule_id,
                            rule_version=self.metadata.version,
                            object_id=col_id,
                            severity=DiagnosticSeverity.LOW,
                            title=f"Reserved Word Column Name: '{full_table_name}.{col_name}' ({engine})",
                            description=(
                                f"Column '{col_name}' on table '{full_table_name}' uses the reserved keyword "
                                f"'{col_name.lower()}'. Queries must enclose this column in quotes."
                            ),
                            evidence=ev,
                            severity_rationale=f"Column identifier matches a reserved keyword in {engine}.",
                            recommendation=(
                                f"Consider qualifying column '{col_name}' (e.g. '{col_name}_at', '{table_name}_{col_name}') "
                                "to avoid escaping and ORM projection conflicts."
                            ),
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
            message=f"Evaluated reserved word collisions for {engine}; found {len(findings)} finding(s).",
        )
