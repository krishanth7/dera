/**
 * DERA — Database Engineering & Reverse Analysis
 * Shared Canonical Schema Contracts (TypeScript)
 *
 * Deterministic database models and static rule interfaces.
 * Copyright (c) 2026 Krishanth. All rights reserved.
 * Licensed under the MIT License.
 */

export interface DatabaseColumn {
  name: string;
  data_type: string;
  nullable: boolean;
  default_value?: string | null;
  is_primary_key: boolean;
  comment?: string | null;
}

export interface PrimaryKeyConstraint {
  name: string;
  columns: string[];
}

export interface ForeignKeyConstraint {
  name: string;
  constrained_columns: string[];
  referenced_table: string;
  referenced_columns: string[];
  on_delete: "NO ACTION" | "RESTRICT" | "CASCADE" | "SET NULL" | "SET DEFAULT";
  on_update: "NO ACTION" | "RESTRICT" | "CASCADE" | "SET NULL" | "SET DEFAULT";
}

export interface TableIndex {
  name: string;
  columns: string[];
  is_unique: boolean;
  method: string;
}

export interface DatabaseTable {
  schema: string;
  name: string;
  columns: DatabaseColumn[];
  primary_key?: PrimaryKeyConstraint | null;
  foreign_keys: ForeignKeyConstraint[];
  indexes: TableIndex[];
  comment?: string | null;
}

export interface SchemaSnapshot {
  version: string;
  dialect: "postgresql" | "mysql" | "sqlite" | "sqlserver";
  extracted_at: string;
  tables: Record<string, DatabaseTable>;
  metadata: Record<string, unknown>;
}

export type DiagnosticSeverityLevel =
  | "informational"
  | "low"
  | "medium"
  | "high"
  | "critical";

export type FindingClassificationType =
  | "confirmed_structural_defect"
  | "potential_engineering_concern"
  | "optimization_candidate"
  | "maintainability_concern"
  | "naming_convention_deviation"
  | "informational_observation"
  | "metadata_limitation"
  | "internal_inspection_integrity_issue";

export type FindingConfidenceType =
  | "verified"
  | "conditional"
  | "incomplete"
  | "unsupported";

export type EvidenceCompletenessType =
  | "complete"
  | "partial"
  | "restricted"
  | "unsupported"
  | "unknown";

export type FindingLifecycleStateType =
  | "open"
  | "acknowledged"
  | "suppressed"
  | "resolved"
  | "reopened";

export interface DiagnosticEvidenceItem {
  object_id: string;
  field_name: string;
  observed_value: unknown;
  expected_value?: unknown;
  message?: string;
  provenance_reference?: string | null;
  context_data?: Record<string, unknown>;
  evidence_type?: string;
  completeness?: EvidenceCompletenessType;
}

export interface StructuredRecommendationItem {
  recommendation_id: string;
  rule_id: string;
  title: string;
  description: string;
  suggested_action: string;
  risk_considerations: string;
  verification_steps: string[];
  limitations: string;
  version: string;
  is_advisory: boolean;
}

export interface DiagnosticFinding {
  rule_id: string;
  severity: DiagnosticSeverityLevel | "info" | "warning" | "critical";
  object_id?: string;
  table?: string;
  title?: string;
  message?: string;
  description?: string;
  remediation?: string;
  recommendation?: string | null;
  severity_rationale?: string;
  fingerprint?: string;
  finding_id?: string;
  category?: string;
  classification?: FindingClassificationType;
  original_severity?: DiagnosticSeverityLevel;
  confidence?: FindingConfidenceType;
  metadata_completeness?: EvidenceCompletenessType;
  evidence?: DiagnosticEvidenceItem[];
  structured_recommendation?: StructuredRecommendationItem | null;
  lifecycle_state?: FindingLifecycleStateType;
  is_suppressed?: boolean;
  suppression_id?: string | null;
  override_id?: string | null;
  priority_score?: number;
  priority_rank?: string;
}

export interface TableDependencyGraph {
  nodes: string[];
  edges: Array<{
    source: string;
    target: string;
    foreign_key: string;
  }>;
  topological_order: string[];
  has_cycle: boolean;
}

export interface DiagnosticSuppressionItem {
  suppression_id: string;
  scope: "fingerprint" | "object" | "rule";
  reason: string;
  authorized_actor: string;
  created_at: string;
  rule_id?: string | null;
  fingerprint?: string | null;
  scoped_object_id?: string | null;
  expires_at?: string | null;
  status: "active" | "expired" | "revoked";
  notes?: string;
}

export interface ReportExplainabilitySummaryItem {
  total_rules_considered: number;
  evaluated_rules_count: number;
  skipped_rules_count: number;
  unsupported_rules_count: number;
  insufficient_metadata_count: number;
  errored_rules_count: number;
  findings_by_severity: Record<string, number>;
  findings_by_classification: Record<string, number>;
  findings_by_lifecycle: Record<string, number>;
  findings_by_confidence: Record<string, number>;
  active_suppression_count: number;
  severity_override_count: number;
  rule_set_version: string;
  severity_policy_version: string;
  recommendation_catalog_version: string;
  config_fingerprint: string;
  skipped_reasons: Record<string, string>;
  unsupported_reasons: Record<string, string>;
}
