/**
 * Phase 9 TypeScript Domain Contracts for Migration Engineering Workspace.
 *
 * Models comparison reports, risk assessments, abstract migration plans,
 * SQL artifacts, and governance review requests.
 */

export type ComparisonChangeType = 'ADDED' | 'REMOVED' | 'MODIFIED' | 'UNCHANGED' | 'UNSUPPORTED';
export type ComparisonObjectType = 'NAMESPACE' | 'TABLE' | 'COLUMN' | 'PRIMARY_KEY' | 'FOREIGN_KEY' | 'UNIQUE_CONSTRAINT' | 'CHECK_CONSTRAINT' | 'INDEX' | 'VIEW';

export interface PropertyDifference {
  property?: string;
  property_name?: string;
  baseline_value?: any;
  target_value?: any;
  before_value?: any;
  after_value?: any;
}

export interface SchemaChangeDto {
  change_id: string;
  change_type: ComparisonChangeType | string;
  object_type: ComparisonObjectType | string;
  canonical_id: string;
  namespace: string;
  name: string;
  object_name?: string;
  object_id?: string;
  parent_name?: string | null;
  fingerprint: string;
  property_differences?: PropertyDifference[];
  property_diffs?: PropertyDifference[];
}

export interface ComparisonSummaryDto {
  total_changes: number;
  total_added: number;
  total_removed: number;
  total_modified: number;
  added_count?: number;
  removed_count?: number;
  modified_count?: number;
}

export interface ComparisonReportDto {
  report_id: string;
  baseline_snapshot_id: string;
  source_snapshot_id?: string;
  target_snapshot_id: string;
  engine: string;
  target_engine: string;
  status: string;
  summary: ComparisonSummaryDto;
  changes: SchemaChangeDto[];
  differences?: SchemaChangeDto[];
  report_fingerprint: string;
  fingerprint?: string;
}

export type ComparisonDiffItem = SchemaChangeDto;

export enum ReviewPriority {
  P1_CRITICAL = 'P1_CRITICAL',
  P2_HIGH = 'P2_HIGH',
  P3_MEDIUM = 'P3_MEDIUM',
  P4_LOW = 'P4_LOW',
  P5_INFORMATIONAL = 'P5_INFORMATIONAL',
}

export interface MigrationRiskAssessmentDto {
  risk_id: string;
  finding_id?: string;
  source_change_fingerprint: string;
  rule_id: string;
  dimension: string;
  severity: string;
  priority: string;
  review_priority?: ReviewPriority | string;
  reversibility: string;
  title: string;
  description: string;
  target_object?: string;
  classification?: string;
  affected_property?: string;
  source_change_id?: string;
  recommended_action?: string;
  fingerprint: string;
}

export type MigrationRiskFinding = MigrationRiskAssessmentDto;

export interface MigrationRiskReportDto {
  report_id: string;
  summary: {
    total_changes: number;
    additive_changes: number;
    removals: number;
    modifications: number;
    potentially_breaking: number;
    requires_review: number;
    total_risks: number;
    critical_count?: number;
    high_count?: number;
    medium_count?: number;
    low_count?: number;
    breaking_change_count?: number;
    data_loss_concern_count?: number;
  };
  risk_assessments: MigrationRiskAssessmentDto[];
  findings?: MigrationRiskAssessmentDto[];
  report_fingerprint: string;
  fingerprint?: string;
}

export interface AbstractMigrationOperationDto {
  operation_id: string;
  operation_type: string;
  target_object_id: string;
  target_object_name: string;
  target_object?: string;
  order_index?: number;
  stage?: number;
  description?: string;
  dependencies?: string[];
  namespace?: string | null;
  table_name?: string | null;
  prerequisite_operation_ids: string[];
  dependent_operation_ids: string[];
  engine_capability: string;
  review_priority: string;
  is_destructive: boolean;
  is_blocked: boolean;
  blocking_reasons: string[];
}

export type PlannedOperation = AbstractMigrationOperationDto;

export interface ManualDecisionGate {
  gate_id: string;
  name: string;
  description: string;
  status: string;
}

