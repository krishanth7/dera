/**
 * DERA Phase 8.6 Diagnostic Dashboard — Deterministic Formatters & Algorithms.
 */

import {
  DiagnosticFinding,
  DiagnosticSeverity,
  FindingClassification,
  FindingFilterState,
  FindingLifecycleState,
  PriorityRank,
  ReportExplainabilitySummary,
} from "./types";

export function formatSeverity(severity: DiagnosticSeverity): string {
  switch (severity) {
    case "CRITICAL":
      return "Critical";
    case "HIGH":
      return "High";
    case "MEDIUM":
      return "Medium";
    case "LOW":
      return "Low";
    case "INFORMATIONAL":
      return "Informational";
    default:
      return severity;
  }
}

export function formatClassification(classification: FindingClassification): string {
  switch (classification) {
    case "CONFIRMED_STRUCTURAL_DEFECT":
      return "Structural Defect";
    case "POTENTIAL_ENGINEERING_CONCERN":
      return "Engineering Concern";
    case "OPTIMIZATION_CANDIDATE":
      return "Optimization Candidate";
    case "MAINTAINABILITY_CONCERN":
      return "Maintainability Concern";
    case "NAMING_CONVENTION_DEVIATION":
      return "Naming Deviation";
    case "INFORMATIONAL_OBSERVATION":
      return "Informational";
    case "METADATA_LIMITATION":
      return "Metadata Limitation";
    case "INTERNAL_INSPECTION_INTEGRITY_ISSUE":
      return "Inspection Anomaly";
    default:
      return classification;
  }
}

export function formatPriorityRank(rank: PriorityRank): string {
  switch (rank) {
    case "URGENT":
      return "P1 - Urgent";
    case "IMPORTANT":
      return "P2 - Important";
    case "NORMAL":
      return "P3 - Normal";
    case "LOW_PRIORITY":
      return "P4 - Low Priority";
    default:
      return rank;
  }
}

export function formatLifecycleState(state: FindingLifecycleState): string {
  switch (state) {
    case "OPEN":
      return "Open";
    case "ACKNOWLEDGED":
      return "Acknowledged";
    case "SUPPRESSED":
      return "Suppressed";
    case "RESOLVED":
      return "Resolved";
    case "REOPENED":
      return "Reopened";
    default:
      return state;
  }
}

/**
 * Calculates rule coverage percentage deterministically:
 * Evaluated applicable rules / Total applicable rules * 100
 * Handles zero denominators safely without NaN or Infinity.
 */
export function computeRuleCoveragePercentage(
  evaluatedRules: number,
  totalApplicableRules: number
): number {
  if (totalApplicableRules <= 0) {
    return 0;
  }
  const ratio = (evaluatedRules / totalApplicableRules) * 100;
  return Math.min(100, Math.max(0, Math.round(ratio * 10) / 10));
}

/**
 * Derives rule coverage statistics from an explainability summary.
 */
export function deriveCoverageStats(explainability?: ReportExplainabilitySummary) {
  if (!explainability) {
    return {
      totalRegistered: 0,
      evaluated: 0,
      skipped: 0,
      unsupported: 0,
      insufficientMetadata: 0,
      coveragePercentage: 0,
    };
  }

  const total = explainability.total_rules_registered || 0;
  const evaluated = explainability.rules_evaluated || 0;
  const skipped = explainability.rules_skipped || 0;
  const unsupported = explainability.rules_unsupported || 0;
  const insufficient = explainability.insufficient_metadata_count || 0;
  const coveragePercentage = computeRuleCoveragePercentage(evaluated, total);

  return {
    totalRegistered: total,
    evaluated,
    skipped,
    unsupported,
    insufficientMetadata: insufficient,
    coveragePercentage,
  };
}

const SEVERITY_ORDER: Record<DiagnosticSeverity, number> = {
  CRITICAL: 5,
  HIGH: 4,
  MEDIUM: 3,
  LOW: 2,
  INFORMATIONAL: 1,
};

/**
 * Deterministically filters a findings collection according to multi-attribute filter state.
 */
export function filterFindings(
  findings: DiagnosticFinding[],
  filters: FindingFilterState
): DiagnosticFinding[] {
  return findings.filter((finding) => {
    // 1. Search Query (title, rule_id, object_id)
    if (filters.searchQuery.trim().length > 0) {
      const q = filters.searchQuery.toLowerCase().trim();
      const matchTitle = finding.title.toLowerCase().includes(q);
      const matchRule = finding.rule_id.toLowerCase().includes(q);
      const matchObject = finding.object_id.toLowerCase().includes(q);
      const matchDescription = finding.description.toLowerCase().includes(q);
      if (!matchTitle && !matchRule && !matchObject && !matchDescription) {
        return false;
      }
    }

    // 2. Severity Filter
    if (filters.severityFilter !== "ALL" && finding.severity !== filters.severityFilter) {
      return false;
    }

    // 3. Category Filter
    if (filters.categoryFilter !== "ALL" && finding.category !== filters.categoryFilter) {
      return false;
    }

    // 4. Classification Filter
    if (
      filters.classificationFilter !== "ALL" &&
      finding.classification !== filters.classificationFilter
    ) {
      return false;
    }

    // 5. Confidence Filter
    if (filters.confidenceFilter !== "ALL" && finding.confidence !== filters.confidenceFilter) {
      return false;
    }

    // 6. Suppression Filter
    if (filters.suppressionFilter === "ACTIVE_ONLY" && finding.is_suppressed) {
      return false;
    }
    if (filters.suppressionFilter === "SUPPRESSED_ONLY" && !finding.is_suppressed) {
      return false;
    }

    return true;
  });
}

/**
 * Deterministically sorts findings using configured sort criteria with stable tie-breakers.
 */
export function sortFindings(
  findings: DiagnosticFinding[],
  sortBy: FindingFilterState["sortBy"],
  sortDirection: FindingFilterState["sortDirection"]
): DiagnosticFinding[] {
  const dir = sortDirection === "asc" ? 1 : -1;

  return [...findings].sort((a, b) => {
    let comparison = 0;

    switch (sortBy) {
      case "priority":
        comparison = (a.priority_score - b.priority_score) * dir;
        break;
      case "severity":
        comparison = (SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]) * dir;
        break;
      case "rule":
        comparison = a.rule_id.localeCompare(b.rule_id) * dir;
        break;
      case "object":
        comparison = a.object_id.localeCompare(b.object_id) * dir;
        break;
      default:
        comparison = (a.priority_score - b.priority_score) * dir;
    }

    if (comparison !== 0) {
      return comparison;
    }

    // Deterministic tie-breakers: severity rank -> rule ID -> object ID -> fingerprint
    const sevDiff = SEVERITY_ORDER[b.severity] - SEVERITY_ORDER[a.severity];
    if (sevDiff !== 0) return sevDiff;

    const ruleDiff = a.rule_id.localeCompare(b.rule_id);
    if (ruleDiff !== 0) return ruleDiff;

    const objDiff = a.object_id.localeCompare(b.object_id);
    if (objDiff !== 0) return objDiff;

    return a.fingerprint.localeCompare(b.fingerprint);
  });
}
