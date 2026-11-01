"""Phase 9.3 Deterministic Migration Planning & Dependency Ordering Package.

Provides abstract migration operation modeling, operation catalog rules,
change-to-operation mapping, dependency DAG construction, cycle detection (Tarjan SCC),
topological ordering, stage grouping, manual decision gates, and plan reporting.
"""

from dera.migration.planning.change_mapper import ChangeToOperationMapper
from dera.migration.planning.cycles import CycleDetector
from dera.migration.planning.engine import MigrationPlanningEngine
from dera.migration.planning.enums import (
    EngineCapabilityState,
    ManualGateStatus,
    MigrationOperationType,
    PlanningStageType,
    PlanStatus,
    PreconditionType,
)
from dera.migration.planning.fingerprint import PlanFingerprintCalculator
from dera.migration.planning.graph import OperationDependencyGraph
from dera.migration.planning.models import (
    AbstractMigrationOperation,
    ManualDecisionGate,
    OperationPostcondition,
    OperationPrecondition,
    PlanningStage,
    RollbackConsideration,
    ValidationRequirement,
)
from dera.migration.planning.operation_catalog import OperationCatalog
from dera.migration.planning.ordering import DeterministicOrderingEngine
from dera.migration.planning.reports import MigrationPlanReport, MigrationPlanSummary

__all__ = [
    "AbstractMigrationOperation",
    "ChangeToOperationMapper",
    "CycleDetector",
    "DeterministicOrderingEngine",
    "EngineCapabilityState",
    "ManualDecisionGate",
    "ManualGateStatus",
    "MigrationOperationType",
    "MigrationPlanReport",
    "MigrationPlanSummary",
    "MigrationPlanningEngine",
    "OperationCatalog",
    "OperationDependencyGraph",
    "OperationPostcondition",
    "OperationPrecondition",
    "PlanFingerprintCalculator",
    "PlanStatus",
    "PlanningStage",
    "PlanningStageType",
    "PreconditionType",
    "RollbackConsideration",
    "ValidationRequirement",
]
