"""DERA Diagnostics — Rule DERA-MNT-008: Excessive Text/Binary LOB Column Concentration.

Audits tables containing numerous large text (TEXT, CLOB) or binary (BLOB, BYTEA)
columns that contribute to off-page storage overhead and slow full-table scans.
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


class LobConcentrationRule(DiagnosticRule):
    """Audits tables for high concentrations of large object (LOB) columns."""

    DEFAULT_MAX_LOB_COLUMNS = 4
    ELEVATED_MAX_LOB_COLUMNS = 8

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-MNT-008",
            title="Excessive Text/Binary LOB Column Concentration",
            description=(
                "Detects relational tables containing multiple large text (TEXT, CLOB, VARCHAR(MAX)) "
                "or binary (BLOB, BYTEA, IMAGE) columns. Storing numerous unbounded LOB columns in a single "
                "table increases row-size fragmentation, causes frequent TOAST/overflow paging, and degrades scan throughput."
            ),
            version="1.0.0",
            category=RuleCategory.MAINTAINABILITY,
            default_severity=DiagnosticSeverity.INFORMATIONAL,
            supported_object_kinds=("table",),
            required_capabilities=("columns", "data_types"),
            applicability_summary="Applies to all declared relational tables.",
            evidence_requirements="Requires table column definitions and native data types.",
            recommendation_template=(
                "Table '{table_name}' defines {lob_count} LOB columns. Consider offloading binary assets "
                "or large document payloads to dedicated document stores or external object storage."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-MNT-008",
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
            context.config.rule_thresholds.get("max_lob_columns", self.DEFAULT_MAX_LOB_COLUMNS)
        )
        elevated_threshold = int(
            context.config.rule_thresholds.get(
                "elevated_lob_columns", self.ELEVATED_MAX_LOB_COLUMNS
            )
        )

        findings: list[DiagnosticFinding] = []

        for table in tables:
            metrics = compute_table_metrics(table)
            if metrics.lob_column_count >= threshold:
                sev = (
                    DiagnosticSeverity.LOW
                    if metrics.lob_column_count >= elevated_threshold
                    else DiagnosticSeverity.INFORMATIONAL
                )
                full_name = f"{metrics.namespace}.{metrics.table_name}"

                ev = (
                    DiagnosticEvidence(
                        object_id=metrics.object_id,
                        field_name="lob_column_count",
                        observed_value=metrics.lob_column_count,
                        expected_value=f"< {threshold}",
                        message=(
                            f"Table '{full_name}' defines {metrics.lob_column_count} large text/binary LOB columns "
                            f"(threshold: {threshold})."
                        ),
                        context_data={
                            "table_id": metrics.object_id,
                            "table_name": metrics.table_name,
                            "namespace": metrics.namespace,
                            "lob_column_count": metrics.lob_column_count,
                            "total_column_count": metrics.column_count,
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
                        title=f"High LOB Column Concentration: '{full_name}' ({metrics.lob_column_count} LOBs)",
                        description=(
                            f"Table '{full_name}' contains {metrics.lob_column_count} large text or binary columns, "
                            f"exceeding the maintainability threshold of {threshold}."
                        ),
                        evidence=ev,
                        severity_rationale=(
                            f"Table has {metrics.lob_column_count} LOB columns. Storing many large unbounded payloads "
                            "in the primary table increases off-page storage overhead and degrades cache efficiency."
                        ),
                        recommendation=(
                            f"Review storage design for '{full_name}'. Consider moving rarely queried large text/binary "
                            "columns to a separate detail table or cloud object store (e.g. S3, GCS) storing only URIs."
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
            message=f"Evaluated LOB concentration for {len(tables)} tables; found {len(findings)} finding(s).",
        )