export interface PlanningStageDto {
  stage_id: string;
  stage_type: string;
  stage_order: number;
  stage_number?: number;
  name?: string;
  operation_ids: string[];
  operations?: PlannedOperation[];
  description: string;
}

export interface MigrationPlanReportDto {
  plan_id: string;
  plan_status: string;
  target_engine: string;
  plan_fingerprint: string;
  fingerprint?: string;
  summary: {
    total_operations: number;
    supported_operations: number;
    conditional_operations: number;
    blocked_operations: number;
    unsupported_operations: number;
    manual_decision_gates_count: number;
    manual_gates_count?: number;
    dependency_edges_count: number;
    stages_count: number;
    destructive_operations_count: number;
  };
  operations: AbstractMigrationOperationDto[];
  stages: PlanningStageDto[];
  manual_gates?: ManualDecisionGate[];
}

export interface GeneratedSqlStatementDto {
  statement_id: string;
  source_operation_id: string;
  source_operation_type: string;
  target_object_name: string;
  sql: string;
  dialect: string;
  execution_mode: string;
  is_destructive: boolean;
  requires_manual_review: boolean;
}

export interface SqlValidationReport {
  is_valid: boolean;
  dialect_supported: boolean;
  warnings?: string[];
}

export interface SqlMigrationArtifactDto {
  artifact_id: string;
  source_plan_id: string;
  dialect: string;
  target_engine: string;
  status: string;
  artifact_fingerprint: string;
  fingerprint?: string;
  rendered_sql_script: string;
  sql_content?: string;
  rollback_sql?: string;
  compiler_version?: string;
  validation?: SqlValidationReport;
  summary: {
    total_statements: number;
    destructive_statements: number;
    review_required_statements: number;
    transaction_blocks_count: number;
    validation_issues_count: number;
  };
  statements: GeneratedSqlStatementDto[];
  execution_notice: string;
}

export interface SafetyGateResultDto {
  gate_id: string;
  status: string;
  rationale: string;
}

export enum ReviewDecisionType {
  APPROVE = 'APPROVE',
  REJECT = 'REJECT',
  REQUEST_CHANGES = 'REQUEST_CHANGES',
  ABSTAIN = 'ABSTAIN',
}

export enum ReviewStatus {
  DRAFT = 'DRAFT',
  PENDING = 'PENDING',
  SUBMITTED = 'SUBMITTED',
  UNDER_REVIEW = 'UNDER_REVIEW',
  CHANGES_REQUESTED = 'CHANGES_REQUESTED',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
}

export interface ReviewDecisionDto {
  decision_id: string;
  reviewer_id: string;
  reviewer_role: string;
  decision_type?: string;
  decision?: ReviewDecisionType | string;
  reason?: string;
  rationale?: string;
  timestamp?: string;
  decided_at?: string;
}

export interface AuditEventDto {
  event_id: string;
  actor_id: string;
  event_type: string;
  previous_state?: string | null;
  new_state: string;
  timestamp: string;
  event_hash: string;
}

export interface MigrationReviewRequestDto {
  review_id: string;
  workspace_id: string;
  artifact_id: string;
  artifact_fingerprint: string;
  status: ReviewStatus | string;
  requester_id: string;
  created_at: string;
  required_approvals?: number;
  policy_version?: string;
  decisions: ReviewDecisionDto[];
  safety_gate_results: SafetyGateResultDto[];
  audit_events: AuditEventDto[];
  is_invalidated: boolean;
  export_eligibility: string;
}

export interface SchemaSnapshotSummary {
  id: string;
  name: string;
  engine: string;
  engine_version: string;
  fingerprint: string;
  table_count: number;
  view_count: number;
  captured_at: string;
}

export type SchemaComparisonReport = ComparisonReportDto;
export type RiskAssessmentReport = MigrationRiskReportDto;
export type MigrationPlan = MigrationPlanReportDto;
export type SqlArtifact = SqlMigrationArtifactDto;
export type GovernanceReviewRequest = MigrationReviewRequestDto;
export type AuditEventRecord = AuditEventDto;
export type ReviewDecision = ReviewDecisionDto;
