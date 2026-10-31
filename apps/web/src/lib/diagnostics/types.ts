/**
 * DERA Phase 8.6 Diagnostic Dashboard — Frontend Type Contracts.
 * Grounded in Phase 8.1–8.5 backend models and @dera/contracts.
 */

export type DiagnosticSeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFORMATIONAL";

export type FindingClassification =
  | "CONFIRMED_STRUCTURAL_DEFECT"
  | "POTENTIAL_ENGINEERING_CONCERN"
  | "OPTIMIZATION_CANDIDATE"
  | "MAINTAINABILITY_CONCERN"
  | "NAMING_CONVENTION_DEVIATION"
  | "INFORMATIONAL_OBSERVATION"
  | "METADATA_LIMITATION"
  | "INTERNAL_INSPECTION_INTEGRITY_ISSUE";

export type FindingConfidence = "VERIFIED" | "CONDITIONAL" | "INCOMPLETE" | "UNSUPPORTED";

export type EvidenceCompleteness = "COMPLETE" | "PARTIAL" | "RESTRICTED" | "UNSUPPORTED" | "UNKNOWN";

export type FindingLifecycleState = "OPEN" | "ACKNOWLEDGED" | "SUPPRESSED" | "RESOLVED" | "REOPENED";

export type PriorityRank = "URGENT" | "IMPORTANT" | "NORMAL" | "LOW_PRIORITY";

export interface TypedEvidence {
  evidence_type?: string;
  field_name?: string;
  object_id: string;
  observed_value?: unknown;
  expected_value?: unknown;
  message?: string;
  provenance?: {
    engine?: string;
    connector_version?: string;
    inspection_timestamp?: string;
    snapshot_id?: string;
  };
  completeness?: EvidenceCompleteness;
  unresolved?: boolean;
}

export interface StructuredRecommendation {
  recommendation_id: string;
  rule_id: string;
  title: string;
  action: string;
  preconditions: string[];
  risk_considerations: string[];
  verification_steps: string[];
  is_destructive_prohibited: boolean;
}

export interface DiagnosticFinding {
  fingerprint: string;
  rule_id: string;
  rule_version: string;
  object_id: string;
  severity: DiagnosticSeverity;
  severity_rationale?: string;
  title: string;
  description: string;
  category: string;
  classification: FindingClassification;
  confidence: FindingConfidence;
  metadata_completeness: EvidenceCompleteness;
  evidence: TypedEvidence[];
  recommendation?: string;
  structured_recommendation?: StructuredRecommendation;
  lifecycle_state: FindingLifecycleState;
  is_suppressed: boolean;
  suppression_id?: string;
  override_id?: string;
  priority_score: number;
  priority_rank: PriorityRank;
}

export interface DiagnosticSummary {
  total_findings: number;
  critical_findings: number;
  high_findings: number;
  medium_findings: number;
  low_findings: number;
  informational_findings: number;
  suppressed_findings: number;
  rules_evaluated: number;
}

export interface ReportExplainabilitySummary {
  total_rules_registered: number;
  rules_evaluated: number;
  rules_skipped: number;
  rules_unsupported: number;
  insufficient_metadata_count: number;
  evaluation_errors_count: number;
  findings_by_severity: Record<string, number>;
  findings_by_classification: Record<string, number>;
  total_suppressed_findings: number;
  evidence_completeness_breakdown: Record<string, number>;
  unresolved_reference_count: number;
}

export interface DiagnosticReport {
  report_id: string;
  schema_id: string;
  snapshot_id?: string;
  evaluated_at: string;
  summary: DiagnosticSummary;
  findings: DiagnosticFinding[];
  explainability?: ReportExplainabilitySummary;
  metadata?: {
    engine_version?: string;
    severity_policy_version?: string;
    recommendation_catalog_version?: string;
    config_fingerprint?: string;
    evaluation_duration_ms?: number;
  };
}

export interface DiagnosticRuleMetadata {
  rule_id: string;
  title: string;
  description: string;
  version: string;
  category: string;
  default_severity: string;
  supported_object_kinds: string[];
  required_capabilities: string[];
  supported_engines: string[];
  documentation_url?: string;
}

export interface FindingFilterState {
  searchQuery: string;
  severityFilter: string; // "ALL" | DiagnosticSeverity
  categoryFilter: string; // "ALL" | Category
  classificationFilter: string; // "ALL" | FindingClassification
  confidenceFilter: string; // "ALL" | FindingConfidence
  suppressionFilter: "ALL" | "ACTIVE_ONLY" | "SUPPRESSED_ONLY";
  sortBy: "priority" | "severity" | "rule" | "object";
  sortDirection: "asc" | "desc";
}
