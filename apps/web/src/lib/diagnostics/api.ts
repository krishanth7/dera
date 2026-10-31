/**
 * DERA Phase 8.6 Diagnostic Dashboard — Typed API Integration.
 */

import { DiagnosticReport, DiagnosticRuleMetadata } from "./types";
import { SAMPLE_DIAGNOSTIC_REPORT, SAMPLE_RULES_METADATA } from "./fixtures";
import { env } from "@/lib/env";

const API_BASE = env.NEXT_PUBLIC_DERA_API_URL || "http://localhost:8000";

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
    enabledRuleIds?: string[];
    disabledRuleIds?: string[];
  }
): Promise<DiagnosticReport> {
  try {
    const res = await fetch(
      `${API_BASE}/api/v1/reverse-engineering/schemas/${encodeURIComponent(schemaId)}/diagnostics`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          enabled_rule_ids: options?.enabledRuleIds || null,
          disabled_rule_ids: options?.disabledRuleIds || [],
        }),
        cache: "no-store",
      }
    );

    if (!res.ok) {
      return SAMPLE_DIAGNOSTIC_REPORT;
    }

    return await res.json();
  } catch {
    return SAMPLE_DIAGNOSTIC_REPORT;
  }
}
