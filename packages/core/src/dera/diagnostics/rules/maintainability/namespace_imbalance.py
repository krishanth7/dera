"""DERA Diagnostics — Rule DERA-MNT-005: Namespace Object Imbalance & Monolith.

Detects disproportionate object concentration within a single database namespace
alongside underutilized or empty schemas in multi-namespace databases.
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
from dera.diagnostics.metrics.namespace_metrics import (
    compute_namespace_imbalance_ratio,
    compute_namespace_metrics,
)
from dera.diagnostics.models import DiagnosticFinding, RuleEvaluation, RuleMetadata
from dera.diagnostics.protocols import DiagnosticRule
from dera.diagnostics.rules.shared.graph_helpers import resolve_namespaces, resolve_tables

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


class NamespaceImbalanceRule(DiagnosticRule):
    """Audits multi-namespace databases for severe object distribution imbalance."""

    DEFAULT_MAX_IMBALANCE = 0.90
    MIN_TABLES_REQUIRED = 10

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-MNT-005",
            title="Namespace Object Imbalance & Monolithic Schema",
            description=(
                "Detects multi-namespace databases where almost all tables are concentrated in a single "
                "monolithic schema (e.g. 'public') while other declared schemas remain empty or underutilized. "
                "Proper schema modularization clarifies bounded contexts and simplifies privilege governance."
            ),
            version="1.0.0",
            category=RuleCategory.MAINTAINABILITY,
            default_severity=DiagnosticSeverity.INFORMATIONAL,
            supported_object_kinds=("namespace", "schema"),
            required_capabilities=("namespaces",),
            applicability_summary="Applies to multi-namespace databases with at least 10 tables.",
            evidence_requirements="Requires namespace list and table object counts.",
            recommendation_template=(
                "Namespace '{namespace_name}' contains {share_pct}% of all tables in the database. "
                "Consider modularizing domain tables into dedicated namespaces."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-MNT-005",
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        start_time = time.perf_counter()
        namespaces = resolve_namespaces(context)
        tables = resolve_tables(context)

        # Single-namespace databases or small schemas are not evaluated
        if len(namespaces) <= 1:
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.NOT_APPLICABLE,
                findings=(),
                execution_duration_ms=(time.perf_counter() - start_time) * 1000,
                message="Rule is not applicable to single-namespace databases.",
            )

        total_tables = len(tables)
        min_tables = int(
            context.config.rule_thresholds.get(
                "min_tables_for_namespace_imbalance", self.MIN_TABLES_REQUIRED
            )
        )
        if total_tables < min_tables:
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.PASS,
                findings=(),
                execution_duration_ms=(time.perf_counter() - start_time) * 1000,
                message=f"Schema contains {total_tables} tables (below threshold of {min_tables}).",
            )

        threshold = float(
            context.config.rule_thresholds.get(
                "max_namespace_imbalance_ratio", self.DEFAULT_MAX_IMBALANCE
            )
        )

        ns_metrics = compute_namespace_metrics(namespaces, total_database_tables=total_tables)
        imbalance_ratio = compute_namespace_imbalance_ratio(ns_metrics)

        findings: list[DiagnosticFinding] = []

        if imbalance_ratio >= threshold:
            dominant = max(ns_metrics, key=lambda m: m.table_count)
            empty_namespaces = [m.namespace_name for m in ns_metrics if m.total_objects == 0]
            pct = round(dominant.object_share_ratio * 100, 1)

            ev = (
                DiagnosticEvidence(
                    object_id=dominant.namespace_name,
                    field_name="object_share_ratio",
                    observed_value=dominant.object_share_ratio,
                    expected_value=f"< {threshold}",
                    message=(
                        f"Namespace '{dominant.namespace_name}' contains {dominant.table_count} of "
                        f"{total_tables} tables ({pct}%), exceeding concentration threshold of {int(threshold * 100)}%."
                    ),
                    context_data={
                        "dominant_namespace": dominant.namespace_name,
                        "dominant_table_count": dominant.table_count,
                        "total_database_tables": total_tables,
                        "share_ratio": dominant.object_share_ratio,
                        "total_namespaces": len(namespaces),
                        "empty_namespaces": empty_namespaces,
                        "threshold": threshold,
                    },
                ),
            )

            findings.append(
                DiagnosticFinding(
                    rule_id=self.metadata.rule_id,
                    rule_version=self.metadata.version,
                    object_id=dominant.namespace_name,
                    severity=DiagnosticSeverity.INFORMATIONAL,
                    title=f"Monolithic Namespace Concentration: '{dominant.namespace_name}' ({pct}%)",
                    description=(
                        f"Namespace '{dominant.namespace_name}' hosts {pct}% of all tables ({dominant.table_count}/{total_tables}) "
                        f"across {len(namespaces)} declared namespaces."
                    ),
                    evidence=ev,
                    severity_rationale=(
                        f"High concentration ({pct}%) in one schema while {len(empty_namespaces)} namespace(s) "
                        "remain empty or underutilized suggests incomplete or unmaintained schema partitioning."
                    ),
                    recommendation=(
                        f"Evaluate schema modularity. Consider migrating bounded domain entities from '{dominant.namespace_name}' "
                        "into dedicated namespaces, or pruning unused empty schemas."
                    ),
                )
            )

        status = EvaluationStatus.FINDINGS_DETECTED if findings else EvaluationStatus.PASS
        return RuleEvaluation(
            rule_id=self.metadata.rule_id,
            rule_version=self.metadata.version,
            status=status,
            findings=tuple(findings),
            execution_duration_ms=(time.perf_counter() - start_time) * 1000,
            message=f"Evaluated {len(namespaces)} namespaces; imbalance ratio: {imbalance_ratio}.",
        )
