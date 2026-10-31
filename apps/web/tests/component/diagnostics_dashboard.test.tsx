import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import {
  SeveritySummary,
  CategorySummary,
  RuleCoverage,
  FindingsFilters,
  FindingsExplorer,
  FindingDetails,
  DiagnosticsOverview,
  SnapshotSelector,
} from "../../src/components/diagnostics";
import { SAMPLE_DIAGNOSTIC_REPORT } from "../../src/lib/diagnostics/fixtures";
import { FindingFilterState } from "../../src/lib/diagnostics/types";

describe("Phase 8.6 Diagnostic Dashboard Components", () => {
  describe("SeveritySummary", () => {
    it("renders all discrete severity levels and accessible summary", () => {
      render(<SeveritySummary summary={SAMPLE_DIAGNOSTIC_REPORT.summary} />);

      expect(screen.getByText("Severity Distribution")).toBeInTheDocument();
      expect(screen.getByText("6 total findings across all evaluated rules")).toBeInTheDocument();
      // Screen-reader accessible table caption
      expect(screen.getByText("Diagnostic Findings by Severity")).toBeInTheDocument();
    });

    it("triggers onSeverityClick when a severity card is clicked", () => {
      const handleSeverityClick = vi.fn();
      render(
        <SeveritySummary
          summary={SAMPLE_DIAGNOSTIC_REPORT.summary}
          onSeverityClick={handleSeverityClick}
        />
      );

      const criticalButton = screen.getByRole("button", { name: /filter by critical severity/i });
      fireEvent.click(criticalButton);
      expect(handleSeverityClick).toHaveBeenCalledWith("CRITICAL");
    });
  });

  describe("CategorySummary", () => {
    it("renders engineering domain categories and counts", () => {
      render(<CategorySummary findings={SAMPLE_DIAGNOSTIC_REPORT.findings} />);

      expect(screen.getByText("Rule Categories")).toBeInTheDocument();
      expect(screen.getByText("Indexes")).toBeInTheDocument();
      expect(screen.getByText("Constraints")).toBeInTheDocument();
      expect(screen.getByText("Relationships")).toBeInTheDocument();
      expect(screen.getByText("Maintainability")).toBeInTheDocument();
    });

    it("triggers onCategoryClick callback when clicked", () => {
      const handleCategoryClick = vi.fn();
      render(
        <CategorySummary
          findings={SAMPLE_DIAGNOSTIC_REPORT.findings}
          onCategoryClick={handleCategoryClick}
        />
      );

      const indexesButton = screen.getByRole("button", { name: /filter by indexes category/i });
      fireEvent.click(indexesButton);
      expect(handleCategoryClick).toHaveBeenCalledWith("INDEXES");
    });
  });

  describe("RuleCoverage", () => {
    it("renders exact rule coverage statistics and explanation", () => {
      render(<RuleCoverage explainability={SAMPLE_DIAGNOSTIC_REPORT.explainability} />);

      expect(screen.getByText("Diagnostic Rule Coverage")).toBeInTheDocument();
      expect(screen.getByText("100%")).toBeInTheDocument();
      expect(screen.getByText("Registered Rules")).toBeInTheDocument();
      expect(screen.getByText("Evaluated")).toBeInTheDocument();
      expect(screen.getByText(/Coverage represents/i)).toBeInTheDocument();
    });
  });

  describe("FindingsFilters", () => {
    const filterState: FindingFilterState = {
      searchQuery: "",
      severityFilter: "ALL",
      categoryFilter: "ALL",
      classificationFilter: "ALL",
      confidenceFilter: "ALL",
      suppressionFilter: "ALL",
      sortBy: "priority",
      sortDirection: "desc",
    };

    it("renders search input and dropdown controls", () => {
      render(
        <FindingsFilters
          filterState={filterState}
          onFilterChange={vi.fn()}
          onResetFilters={vi.fn()}
          totalFilteredCount={6}
          totalFindingsCount={6}
        />
      );

      expect(
        screen.getByPlaceholderText(/Search findings by title, rule ID, object/i)
      ).toBeInTheDocument();
      expect(screen.getByText("Showing 6 of 6 findings")).toBeInTheDocument();
    });

    it("calls onFilterChange when search query is typed", () => {
      const handleFilterChange = vi.fn();
      render(
        <FindingsFilters
          filterState={filterState}
          onFilterChange={handleFilterChange}
          onResetFilters={vi.fn()}
          totalFilteredCount={6}
          totalFindingsCount={6}
        />
      );

      const input = screen.getByPlaceholderText(/Search findings/i);
      fireEvent.change(input, { target: { value: "users" } });
      expect(handleFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({ searchQuery: "users" })
      );
    });
  });

  describe("FindingsExplorer", () => {
    it("renders table rows for findings with accessible attributes", () => {
      const handleSelect = vi.fn();
      render(
        <FindingsExplorer
          findings={SAMPLE_DIAGNOSTIC_REPORT.findings}
          selectedFinding={null}
          onSelectFinding={handleSelect}
        />
      );

      expect(screen.getByText("Primary Key Contains Nullable Column")).toBeInTheDocument();
      expect(screen.getByText("DERA-CON-001")).toBeInTheDocument();
      expect(screen.getByText("public.users")).toBeInTheDocument();
      expect(screen.getByText("Duplicate Secondary Index Detected")).toBeInTheDocument();
    });

    it("calls onSelectFinding when a row is clicked or activated via Enter", () => {
      const handleSelect = vi.fn();
      render(
        <FindingsExplorer
          findings={SAMPLE_DIAGNOSTIC_REPORT.findings}
          selectedFinding={null}
          onSelectFinding={handleSelect}
        />
      );

      const row = screen.getByText("Primary Key Contains Nullable Column").closest("tr");
      expect(row).not.toBeNull();
      fireEvent.click(row!);
      expect(handleSelect).toHaveBeenCalledWith(
        expect.objectContaining({ rule_id: "DERA-CON-001" })
      );
    });

    it("renders empty state when findings list is empty", () => {
      render(
        <FindingsExplorer
          findings={[]}
          selectedFinding={null}
          onSelectFinding={vi.fn()}
        />
      );

      expect(screen.getByText("No Diagnostic Findings")).toBeInTheDocument();
    });
  });

  describe("FindingDetails", () => {
    const finding = SAMPLE_DIAGNOSTIC_REPORT.findings[0];

    it("renders complete finding details, rationale, and recommendation", () => {
      render(<FindingDetails finding={finding} onClose={vi.fn()} />);

      expect(screen.getByText("Primary Key Contains Nullable Column")).toBeInTheDocument();
      expect(screen.getByText(/Severity Rationale/i)).toBeInTheDocument();
      expect(screen.getByText(/public.users as CRITICAL/i)).toBeInTheDocument();
      expect(screen.getByText("Primary Key Integrity Remediation")).toBeInTheDocument();
      expect(screen.getByText(/Verified Evidence/i)).toBeInTheDocument();
      expect(screen.getByText(/Suppression Governance/i)).toBeInTheDocument();
    });

    it("triggers onClose when close button is clicked", () => {
      const handleClose = vi.fn();
      render(<FindingDetails finding={finding} onClose={handleClose} />);

      const closeButton = screen.getByRole("button", { name: /close details panel/i });
      fireEvent.click(closeButton);
      expect(handleClose).toHaveBeenCalled();
    });
  });

  describe("SnapshotSelector", () => {
    it("renders target selector and re-evaluate button", () => {
      const handleReevaluate = vi.fn();
      render(
        <SnapshotSelector
          currentSnapshotId="live"
          onEvaluateLive={handleReevaluate}
        />
      );

      expect(screen.getByText(/Evaluation Target:/i)).toBeInTheDocument();
      expect(screen.getByText("Live Schema (Current)")).toBeInTheDocument();
      const reevalButton = screen.getByRole("button", { name: /re-evaluate/i });
      fireEvent.click(reevalButton);
      expect(handleReevaluate).toHaveBeenCalled();
    });
  });

  describe("DiagnosticsOverview Integration", () => {
    it("renders overall dashboard header and KPI summary cards", () => {
      render(
        <DiagnosticsOverview
          report={SAMPLE_DIAGNOSTIC_REPORT}
          workspaceName="Test Workspace"
          connectionName="Test DB"
          engineName="PostgreSQL"
        />
      );

      expect(screen.getByText("Schema Diagnostics & Intelligence")).toBeInTheDocument();
      expect(screen.getByText("Test Workspace")).toBeInTheDocument();
      expect(screen.getByText("Total Findings")).toBeInTheDocument();
      expect(screen.getByText("Severity Distribution")).toBeInTheDocument();
      expect(screen.getByText("Diagnostic Rule Coverage")).toBeInTheDocument();
    });
  });
});
