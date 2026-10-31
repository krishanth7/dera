"use client";

import React, { useState, useMemo } from "react";
import {
  DiagnosticFinding,
  DiagnosticReport,
  FindingFilterState,
  DiagnosticSeverity,
} from "@/lib/diagnostics/types";
import { filterFindings, sortFindings } from "@/lib/diagnostics/formatters";
import { SeveritySummary } from "./SeveritySummary";
import { CategorySummary } from "./CategorySummary";
import { RuleCoverage } from "./RuleCoverage";
import { FindingsFilters } from "./FindingsFilters";
import { FindingsExplorer } from "./FindingsExplorer";
import { FindingDetails } from "./FindingDetails";
import { SnapshotSelector } from "./SnapshotSelector";
import {
  ShieldAlert,
  AlertTriangle,
  Info,
  CheckCircle2,
  Database,
  Calendar,
  Layers,
  Sparkles,
} from "lucide-react";

interface DiagnosticsOverviewProps {
  report: DiagnosticReport;
  workspaceName?: string;
  connectionName?: string;
  engineName?: string;
  onReevaluate?: () => void;
  isLoading?: boolean;
  className?: string;
}

const INITIAL_FILTER_STATE: FindingFilterState = {
  searchQuery: "",
  severityFilter: "ALL",
  categoryFilter: "ALL",
  classificationFilter: "ALL",
  confidenceFilter: "ALL",
  suppressionFilter: "ALL",
  sortBy: "priority",
  sortDirection: "desc",
};

