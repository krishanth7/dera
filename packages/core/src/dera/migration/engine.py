"""DERA Migration — Phase 9.2 Migration Risk Analysis Engine.

Primary orchestrator accepting a Phase 9.1 ComparisonReport (and optional
dependency graph), classifying changes, assessing risks, computing blast radius,
and generating deterministic, evidence-backed MigrationRiskReports.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dera.comparison.enums import ComparisonObjectType
from dera.comparison.models import ComparisonReport
from dera.migration.classification.classifier import ChangeClassifier
from dera.migration.classification.models import ClassifiedChange
from dera.migration.errors import InvalidComparisonReportError
from dera.migration.impact.blast_radius import (
    BlastRadiusMetrics,
    DependencyImpactAnalyzer,
)
from dera.migration.limits import MigrationRiskLimits
from dera.migration.recommendations.models import EngineeringRecommendation
from dera.migration.reports.models import MigrationRiskReport
from dera.migration.risk.evaluator import RiskEvaluator
from dera.migration.risk.models import MigrationRiskAssessment

if TYPE_CHECKING:
    from dera.reverse_engineering.dependencies.models import DependencyAnalysisResult
    from dera.reverse_engineering.graph.models import ForeignKeyGraph


class MigrationRiskAnalysisEngine:
    """Evaluates migration risks and backward compatibility from ComparisonReports."""

    def __init__(self, limits: MigrationRiskLimits | None = None) -> None:
        self.limits = limits or MigrationRiskLimits()
        self.impact_analyzer = DependencyImpactAnalyzer(limits=self.limits)

    def analyze(
        self,
        comparison_report: ComparisonReport,
        dependency_graph: ForeignKeyGraph | None = None,
        dependencies: DependencyAnalysisResult | None = None,
    ) -> MigrationRiskReport:
        """Execute deterministic migration risk analysis.

        Args:
            comparison_report: Verified Phase 9.1 ComparisonReport.
            dependency_graph: Optional Phase 6.3 foreign key graph for blast radius analysis.
            dependencies: Optional Phase 6.4 dependency analysis result for cycle detection.

        Returns:
            Immutable MigrationRiskReport.
        """
        if not isinstance(comparison_report, ComparisonReport):
            raise InvalidComparisonReportError("Input must be a valid ComparisonReport instance.")

        changes = comparison_report.changes
        self.limits.check_change_count(len(changes))

        # 1. Classify all changes
        classified_changes: list[ClassifiedChange] = []
        for raw_change in changes:
            classified = ChangeClassifier.classify(
                change=raw_change,
                engine=comparison_report.engine,
            )
            classified_changes.append(classified)

        # 2. Evaluate Blast Radius for affected tables
        blast_map: dict[str, BlastRadiusMetrics] = {}
        for raw_change in changes:
            if raw_change.object_type == ComparisonObjectType.TABLE:
                t_id = raw_change.canonical_id
                if t_id not in blast_map:
                    metrics = self.impact_analyzer.analyze_table_impact(
                        table_id=t_id,
                        graph=dependency_graph,
                        dependencies=dependencies,
                    )
                    blast_map[t_id] = metrics

        # 3. Evaluate Risks and Recommendations
        risk_assessments: list[MigrationRiskAssessment] = []
        recommendations: list[EngineeringRecommendation] = []

        for classified, raw_change in zip(classified_changes, changes, strict=True):
            t_id = (
                raw_change.canonical_id
                if raw_change.object_type == ComparisonObjectType.TABLE
                else raw_change.parent_canonical_id
            )
            tbl_blast = blast_map.get(t_id) if t_id else None

            chg_risks = RiskEvaluator.evaluate_change_risks(
                classified=classified,
                raw_change=raw_change,
                blast_radius=tbl_blast,
                engine=comparison_report.engine,
            )

            for r in chg_risks:
                risk_assessments.append(r)
                recommendations.extend(r.recommendations)

        self.limits.check_risk_assessments_count(len(risk_assessments))

        # 4. Deterministic Ordering of Risks
        # Ordered by: Priority rank (P1 -> P5) -> Severity rank (Critical -> Info) -> Rule ID -> Fingerprint
        sorted_risks = tuple(
            sorted(
                risk_assessments,
                key=lambda r: (
                    r.priority.rank,
                    -r.severity.rank,
                    r.dimension.value,
                    r.rule_id,
                    r.fingerprint,
                ),
            )
        )

        # Sort recommendations by recommendation_id
        sorted_recs = tuple(sorted(recommendations, key=lambda rec: rec.recommendation_id))

        # Sort blast radius reports by target_table_id
        sorted_blast = tuple(sorted(blast_map.values(), key=lambda b: b.target_table_id))

        return MigrationRiskReport.create(
            baseline_snapshot_id=comparison_report.baseline_snapshot_id,
            baseline_fingerprint=comparison_report.baseline_fingerprint,
            target_snapshot_id=comparison_report.target_snapshot_id,
            target_fingerprint=comparison_report.target_fingerprint,
            comparison_report_id=comparison_report.report_id,
            comparison_fingerprint=comparison_report.report_fingerprint,
            engine=comparison_report.engine,
            classified_changes=tuple(classified_changes),
            risk_assessments=sorted_risks,
            blast_radius_reports=sorted_blast,
            recommendations=sorted_recs,
            limitations=comparison_report.metadata_limitations,
        )
