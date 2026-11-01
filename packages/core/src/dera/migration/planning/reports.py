"""Migration Plan Report and Summary Models.

Represents the top-level structured, reviewable contract for Phase 9.3.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from dera.migration.planning.enums import PlanStatus
from dera.migration.planning.models import (
    AbstractMigrationOperation,
    ManualDecisionGate,
    PlanningStage,
    RollbackConsideration,
    ValidationRequirement,
)


class MigrationPlanSummary(BaseModel):
    """High-level metrics summarizing the migration plan."""
    total_operations: int
    supported_operations: int
    conditional_operations: int
    blocked_operations: int
    unsupported_operations: int
    manual_decision_gates_count: int
    dependency_edges_count: int
    stages_count: int
    destructive_operations_count: int
    validation_requirements_count: int
    detected_cycles_count: int


class MigrationPlanReport(BaseModel):
    """Deterministic, structured migration plan report."""
    plan_id: str
    plan_status: PlanStatus
    target_engine: str
    baseline_snapshot_id: str
    target_snapshot_id: str
    comparison_fingerprint: str
    risk_report_fingerprint: str
    policy_version: str = "1.0.0"
    catalog_version: str = "1.0.0"
    plan_fingerprint: str

    summary: MigrationPlanSummary
    operations: List[AbstractMigrationOperation] = Field(default_factory=list)
    stages: List[PlanningStage] = Field(default_factory=list)
    manual_decision_gates: List[ManualDecisionGate] = Field(default_factory=list)
    validation_requirements: List[ValidationRequirement] = Field(default_factory=list)
    rollback_considerations: List[RollbackConsideration] = Field(default_factory=list)
    detected_cycles: List[List[str]] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