export function DiagnosticsOverview({
  report,
  workspaceName = "Primary Workspace",
  connectionName = "Production DB",
  engineName = "PostgreSQL",
  onReevaluate,
  isLoading = false,
  className = "",
}: DiagnosticsOverviewProps) {
  const [filterState, setFilterState] = useState<FindingFilterState>(INITIAL_FILTER_STATE);
  const [selectedFinding, setSelectedFinding] = useState<DiagnosticFinding | null>(null);

  // Apply filters and sorting deterministically
  const filteredFindings = useMemo(() => {
    const filtered = filterFindings(report.findings, filterState);
    return sortFindings(filtered, filterState.sortBy, filterState.sortDirection);
  }, [report.findings, filterState]);

  const handleSeverityCardClick = (severity: DiagnosticSeverity) => {
    setFilterState((prev) => ({
      ...prev,
      severityFilter: prev.severityFilter === severity ? "ALL" : severity,
    }));
  };

  const handleCategoryCardClick = (category: string) => {
    setFilterState((prev) => ({
      ...prev,
      categoryFilter: prev.categoryFilter === category ? "ALL" : category,
    }));
  };

  const handleResetFilters = () => {
    setFilterState(INITIAL_FILTER_STATE);
  };

  return (
    <div className={`space-y-6 ${className}`} aria-label="DERA Diagnostics Dashboard">
      {/* 1. Header Information Panel */}
      <div className="flex flex-col justify-between gap-4 rounded-lg border border-slate-200 bg-white p-5 shadow-xs sm:flex-row sm:items-center dark:border-slate-800 dark:bg-slate-900">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              Schema Diagnostics & Intelligence
            </h1>
            <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-700 dark:bg-blue-950 dark:text-blue-300">
              Phase 8.6
            </span>
          </div>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
            <span className="flex items-center gap-1">
              <Layers className="h-3.5 w-3.5 text-slate-400" />
              <span>Workspace: <strong>{workspaceName}</strong></span>
            </span>
            <span className="flex items-center gap-1">
              <Database className="h-3.5 w-3.5 text-slate-400" />
              <span>Connection: <strong>{connectionName}</strong> ({engineName})</span>
            </span>
            <span className="flex items-center gap-1">
              <Calendar className="h-3.5 w-3.5 text-slate-400" />
              <span>
                Evaluated: <strong>{new Date(report.evaluated_at).toLocaleString()}</strong>
              </span>
            </span>
          </div>
        </div>

        {/* Snapshot Selector / Actions */}
        <SnapshotSelector
          currentSnapshotId={report.snapshot_id}
          onEvaluateLive={onReevaluate}
          isLoading={isLoading}
        />
      </div>

      {/* 2. Top-Level Summary KPI Cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-8">
        <div className="rounded-lg border border-slate-200 bg-white p-3.5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <span className="block text-[11px] font-medium text-slate-500 dark:text-slate-400">
            Total Findings
          </span>
          <span className="text-xl font-bold text-slate-900 dark:text-slate-100">
            {report.summary.total_findings}
          </span>
        </div>

        <div className="rounded-lg border border-red-200 bg-red-50/40 p-3.5 shadow-xs dark:border-red-950/60 dark:bg-red-950/20">
          <span className="block text-[11px] font-medium text-red-700 dark:text-red-400">
            Critical
          </span>
          <span className="text-xl font-bold text-red-700 dark:text-red-400">
            {report.summary.critical_findings}
          </span>
        </div>

        <div className="rounded-lg border border-amber-200 bg-amber-50/40 p-3.5 shadow-xs dark:border-amber-950/60 dark:bg-amber-950/20">
          <span className="block text-[11px] font-medium text-amber-700 dark:text-amber-400">
            High
          </span>
          <span className="text-xl font-bold text-amber-700 dark:text-amber-400">
            {report.summary.high_findings}
          </span>
        </div>

        <div className="rounded-lg border border-yellow-200 bg-yellow-50/40 p-3.5 shadow-xs dark:border-yellow-950/60 dark:bg-yellow-950/20">
          <span className="block text-[11px] font-medium text-yellow-700 dark:text-yellow-400">
            Medium
          </span>
          <span className="text-xl font-bold text-yellow-700 dark:text-yellow-400">
            {report.summary.medium_findings}
          </span>
        </div>

        <div className="rounded-lg border border-blue-200 bg-blue-50/40 p-3.5 shadow-xs dark:border-blue-950/60 dark:bg-blue-950/20">
          <span className="block text-[11px] font-medium text-blue-700 dark:text-blue-400">
            Low
          </span>
          <span className="text-xl font-bold text-blue-700 dark:text-blue-400">
            {report.summary.low_findings}
          </span>
        </div>

        <div className="rounded-lg border border-slate-200 bg-slate-50/50 p-3.5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <span className="block text-[11px] font-medium text-slate-500 dark:text-slate-400">
            Informational
          </span>
          <span className="text-xl font-bold text-slate-700 dark:text-slate-300">
            {report.summary.informational_findings}
          </span>
        </div>

        <div className="rounded-lg border border-purple-200 bg-purple-50/40 p-3.5 shadow-xs dark:border-purple-950/60 dark:bg-purple-950/20">
          <span className="block text-[11px] font-medium text-purple-700 dark:text-purple-400">
            Suppressed
          </span>
          <span className="text-xl font-bold text-purple-700 dark:text-purple-400">
            {report.summary.suppressed_findings}
          </span>
        </div>

        <div className="rounded-lg border border-emerald-200 bg-emerald-50/40 p-3.5 shadow-xs dark:border-emerald-950/60 dark:bg-emerald-950/20">
          <span className="block text-[11px] font-medium text-emerald-700 dark:text-emerald-400">
            Rules Run
          </span>
          <span className="text-xl font-bold text-emerald-700 dark:text-emerald-400">
            {report.summary.rules_evaluated}
          </span>
        </div>
      </div>

      {/* 3. Visual Summaries: Severity, Categories, and Rule Coverage */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SeveritySummary
          summary={report.summary}
          onSeverityClick={handleSeverityCardClick}
        />
        <RuleCoverage explainability={report.explainability} />
      </div>

      <CategorySummary
        findings={report.findings}
        onCategoryClick={handleCategoryCardClick}
      />

      {/* 4. Filter & Findings Explorer */}
      <div className="space-y-4">
        <FindingsFilters
          filterState={filterState}
          onFilterChange={setFilterState}
          onResetFilters={handleResetFilters}
          totalFilteredCount={filteredFindings.length}
          totalFindingsCount={report.findings.length}
        />

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          {/* Main Table: full width if no selection, or 7 cols if detail open */}
          <div className={selectedFinding ? "lg:col-span-7" : "lg:col-span-12"}>
            <FindingsExplorer
              findings={filteredFindings}
              selectedFinding={selectedFinding}
              onSelectFinding={setSelectedFinding}
            />
          </div>

          {/* Finding Detail Panel */}
          {selectedFinding && (
            <div className="lg:col-span-5">
              <FindingDetails
                finding={selectedFinding}
                onClose={() => setSelectedFinding(null)}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
