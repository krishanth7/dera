import { describe, it, expect } from "vitest";
import {
  formatSeverity,
  formatClassification,
  formatPriorityRank,
  formatLifecycleState,
  computeRuleCoveragePercentage,
  deriveCoverageStats,
  filterFindings,
  sortFindings,
} from "../../src/lib/diagnostics/formatters";
import { SAMPLE_DIAGNOSTIC_REPORT } from "../../src/lib/diagnostics/fixtures";
import { FindingFilterState } from "../../src/lib/diagnostics/types";

describe("Phase 8.6 Diagnostic Dashboard Formatters & Coverage", () => {
  it("formats severities accurately", () => {
    expect(formatSeverity("CRITICAL")).toBe("Critical");
    expect(formatSeverity("HIGH")).toBe("High");
    expect(formatSeverity("MEDIUM")).toBe("Medium");
    expect(formatSeverity("LOW")).toBe("Low");
    expect(formatSeverity("INFORMATIONAL")).toBe("Informational");
  });

  it("formats classifications to human-readable domain strings", () => {
    expect(formatClassification("CONFIRMED_STRUCTURAL_DEFECT")).toBe("Structural Defect");
    expect(formatClassification("POTENTIAL_ENGINEERING_CONCERN")).toBe("Engineering Concern");
    expect(formatClassification("OPTIMIZATION_CANDIDATE")).toBe("Optimization Candidate");
    expect(formatClassification("MAINTAINABILITY_CONCERN")).toBe("Maintainability Concern");
    expect(formatClassification("NAMING_CONVENTION_DEVIATION")).toBe("Naming Deviation");
  });

  it("formats priority ranks and lifecycle states", () => {
    expect(formatPriorityRank("URGENT")).toBe("P1 - Urgent");
    expect(formatPriorityRank("IMPORTANT")).toBe("P2 - Important");
    expect(formatPriorityRank("NORMAL")).toBe("P3 - Normal");
    expect(formatPriorityRank("LOW_PRIORITY")).toBe("P4 - Low Priority");

    expect(formatLifecycleState("OPEN")).toBe("Open");
    expect(formatLifecycleState("ACKNOWLEDGED")).toBe("Acknowledged");
    expect(formatLifecycleState("SUPPRESSED")).toBe("Suppressed");
    expect(formatLifecycleState("RESOLVED")).toBe("Resolved");
    expect(formatLifecycleState("REOPENED")).toBe("Reopened");
  });

  describe("Coverage Calculations", () => {
    it("handles zero denominator safely without NaN or infinity", () => {
      expect(computeRuleCoveragePercentage(0, 0)).toBe(0);
      expect(computeRuleCoveragePercentage(5, 0)).toBe(0);
    });

    it("calculates exact rounded percentages", () => {
      expect(computeRuleCoveragePercentage(15, 15)).toBe(100);
      expect(computeRuleCoveragePercentage(1, 3)).toBe(33.3);
      expect(computeRuleCoveragePercentage(2, 3)).toBe(66.7);
      expect(computeRuleCoveragePercentage(14, 15)).toBe(93.3);
    });

    it("derives coverage statistics from explainability payload", () => {
      const stats = deriveCoverageStats(SAMPLE_DIAGNOSTIC_REPORT.explainability);
      expect(stats.totalRegistered).toBe(15);
      expect(stats.evaluated).toBe(15);
      expect(stats.skipped).toBe(0);
      expect(stats.unsupported).toBe(0);
      expect(stats.coveragePercentage).toBe(100);
    });

    it("returns zeroed statistics when explainability is undefined", () => {
      const stats = deriveCoverageStats(undefined);
      expect(stats.totalRegistered).toBe(0);
      expect(stats.evaluated).toBe(0);
      expect(stats.coveragePercentage).toBe(0);
    });
  });

  describe("Filtering & Search Logic", () => {
    const findings = SAMPLE_DIAGNOSTIC_REPORT.findings;

    const baseFilter: FindingFilterState = {
      searchQuery: "",
      severityFilter: "ALL",
      categoryFilter: "ALL",
      classificationFilter: "ALL",
      confidenceFilter: "ALL",
      suppressionFilter: "ALL",
      sortBy: "priority",
      sortDirection: "desc",
    };

    it("returns all findings under default filter state", () => {
      const result = filterFindings(findings, baseFilter);
      expect(result.length).toBe(findings.length);
    });

    it("filters findings by search query across title, rule ID, and object ID", () => {
      const byTitle = filterFindings(findings, { ...baseFilter, searchQuery: "Primary Key" });
      expect(byTitle.length).toBe(1);
      expect(byTitle[0].rule_id).toBe("DERA-CON-001");

      const byRule = filterFindings(findings, { ...baseFilter, searchQuery: "DERA-IDX" });
      expect(byRule.length).toBe(2);

      const byObject = filterFindings(findings, { ...baseFilter, searchQuery: "public.orders" });
      expect(byObject.length).toBe(1);
    });

    it("filters findings by severity level", () => {
      const criticals = filterFindings(findings, { ...baseFilter, severityFilter: "CRITICAL" });
      expect(criticals.length).toBe(1);
      expect(criticals[0].severity).toBe("CRITICAL");

      const mediums = filterFindings(findings, { ...baseFilter, severityFilter: "MEDIUM" });
      expect(mediums.length).toBe(2);
    });

    it("filters findings by category", () => {
      const indexes = filterFindings(findings, { ...baseFilter, categoryFilter: "INDEXES" });
      expect(indexes.length).toBe(2);

      const constraints = filterFindings(findings, { ...baseFilter, categoryFilter: "CONSTRAINTS" });
      expect(constraints.length).toBe(1);
    });

    it("filters findings by suppression status", () => {
      const activeOnly = filterFindings(findings, { ...baseFilter, suppressionFilter: "ACTIVE_ONLY" });
      expect(activeOnly.length).toBe(5);
      expect(activeOnly.every((f) => !f.is_suppressed)).toBe(true);

      const suppressedOnly = filterFindings(findings, { ...baseFilter, suppressionFilter: "SUPPRESSED_ONLY" });
      expect(suppressedOnly.length).toBe(1);
      expect(suppressedOnly[0].is_suppressed).toBe(true);
      expect(suppressedOnly[0].rule_id).toBe("DERA-MAINT-003");
    });
  });

  describe("Deterministic Sorting Logic", () => {
    const findings = SAMPLE_DIAGNOSTIC_REPORT.findings;

    it("sorts deterministically by priority score descending", () => {
      const sorted = sortFindings(findings, "priority", "desc");
      for (let i = 0; i < sorted.length - 1; i++) {
        expect(sorted[i].priority_score).toBeGreaterThanOrEqual(sorted[i + 1].priority_score);
      }
    });

    it("sorts deterministically by severity descending", () => {
      const sorted = sortFindings(findings, "severity", "desc");
      expect(sorted[0].severity).toBe("CRITICAL");
      expect(sorted[1].severity).toBe("HIGH");
    });

    it("sorts deterministically by rule ID ascending", () => {
      const sorted = sortFindings(findings, "rule", "asc");
      expect(sorted[0].rule_id).toBe("DERA-CON-001");
      expect(sorted[sorted.length - 1].rule_id).toBe("DERA-REL-002");
    });

    it("breaks ties using stable deterministic hierarchy", () => {
      // Create duplicate score findings with different object IDs
      const tied1 = { ...findings[2], object_id: "public.b_table", fingerprint: "fp-b" };
      const tied2 = { ...findings[2], object_id: "public.a_table", fingerprint: "fp-a" };
      const sorted = sortFindings([tied1, tied2], "priority", "desc");
      expect(sorted[0].object_id).toBe("public.a_table");
      expect(sorted[1].object_id).toBe("public.b_table");
    });
  });
});
