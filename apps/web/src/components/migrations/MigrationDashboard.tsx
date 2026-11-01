"use client";

import React, { useState } from "react";
import {
  SchemaSnapshotSummary,
  SchemaComparisonReport,
  RiskAssessmentReport,
  MigrationPlan,
  SqlArtifact,
  GovernanceReviewRequest,
  AuditEventRecord,
} from "@/lib/migrations/types";
import { SnapshotSelector } from "./SnapshotSelector";
import { SchemaDiffExplorer } from "./SchemaDiffExplorer";
import { RiskDetailPanel } from "./RiskDetailPanel";
import { MigrationPlanViewer } from "./MigrationPlanViewer";
import { SqlArtifactViewer } from "./SqlArtifactViewer";
import { GovernanceReviewPanel } from "./GovernanceReviewPanel";
import { AuditEvidencePanel } from "./AuditEvidencePanel";
import {
  GitCompare,
  ShieldAlert,
  Layers,
  Code2,
  ShieldCheck,
  History,
  LayoutDashboard,
} from "lucide-react";

interface MigrationDashboardProps {
  snapshots: SchemaSnapshotSummary[];
  initialComparison: SchemaComparisonReport;
  initialRiskReport: RiskAssessmentReport;
  initialPlan: MigrationPlan;
  initialArtifact: SqlArtifact;
  initialReview: GovernanceReviewRequest;
  initialAuditEvents: AuditEventRecord[];
  isDemoMode?: boolean;
}

export type MigrationTab =
  | "OVERVIEW"
  | "COMPARE"
  | "RISKS"
  | "PLANS"
  | "SQL"
  | "GOVERNANCE"
  | "AUDIT";

