"""DERA Diagnostics — Rule DERA-MNT-003: Identifier Naming Convention Inconsistency.

Evaluates table and column identifiers against configured naming convention profiles
(snake_case, camelCase, PascalCase, kebab-case) to detect style deviations.
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
from dera.diagnostics.metrics.naming_metrics import NamingProfile, matches_naming_profile
from dera.diagnostics.models import DiagnosticFinding, RuleEvaluation, RuleMetadata
from dera.diagnostics.protocols import DiagnosticRule
from dera.diagnostics.rules.shared.graph_helpers import resolve_tables

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


class NamingConsistencyRule(DiagnosticRule):
    """Audits database identifiers for deviations from a configured naming profile."""

    DEFAULT_PROFILE = NamingProfile.SNAKE_CASE

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-MNT-003",
            title="Identifier Naming Convention Inconsistency",
            description=(
                "Detects table and column identifiers that deviate from the configured schema "
                "naming profile (default: snake_case). Inconsistent casing and naming styles "
                "increase engineering friction, lead to ORM mapping issues, and complicate schema maintenance."
            ),
            version="1.0.0",
            category=RuleCategory.MAINTAINABILITY,
            default_severity=DiagnosticSeverity.INFORMATIONAL,
            supported_object_kinds=("table", "column"),
            required_capabilities=("columns",),
            applicability_summary="Applies to all declared table and column names.",
            evidence_requirements="Requires identifier strings for tables and columns.",
            recommendation_template=(
                "Rename identifier '{identifier_name}' to adhere to the '{naming_profile}' convention."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-MNT-003",
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

        profile = str(context.config.rule_thresholds.get("naming_profile", self.DEFAULT_PROFILE))

        findings: list[DiagnosticFinding] = []

        for table in tables:
            table_id = str(getattr(table, "id", getattr(table, "name", "<unnamed>")))
            table_name = str(getattr(table, "name", "<unnamed>"))
            namespace = str(getattr(table, "schema_name", getattr(table, "namespace", "public")))
            full_table_name = f"{namespace}.{table_name}"

            # 1. Audit Table Name
            if not matches_naming_profile(table_name, profile):
                ev = (
                    DiagnosticEvidence(
                        object_id=table_id,
                        field_name="table_name",
                        observed_value=table_name,
                        expected_value=f"Matches profile '{profile}'",
                        message=(
                            f"Table '{full_table_name}' does not follow the configured "
                            f"'{profile}' naming convention."
                        ),
                        context_data={
                            "table_id": table_id,
                            "table_name": table_name,
                            "namespace": namespace,
                            "configured_profile": profile,
                        },
                    ),
                )
                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=table_id,
                        severity=DiagnosticSeverity.INFORMATIONAL,
                        title=f"Naming Inconsistency: Table '{full_table_name}'",
                        description=(
                            f"Table name '{table_name}' in namespace '{namespace}' deviates from "
                            f"the configured '{profile}' naming convention."
                        ),
                        evidence=ev,
                        severity_rationale=f"Identifier deviates from the established {profile} convention.",
                        recommendation=(
                            f"Consider renaming table '{table_name}' to follow the '{profile}' "
                            "convention to ensure consistency across the database schema."
                        ),
                    )
                )

            # 2. Audit Column Names
            columns = getattr(table, "columns", ())
            for col in columns:
                col_name = str(getattr(col, "name", ""))
                col_id = str(getattr(col, "id", f"{table_id}.{col_name}"))

                if not matches_naming_profile(col_name, profile):
                    ev = (
                        DiagnosticEvidence(
                            object_id=col_id,
                            field_name="column_name",
                            observed_value=col_name,
                            expected_value=f"Matches profile '{profile}'",
                            message=(
                                f"Column '{full_table_name}.{col_name}' does not follow the configured "
                                f"'{profile}' naming convention."
                            ),
                            context_data={
                                "column_id": col_id,
                                "column_name": col_name,
                                "table_name": table_name,
                                "namespace": namespace,
                                "configured_profile": profile,
                            },
                        ),
                    )
                    findings.append(
                        DiagnosticFinding(
                            rule_id=self.metadata.rule_id,
                            rule_version=self.metadata.version,
                            object_id=col_id,
                            severity=DiagnosticSeverity.INFORMATIONAL,
                            title=f"Naming Inconsistency: Column '{full_table_name}.{col_name}'",
                            description=(
                                f"Column '{col_name}' on table '{full_table_name}' deviates from "
                                f"the configured '{profile}' naming convention."
                            ),
                            evidence=ev,
                            severity_rationale=f"Column identifier '{col_name}' deviates from the {profile} convention.",
                            recommendation=(
                                f"Consider adopting '{profile}' naming for column '{col_name}' on table '{table_name}'."
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
            message=f"Evaluated naming compliance against '{profile}'; found {len(findings)} deviation(s).",
        )
