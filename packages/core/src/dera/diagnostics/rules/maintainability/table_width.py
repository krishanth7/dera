"""DERA Diagnostics — Rule DERA-MNT-001: Excessive Table Width.

Detects wide relational tables with large column counts that exceed
configurable maintainability thresholds.
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


class TableWidthRule(DiagnosticRule):
    """Audits relational tables for excessive column counts."""

    DEFAULT_THRESHOLD = 30
    REVIEW_THRESHOLD = 50
    ELEVATED_THRESHOLD = 100

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-MNT-001",
            title="Excessive Table Width (Wide Table Pattern)",
            description=(
                "Detects relational tables containing a high number of columns that exceed "
                "configured maintainability thresholds. Wide tables increase row-size footprint, "
                "complicate query maintenance, and often indicate opportunities for vertical partitioning."
            ),
            version="1.0.0",
            category=RuleCategory.MAINTAINABILITY,
            default_severity=DiagnosticSeverity.INFORMATIONAL,
            supported_object_kinds=("table",),
            required_capabilities=("columns",),
            applicability_summary="Applies to all declared relational tables.",
            evidence_requirements="Requires table column definitions and column counts.",
            recommendation_template=(
                "Review table '{table_name}' with {column_count} columns. Consider vertical partitioning "
                "or segregating infrequently accessed attributes into secondary tables."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-MNT-001",
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

        threshold = int(
            context.config.rule_thresholds.get("max_table_width", self.DEFAULT_THRESHOLD)
        )
        review_threshold = int(
            context.config.rule_thresholds.get("review_table_width", self.REVIEW_THRESHOLD)
        )
        elevated_threshold = int(
            context.config.rule_thresholds.get("elevated_table_width", self.ELEVATED_THRESHOLD)
        )

        findings: list[DiagnosticFinding] = []

        for table in tables:
            metrics = compute_table_metrics(table)
            if metrics.column_count >= threshold:
                if metrics.column_count >= elevated_threshold:
                    sev = DiagnosticSeverity.MEDIUM
                    rationale = f"Table contains {metrics.column_count} columns, exceeding elevated threshold ({elevated_threshold})."
                elif metrics.column_count >= review_threshold:
                    sev = DiagnosticSeverity.LOW
                    rationale = f"Table contains {metrics.column_count} columns, exceeding review threshold ({review_threshold})."
                else:
                    sev = DiagnosticSeverity.INFORMATIONAL
                    rationale = f"Table contains {metrics.column_count} columns, reaching baseline threshold ({threshold})."

                full_name = f"{metrics.namespace}.{metrics.table_name}"
                ev = (
                    DiagnosticEvidence(
                        object_id=metrics.object_id,
                        field_name="column_count",
                        observed_value=metrics.column_count,
                        expected_value=f"< {threshold}",
                        message=f"Table '{full_name}' has {metrics.column_count} columns (threshold: {threshold}).",
                        context_data={
                            "table_id": metrics.object_id,
                            "table_name": metrics.table_name,
                            "namespace": metrics.namespace,
                            "column_count": metrics.column_count,
                            "threshold": threshold,
                            "nullable_column_count": metrics.nullable_column_count,
                        },
                    ),
                )

                findings.append(
                    DiagnosticFinding(
                        rule_id=self.metadata.rule_id,
                        rule_version=self.metadata.version,
                        object_id=metrics.object_id,
                        severity=sev,
                        title=f"Wide Table Pattern: {full_name} ({metrics.column_count} columns)",
                        description=(
                            f"Table '{full_name}' defines {metrics.column_count} columns, exceeding the "
                            f"configured maintainability threshold of {threshold} columns."
                        ),
                        evidence=ev,
                        severity_rationale=rationale,
                        recommendation=(
                            f"Review table '{full_name}'. Evaluate if this entity can be vertically partitioned "
                            "or if infrequently accessed fields should be moved to an extension table."
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
            message=f"Evaluated {len(tables)} table(s); found {len(findings)} wide table finding(s).",
        )
