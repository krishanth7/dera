"""DERA Diagnostics — Rule DERA-MNT-002: High Column Nullability Ratio.

Identifies tables where a large majority of declared columns permit NULL,
indicating sparse schemas, unnormalized subtyping, or missing NOT NULL constraints.
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
from dera.diagnostics.metrics.table_metrics import compute_table_metrics
from dera.diagnostics.models import DiagnosticFinding, RuleEvaluation, RuleMetadata
from dera.diagnostics.protocols import DiagnosticRule
from dera.diagnostics.rules.shared.graph_helpers import resolve_tables

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


class ColumnNullabilityRule(DiagnosticRule):
    """Audits tables for disproportionately high column nullability ratios."""

    DEFAULT_MAX_RATIO = 0.50
    ELEVATED_MAX_RATIO = 0.75
    MIN_COLUMNS = 5

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-MNT-002",
            title="High Column Nullability Ratio",
            description=(
                "Detects relational tables where the proportion of nullable columns exceeds "
                "configured thresholds. High nullability often indicates sparse multi-purpose tables, "
                "polymorphic subtype modeling, or omission of required domain constraints."
            ),
            version="1.0.0",
            category=RuleCategory.MAINTAINABILITY,
            default_severity=DiagnosticSeverity.INFORMATIONAL,
            supported_object_kinds=("table",),
            required_capabilities=("columns", "nullability"),
            applicability_summary="Applies to tables with at least 5 columns.",
            evidence_requirements="Requires table column count and is_nullable attributes.",
            recommendation_template=(
                "Review table '{table_name}' ({nullability_percentage}% nullable). Evaluate whether "
                "unnormalized sparse attributes should be normalized into subtype or extension tables."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-MNT-002",
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

        threshold = float(
            context.config.rule_thresholds.get("max_nullability_ratio", self.DEFAULT_MAX_RATIO)
        )
        elevated_threshold = float(
            context.config.rule_thresholds.get(
                "elevated_nullability_ratio", self.ELEVATED_MAX_RATIO
            )
        )
        min_cols = int(
            context.config.rule_thresholds.get(
                "min_table_columns_for_nullability", self.MIN_COLUMNS
            )
        )

        findings: list[DiagnosticFinding] = []

        for table in tables:
            metrics = compute_table_metrics(table)
            if metrics.column_count < min_cols:
                continue

            if metrics.nullability_ratio >= threshold:
                sev = (
                    DiagnosticSeverity.LOW
                    if metrics.nullability_ratio >= elevated_threshold
                    else DiagnosticSeverity.INFORMATIONAL
                )
                pct = round(metrics.nullability_ratio * 100, 1)
                full_name = f"{metrics.namespace}.{metrics.table_name}"

                ev = (
                    DiagnosticEvidence(
                        object_id=metrics.object_id,
                        field_name="nullability_ratio",
                        observed_value=metrics.nullability_ratio,
                        expected_value=f"< {threshold}",
                        message=(
                            f"Table '{full_name}' has {metrics.nullable_column_count} of {metrics.column_count} "
                            f"columns marked nullable ({pct}%, threshold: {int(threshold * 100)}%)."
                        ),
                        context_data={
                            "table_id": metrics.object_id,
                            "table_name": metrics.table_name,
                            "namespace": metrics.namespace,
                            "column_count": metrics.column_count,
                            "nullable_column_count": metrics.nullable_column_count,
                            "nullability_ratio": metrics.nullability_ratio,
                            "threshold": threshold,
                        },
                    ),
                )

                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=metrics.object_id,
                        severity=sev,
                        title=f"High Column Nullability: {full_name} ({pct}% nullable)",
                        description=(
                            f"Table '{full_name}' has a nullability ratio of {pct}% "
                            f"({metrics.nullable_column_count}/{metrics.column_count} columns), "
                            f"exceeding the configured threshold of {int(threshold * 100)}%."
                        ),
                        evidence=ev,
                        severity_rationale=(
                            f"{pct}% of columns are nullable. Tables with extreme nullability often represent "
                            "sparse multi-entity schemas or missing NOT NULL domain requirements."
                        ),
                        recommendation=(
                            f"Review column requirements on '{full_name}'. Enforce NOT NULL constraints where "
                            "business rules require values, or partition sparse columns into dedicated extension tables."
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
            message=f"Evaluated {len(tables)} table(s); found {len(findings)} high nullability finding(s).",
        )
