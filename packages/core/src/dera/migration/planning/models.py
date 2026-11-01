"""Domain models for Phase 9.3 Migration Planning.

Defines abstract migration operations, preconditions, postconditions,
manual decision gates, rollback considerations, stages, and validation requirements.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from dera.migration.enums import ReversibilityClassification, ReviewPriority
from dera.migration.planning.enums import (
    EngineCapabilityState,
    ManualGateStatus,
    MigrationOperationType,
    PlanningStageType,
    PreconditionType,
)


class OperationPrecondition(BaseModel):
    """Prerequisite condition required before an operation can proceed."""
    condition_id: str
    precondition_type: PreconditionType
    description: str
    target_object_id: str
    required_evidence: str
    verification_method: str
    is_satisfied: bool = False
    limitations: List[str] = Field(default_factory=list)


class OperationPostcondition(BaseModel):
    """Expected structural state following successful operation execution."""
    postcondition_id: str
    description: str
    target_object_id: str
    expected_state: Dict[str, Any]
    verification_method: str


class ValidationRequirement(BaseModel):
    """Post-migration or pre-flight structural verification requirement."""
    requirement_id: str
    operation_id: str
    description: str
    target_object_id: str
    check_type: str  # e.g., OBJECT_EXISTS, COLUMN_TYPE_MATCH, CONSTRAINT_PRESENT
    expected_metadata: Dict[str, Any] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)


class ManualDecisionGate(BaseModel):
    """Explicit engineering decision required before execution."""
    gate_id: str
    operation_id: str
    title: str
    description: str
    gate_status: ManualGateStatus = ManualGateStatus.REQUIRED
    decision_category: str  # DATA_PRESERVATION, BACKFILL_STRATEGY, COLUMN_CONVERSION, APP_COORDINATION
    required_action: str
    resolution_evidence: Optional[str] = None


class RollbackConsideration(BaseModel):
    """Advisory rollback assessment based on verified reversibility."""
    operation_id: str
    reversibility: ReversibilityClassification
    is_destructive: bool
    requires_data_preservation: bool
    rollback_strategy: str
    advisory_notes: List[str] = Field(default_factory=list)


class AbstractMigrationOperation(BaseModel):
    """Abstract, database-agnostic migration operation."""
    operation_id: str
    operation_type: MigrationOperationType
    target_object_id: str
    target_object_type: str
    target_object_name: str
    namespace: Optional[str] = None
    table_name: Optional[str] = None
    source_change_fingerprint: str
    catalog_version: str = "1.0.0"
    operation_properties: Dict[str, Any] = Field(default_factory=dict)

    # Dependency tracking
    prerequisite_operation_ids: List[str] = Field(default_factory=list)
    dependent_operation_ids: List[str] = Field(default_factory=list)

    # Engine compatibility
    engine_capability: EngineCapabilityState = EngineCapabilityState.SUPPORTED
    engine_limitations: List[str] = Field(default_factory=list)

    # Gates and verifications
    preconditions: List[OperationPrecondition] = Field(default_factory=list)
    postconditions: List[OperationPostcondition] = Field(default_factory=list)
    validation_requirements: List[ValidationRequirement] = Field(default_factory=list)
    manual_decision_gates: List[ManualDecisionGate] = Field(default_factory=list)
    rollback_consideration: Optional[RollbackConsideration] = None

    # Risk references
    source_risk_fingerprint: Optional[str] = None
    review_priority: ReviewPriority = ReviewPriority.P4_LOW
    is_destructive: bool = False
    is_blocked: bool = False
    blocking_reasons: List[str] = Field(default_factory=list)


class PlanningStage(BaseModel):
    """Ordered stage containing independent or internally ordered operations."""
    stage_id: str
    stage_type: PlanningStageType
    stage_order: int
    operation_ids: List[str] = Field(default_factory=list)
    description: str
