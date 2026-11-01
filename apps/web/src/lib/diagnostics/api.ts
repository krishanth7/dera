/**
 * DERA Phase 8.6 Diagnostic Dashboard — Typed API Integration.
 */

import {
  DiagnosticFinding,
  DiagnosticReport,
  DiagnosticRuleMetadata,
  DiagnosticSeverity,
  DiagnosticSummary,
  EvidenceCompleteness,
  FindingClassification,
  FindingConfidence,
  FindingLifecycleState,
  PriorityRank,
  StructuredRecommendation,
} from "./types";
import { SAMPLE_DIAGNOSTIC_REPORT, SAMPLE_RULES_METADATA } from "./fixtures";
import { env } from "@/lib/env";

const API_BASE = env.NEXT_PUBLIC_DERA_API_URL || "http://localhost:8000";

/**
 * Normalizes backend report response to match frontend DiagnosticReport contracts.
 */
export function normalizeDiagnosticReport(raw: any): DiagnosticReport {
  if (!raw) {
    return SAMPLE_DIAGNOSTIC_REPORT;
  }

  const summaryRaw = raw.summary || {};
  const findingsBySev = summaryRaw.findings_by_severity || {};

  const summary: DiagnosticSummary = {
    total_findings: summaryRaw.total_findings ?? raw.findings?.length ?? 0,
    critical_findings:
      summaryRaw.critical_findings ??
      findingsBySev.CRITICAL ??
      findingsBySev.critical ??
      0,
    high_findings:
      summaryRaw.high_findings ??
      findingsBySev.HIGH ??
      findingsBySev.high ??
      0,
    medium_findings:
      summaryRaw.medium_findings ??
      findingsBySev.MEDIUM ??
      findingsBySev.medium ??
      0,
    low_findings:
      summaryRaw.low_findings ??
      findingsBySev.LOW ??
      findingsBySev.low ??
      0,
    informational_findings:
      summaryRaw.informational_findings ??
      findingsBySev.INFORMATIONAL ??
      findingsBySev.informational ??
      0,
    suppressed_findings:
      summaryRaw.suppressed_findings ??
      raw.suppressions_applied?.length ??
      raw.findings?.filter((f: any) => f.is_suppressed)?.length ??
      0,
    rules_evaluated:
      summaryRaw.rules_evaluated ??
      summaryRaw.total_rules_evaluated ??
      raw.rule_evaluations?.length ??
      0,
  };

  const findings: DiagnosticFinding[] = (raw.findings || []).map((f: any) => {
    const sev = (f.severity || "INFORMATIONAL").toUpperCase() as DiagnosticSeverity;

    let structuredRec: StructuredRecommendation | undefined = undefined;
    if (f.structured_recommendation) {
      const sr = f.structured_recommendation;
      structuredRec = {
        recommendation_id: sr.recommendation_id || "",
        rule_id: sr.rule_id || f.rule_id,
        title: sr.title || "",
        action: sr.action || sr.suggested_action || "",
        preconditions: Array.isArray(sr.preconditions) ? sr.preconditions : [],
        risk_considerations: Array.isArray(sr.risk_considerations)
          ? sr.risk_considerations
          : sr.risk_considerations
          ? [sr.risk_considerations]
          : [],
        verification_steps: Array.isArray(sr.verification_steps)
          ? sr.verification_steps
          : [],
        is_destructive_prohibited: sr.is_destructive_prohibited ?? true,
      };
    }

    return {
      fingerprint: f.fingerprint || "",
      rule_id: f.rule_id,
      rule_version: f.rule_version || "1.0.0",
      object_id: f.object_id,
      severity: sev,
      severity_rationale: f.severity_rationale,
      title: f.title,
      description: f.description,
      category: f.category || "STRUCTURAL_INTEGRITY",
      classification: (f.classification || "POTENTIAL_ENGINEERING_CONCERN") as FindingClassification,
      confidence: (f.confidence || "VERIFIED") as FindingConfidence,
      metadata_completeness: (f.metadata_completeness || "COMPLETE") as EvidenceCompleteness,
      evidence: Array.isArray(f.evidence) ? f.evidence : [],
      recommendation: f.recommendation,
      structured_recommendation: structuredRec,
      lifecycle_state: (f.lifecycle_state || "OPEN") as FindingLifecycleState,
      is_suppressed: Boolean(f.is_suppressed),
      suppression_id: f.suppression_id,
      override_id: f.override_id,
      priority_score: f.priority_score ?? 0,
      priority_rank: (f.priority_rank || "NORMAL") as PriorityRank,
    };
  });

  return {
    ...raw,
    summary,
    findings,
  };
}

/**
 * Fetches all registered diagnostic rules from the backend.
 */
export async function getDiagnosticRules(): Promise<DiagnosticRuleMetadata[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/reverse-engineering/diagnostics/rules`, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    });

    if (!res.ok) {
      return SAMPLE_RULES_METADATA;
    }

    return await res.json();
  } catch {
    return SAMPLE_RULES_METADATA;
  }
}

/**
 * Executes or retrieves diagnostic evaluation report for a schema.
 */
export async function evaluateSchemaDiagnostics(
  schemaId: string,
  options?: {
    workspaceId?: string;
    enabledRuleIds?: string[];
    disabledRuleIds?: string[];
  }
): Promise<DiagnosticReport> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };
  if (options?.workspaceId) {
    headers["X-Workspace-Id"] = options.workspaceId;
  }

  const queryParams = new URLSearchParams();
  if (options?.workspaceId) {
    queryParams.set("workspace_id", options.workspaceId);
  }
  const queryString = queryParams.toString() ? `?${queryParams.toString()}` : "";

  const res = await fetch(
    `${API_BASE}/api/v1/reverse-engineering/schemas/${encodeURIComponent(schemaId)}/diagnostics${queryString}`,
    {
      method: "POST",
      headers,
      body: JSON.stringify({
        enabled_rule_ids: options?.enabledRuleIds || null,
        disabled_rule_ids: options?.disabledRuleIds || [],
      }),
      cache: "no-store",
    }
  );

  if (!res.ok) {
    const errorBody = await res.text().catch(() => "");
    throw new Error(`Evaluation failed with status ${res.status}: ${errorBody || res.statusText}`);
  }

  const data = await res.json();
  return normalizeDiagnosticReport(data);
}
