/** Imported plan API v1. Null means unavailable, never zero. */
export interface PlanNode {
  node_id: string;
  parent_id: string | null;
  depth: number;
  operation: string;
  native_operation: string;
  child_ids: string[];
  relation: { name: string | null; namespace: string | null; alias: string | null; index_name: string | null; covering_index: boolean };
  estimate: { startup: number | null; total: number | null; rows: number | null; row_width: number | null; unit: string; semantics: string };
  actual: { rows: number | null; loops: number | null; total_time_ms: number | null; row_semantics: string; time_semantics: string; row_estimation_ratio: number | null; estimation_case: string };
  metadata_json: string;
}
export interface PlanFinding {
  finding_id: string; rule_id: string; severity: string; node_id: string;
  evidence: string[]; explanation: string; suggested_investigation: string; limitations: string[];
}
export interface PlanReport {
  status: "COMPLETE" | "PARTIAL";
  dialect: string;
  nodes: PlanNode[];
  root_ids: string[];
  summary: { node_count: number; max_depth: number; has_actual_metrics: boolean; estimated_total_cost: number | null; estimated_startup_cost: number | null; execution_time_ms: number | null; cost_limitation: string; operation_counts: Record<string, number> };
  diagnostics: PlanFinding[];
  recommendations: { recommendation_id: string; node_id: string; title: string; suggested_action: string; expected_benefit: string; limitations: string[] }[];
  limitations: string[];
  plan_fingerprint: string;
  sql_diagnostics: { analysis_status: string; total_findings: number } | null;
}
export interface PlanRequest {
  dialect: "postgresql" | "mysql" | "mariadb" | "sqlite";
  format: "postgresql-json" | "mysql-json-v1" | "mariadb-json" | "sqlite-eqp";
  plan_json: string;
  sql?: string;
}