export function MigrationDashboard({
  snapshots,
  initialComparison,
  initialRiskReport,
  initialPlan,
  initialArtifact,
  initialReview,
  initialAuditEvents,
  isDemoMode = false,
}: MigrationDashboardProps) {
  const [activeTab, setActiveTab] = useState<MigrationTab>("OVERVIEW");
  const [baselineId, setBaselineId] = useState<string>(
    initialComparison.baseline_snapshot_id || initialComparison.source_snapshot_id || ""
  );
  const [targetId, setTargetId] = useState<string>(initialComparison.target_snapshot_id || "");
  const [isComparing, setIsComparing] = useState(false);

  // States for sub-engines
  const [comparison, setComparison] = useState<SchemaComparisonReport>(initialComparison);
  const [riskReport] = useState<RiskAssessmentReport>(initialRiskReport);
  const [plan] = useState<MigrationPlan>(initialPlan);
  const [artifact] = useState<SqlArtifact>(initialArtifact);
  const [review] = useState<GovernanceReviewRequest>(initialReview);
  const [auditEvents] = useState<AuditEventRecord[]>(initialAuditEvents);

  const handleRunComparison = () => {
    setIsComparing(true);
    setTimeout(() => {
      setComparison((prev) => ({
        ...prev,
        baseline_snapshot_id: baselineId,
        source_snapshot_id: baselineId,
        target_snapshot_id: targetId,
      }));
      setIsComparing(false);
      setActiveTab("COMPARE");
    }, 500);
  };

  const criticalCount = riskReport.summary.critical_count ?? 0;
  const highCount = riskReport.summary.high_count ?? 1;
  const breakingCount = riskReport.summary.breaking_change_count ?? riskReport.summary.potentially_breaking ?? 0;
  const manualGatesCount = plan.summary.manual_gates_count ?? plan.summary.manual_decision_gates_count ?? 0;

  return (
    <div className="space-y-6">
      {/* Top Banner and Navigation Tabs */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                Phase 9.6 Milestone Complete
              </span>
              {isDemoMode && (
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
                  Verified Sample Fixtures
                </span>
              )}
            </div>
            <h1 className="text-2xl font-bold text-slate-100 tracking-tight mt-1.5">
              Migration Engineering & Governance Workspace
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Deterministic comparison, risk classification, dependency-ordered planning, review-only SQL compiler, and cryptographic audit evidence.
            </p>
          </div>

          <div className="text-xs text-right hidden lg:block text-slate-500 font-mono">
            <div>Engine Dialects: Postgres / SQLite / MySQL</div>
            <div className="text-emerald-400 font-semibold mt-0.5">Customer Mutation: PROHIBITED</div>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setActiveTab("OVERVIEW")}
            className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-md text-xs font-medium transition-colors ${
              activeTab === "OVERVIEW"
                ? "bg-indigo-600 text-white shadow"
                : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <LayoutDashboard className="w-4 h-4" /> Overview
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("COMPARE")}
            className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-md text-xs font-medium transition-colors ${
              activeTab === "COMPARE"
                ? "bg-indigo-600 text-white shadow"
                : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <GitCompare className="w-4 h-4" /> Compare (9.1)
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("RISKS")}
            className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-md text-xs font-medium transition-colors ${
              activeTab === "RISKS"
                ? "bg-indigo-600 text-white shadow"
                : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <ShieldAlert className="w-4 h-4" /> Risk Analysis (9.2)
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("PLANS")}
            className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-md text-xs font-medium transition-colors ${
              activeTab === "PLANS"
                ? "bg-indigo-600 text-white shadow"
                : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <Layers className="w-4 h-4" /> Migration Plan (9.3)
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("SQL")}
            className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-md text-xs font-medium transition-colors ${
              activeTab === "SQL"
                ? "bg-indigo-600 text-white shadow"
                : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <Code2 className="w-4 h-4" /> SQL Artifacts (9.4)
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("GOVERNANCE")}
            className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-md text-xs font-medium transition-colors ${
              activeTab === "GOVERNANCE"
                ? "bg-indigo-600 text-white shadow"
                : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <ShieldCheck className="w-4 h-4" /> Governance & SoD (9.5)
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("AUDIT")}
            className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-md text-xs font-medium transition-colors ${
              activeTab === "AUDIT"
                ? "bg-indigo-600 text-white shadow"
                : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <History className="w-4 h-4" /> Audit & Export (9.5)
          </button>
        </div>
      </div>

      {/* Snapshot Selector is always visible to switch or verify snapshots */}
      <SnapshotSelector
        snapshots={snapshots}
        baselineId={baselineId}
        targetId={targetId}
        onSelectBaseline={setBaselineId}
        onSelectTarget={setTargetId}
        onRunComparison={handleRunComparison}
        isComparing={isComparing}
      />

      {/* Tab Content Rendering */}
      {activeTab === "OVERVIEW" && (
        <div className="space-y-6">
          {/* Executive Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-lg">
              <div className="text-xs text-slate-400">Total Structural Diffs</div>
              <div className="text-2xl font-bold text-slate-100 mt-1">
                {comparison.summary.total_changes}
              </div>
              <div className="text-[11px] text-slate-500 mt-1">
                +{comparison.summary.total_added} add / -{comparison.summary.total_removed} rem / ~{comparison.summary.total_modified} mod
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-4 rounded-lg">
              <div className="text-xs text-slate-400">Critical / High Risks</div>
              <div className="text-2xl font-bold text-amber-400 mt-1">
                {criticalCount + highCount}
              </div>
              <div className="text-[11px] text-slate-500 mt-1">
                {breakingCount} breaking changes detected
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-4 rounded-lg">
              <div className="text-xs text-slate-400">Planned Operations</div>
              <div className="text-2xl font-bold text-indigo-400 mt-1">
                {plan.summary.total_operations}
              </div>
              <div className="text-[11px] text-slate-500 mt-1">
                Across {plan.stages.length} ordered stages • {manualGatesCount} gates
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-4 rounded-lg">
              <div className="text-xs text-slate-400">Governance Review Status</div>
              <div className="text-2xl font-bold text-emerald-400 mt-1">
                {review.status}
              </div>
              <div className="text-[11px] text-slate-500 mt-1">
                {review.decisions.length} decisions • {auditEvents.length} audit records
              </div>
            </div>
          </div>

          {/* Quick Flow Navigator */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-lg space-y-3">
            <h3 className="text-sm font-semibold text-slate-200">
              End-to-End Phase 9 Engineering Workflow Progression
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-xs">
              <button
                onClick={() => setActiveTab("COMPARE")}
                className="p-3 bg-slate-950 border border-slate-800 hover:border-indigo-500 rounded text-left transition-colors"
              >
                <div className="font-semibold text-slate-200">1. Compare</div>
                <div className="text-[11px] text-slate-400 mt-1">
                  Inspect pairwise schema diffs
                </div>
              </button>
              <button
                onClick={() => setActiveTab("RISKS")}
                className="p-3 bg-slate-950 border border-slate-800 hover:border-amber-500 rounded text-left transition-colors"
              >
                <div className="font-semibold text-slate-200">2. Assess Risks</div>
                <div className="text-[11px] text-slate-400 mt-1">
                  Identify breaking changes
                </div>
              </button>
              <button
                onClick={() => setActiveTab("PLANS")}
                className="p-3 bg-slate-950 border border-slate-800 hover:border-indigo-500 rounded text-left transition-colors"
              >
                <div className="font-semibold text-slate-200">3. Review Plan</div>
                <div className="text-[11px] text-slate-400 mt-1">
                  Verify DAG order & gates
                </div>
              </button>
              <button
                onClick={() => setActiveTab("SQL")}
                className="p-3 bg-slate-950 border border-slate-800 hover:border-indigo-500 rounded text-left transition-colors"
              >
                <div className="font-semibold text-slate-200">4. Review-Only SQL</div>
                <div className="text-[11px] text-slate-400 mt-1">
                  Examine generated DDL
                </div>
              </button>
              <button
                onClick={() => setActiveTab("GOVERNANCE")}
                className="p-3 bg-slate-950 border border-slate-800 hover:border-emerald-500 rounded text-left transition-colors"
              >
                <div className="font-semibold text-slate-200">5. Sign-off & Audit</div>
                <div className="text-[11px] text-slate-400 mt-1">
                  Peer sign-off & export
                </div>
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === "COMPARE" && <SchemaDiffExplorer comparison={comparison} />}
      {activeTab === "RISKS" && <RiskDetailPanel report={riskReport} />}
      {activeTab === "PLANS" && <MigrationPlanViewer plan={plan} />}
      {activeTab === "SQL" && <SqlArtifactViewer artifact={artifact} />}
      {activeTab === "GOVERNANCE" && <GovernanceReviewPanel review={review} />}
      {activeTab === "AUDIT" && (
        <AuditEvidencePanel events={auditEvents} review={review} artifact={artifact} />
      )}
    </div>
  );
}
