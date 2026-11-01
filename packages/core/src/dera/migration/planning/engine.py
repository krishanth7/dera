"""Migration Planning Engine.

Orchestrates Phase 9.3 deterministic migration planning and dependency ordering:
1. Validates consistency between Phase 9.1 ComparisonReport and Phase 9.2 MigrationRiskReport.
2. Maps schema changes to abstract migration operations with catalog rules.
3. Constructs the operation dependency DAG (Prerequisite -> Dependent).
4. Runs Tarjan SCC cycle detection and marks cycle operations as BLOCKED.
5. Performs deterministic topological ordering with stable tie-breaking.
6. Groups operations into sequential planning stages.
7. Aggregates manual decision gates, validation requirements, and rollback considerations.
8. Computes the canonical SHA-256 plan fingerprint.
9. Emits the verified MigrationPlanReport.
"""

from dera.comparison.models import ComparisonReport
from dera.migration.planning.change_mapper import ChangeToOperationMapper
from dera.migration.planning.cycles import CycleDetector
from dera.migration.planning.enums import EngineCapabilityState, PlanStatus
from dera.migration.planning.fingerprint import PlanFingerprintCalculator
from dera.migration.planning.graph import OperationDependencyGraph
from dera.migration.planning.models import (
    ManualDecisionGate,
    RollbackConsideration,
    ValidationRequirement,
)
from dera.migration.planning.operation_catalog import OperationCatalog
from dera.migration.planning.ordering import DeterministicOrderingEngine
from dera.migration.planning.reports import MigrationPlanReport, MigrationPlanSummary
from dera.migration.reports.models import MigrationRiskReport


class MigrationPlanningEngine:
    """Deterministic migration planner."""

    POLICY_VERSION = "1.0.0"

    def __init__(self, target_engine: str | None = None):
        self.target_engine = target_engine

    def plan_migration(
        self,
        comparison_report: ComparisonReport,
        risk_report: MigrationRiskReport,
        override_engine: str | None = None,
    ) -> MigrationPlanReport:
        """Generate a deterministic migration plan from comparison and risk inputs."""
        # 1. Input consistency verification
        if comparison_report.baseline_snapshot_id != risk_report.baseline_snapshot_id:
            raise ValueError(
                f"Mismatched baseline snapshots: comparison has '{comparison_report.baseline_snapshot_id}', risk has '{risk_report.baseline_snapshot_id}'."
            )
        if comparison_report.target_snapshot_id != risk_report.target_snapshot_id:
            raise ValueError(
                f"Mismatched target snapshots: comparison has '{comparison_report.target_snapshot_id}', risk has '{risk_report.target_snapshot_id}'."
            )

        engine = (
            override_engine or self.target_engine or comparison_report.target_engine or "postgresql"
        ).lower()

        # 2. Map changes to abstract operations
        mapper = ChangeToOperationMapper(target_engine=engine)
        operations = mapper.map_changes(
            schema_changes=comparison_report.changes,
            classified_changes=risk_report.classified_changes,
            risk_assessments=risk_report.risk_assessments,
        )

        # 3. Build operation dependency DAG
        graph = OperationDependencyGraph(operations=operations)

        # 4. Cycle detection
        cycle_detector = CycleDetector(graph=graph)
        detected_cycles = cycle_detector.annotate_blocked_operations()

        # 5. Deterministic topological ordering & stage grouping
        ordering_engine = DeterministicOrderingEngine(graph=graph)
        ordered_ops, stages = ordering_engine.compute_ordering()

        # 6. Aggregate gates, validations, and rollback considerations
        manual_gates: list[ManualDecisionGate] = []
        validation_reqs: list[ValidationRequirement] = []
        rollback_considerations: list[RollbackConsideration] = []

        for op in ordered_ops:
            manual_gates.extend(op.manual_decision_gates)
            validation_reqs.extend(op.validation_requirements)
            if op.rollback_consideration:
                rollback_considerations.append(op.rollback_consideration)

        # 7. Summary metrics
        total_ops = len(ordered_ops)
        supported_ops = sum(
            1 for op in ordered_ops if op.engine_capability == EngineCapabilityState.SUPPORTED
        )
        conditional_ops = sum(
            1 for op in ordered_ops if op.engine_capability == EngineCapabilityState.CONDITIONAL
        )
        unsupported_ops = sum(
            1 for op in ordered_ops if op.engine_capability == EngineCapabilityState.UNSUPPORTED
        )
        blocked_ops = sum(1 for op in ordered_ops if op.is_blocked)
        destructive_ops = sum(1 for op in ordered_ops if op.is_destructive)

        summary = MigrationPlanSummary(
            total_operations=total_ops,
            supported_operations=supported_ops,
            conditional_operations=conditional_ops,
            blocked_operations=blocked_ops,
            unsupported_operations=unsupported_ops,
            manual_decision_gates_count=len(manual_gates),
            dependency_edges_count=graph.edge_count,
            stages_count=len(stages),
            destructive_operations_count=destructive_ops,
            validation_requirements_count=len(validation_reqs),
            detected_cycles_count=len(detected_cycles),
        )

        # 8. Plan status derivation
        plan_status = self._derive_plan_status(
            unsupported_count=unsupported_ops,
            blocked_count=blocked_ops,
            manual_gates_count=len(manual_gates),
            detected_cycles_count=len(detected_cycles),
        )

        # 9. Deterministic plan fingerprint
        fingerprint = PlanFingerprintCalculator.compute_fingerprint(
            comparison_fingerprint=comparison_report.report_fingerprint,
            risk_report_fingerprint=risk_report.report_fingerprint,
            engine=engine,
            policy_version=self.POLICY_VERSION,
            catalog_version=OperationCatalog.CATALOG_VERSION,
            operations=ordered_ops,
            stages=stages,
        )

        plan_id = f"plan_{fingerprint[:16]}"

        return MigrationPlanReport(
            plan_id=plan_id,
            plan_status=plan_status,
            target_engine=engine,
            baseline_snapshot_id=comparison_report.baseline_snapshot_id,
            target_snapshot_id=comparison_report.target_snapshot_id,
            comparison_fingerprint=comparison_report.report_fingerprint,
            risk_report_fingerprint=risk_report.report_fingerprint,
            policy_version=self.POLICY_VERSION,
            catalog_version=OperationCatalog.CATALOG_VERSION,
            plan_fingerprint=fingerprint,
            summary=summary,
            operations=ordered_ops,
            stages=stages,
            manual_decision_gates=manual_gates,
            validation_requirements=validation_reqs,
            rollback_considerations=rollback_considerations,
            detected_cycles=detected_cycles,
            limitations=[
                "Execution of migration plans is strictly out of scope for Phase 9.3.",
                "Plans are reviewable advisory specifications and require engineer approval.",
            ],
        )

    def _derive_plan_status(
        self,
        unsupported_count: int,
        blocked_count: int,
        manual_gates_count: int,
        detected_cycles_count: int,
    ) -> PlanStatus:
        if unsupported_count > 0:
            return PlanStatus.UNSUPPORTED
        if blocked_count > 0 or detected_cycles_count > 0:
            return PlanStatus.BLOCKED
        if manual_gates_count > 0:
            return PlanStatus.REQUIRES_MANUAL_DECISION
        return PlanStatus.READY_FOR_REVIEW
