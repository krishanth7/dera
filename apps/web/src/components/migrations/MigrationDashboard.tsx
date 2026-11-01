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
  workspaceId?: string;
  snapshots: SchemaSnapshotSummary[];
  initialComparison?: SchemaComparisonReport;
  initialRiskReport?: RiskAssessmentReport;
  initialPlan?: MigrationPlan;
  initialArtifact?: SqlArtifact;
  initialReview?: GovernanceReviewRequest;
  initialAuditEvents?: AuditEventRecord[];
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

import { apiClient } from "@/lib/api-client";

export function MigrationDashboard({
  workspaceId,
  snapshots,
  initialComparison,
  initialRiskReport,
  initialPlan,
  initialArtifact,
  initialReview,
  initialAuditEvents = [],
  isDemoMode = false,
}: MigrationDashboardProps) {
  const [activeTab, setActiveTab] = useState<MigrationTab>("OVERVIEW");
  const [baselineId, setBaselineId] = useState<string>(
    initialComparison?.baseline_snapshot_id || initialComparison?.source_snapshot_id || snapshots[0]?.id || ""
  );
  const [targetId, setTargetId] = useState<string>(
    initialComparison?.target_snapshot_id || snapshots[1]?.id || ""
  );
  const [isComparing, setIsComparing] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // States for sub-engines
  const [comparison, setComparison] = useState<SchemaComparisonReport | undefined>(initialComparison);
  const [riskReport, setRiskReport] = useState<RiskAssessmentReport | undefined>(initialRiskReport);
  const [plan, setPlan] = useState<MigrationPlan | undefined>(initialPlan);
  const [artifact, setArtifact] = useState<SqlArtifact | undefined>(initialArtifact);
  const [review, setReview] = useState<GovernanceReviewRequest | undefined>(initialReview);
  const [auditEvents, setAuditEvents] = useState<AuditEventRecord[]>(initialAuditEvents);

  const handleRunComparison = async () => {
    if (!baselineId || !targetId) {
      setActionError("Please select both a baseline and a target snapshot.");
      return;
    }

    if (baselineId === targetId) {
      setActionError("Baseline and target snapshots must be distinct.");
      return;
    }

    setIsComparing(true);
    setActionError(null);

    // If in demo mode without workspaceId, fallback to fixture display
    if (isDemoMode && !workspaceId) {
      setTimeout(() => {
        if (comparison) {
          setComparison({
            ...comparison,
            baseline_snapshot_id: baselineId,
            source_snapshot_id: baselineId,
            target_snapshot_id: targetId,
          });
        }
        setIsComparing(false);
        setActiveTab("COMPARE");
      }, 400);
      return;
    }

    try {
      if (!workspaceId) {
        throw new Error("No active workspace selected.");
      }

      // Step 1: Real Comparison (Phase 9.1)
      const compRes = await apiClient.compareMigrationSnapshots(workspaceId, baselineId, targetId);
      
      const normalizedComp: SchemaComparisonReport = {
        report_id: compRes.comparison_id,
        baseline_snapshot_id: compRes.baseline_snapshot_id,
        target_snapshot_id: compRes.target_snapshot_id,
        engine: compRes.engine,
        target_engine: compRes.engine,
        status: "COMPARED",
        report_fingerprint: compRes.comparison_fingerprint,
        summary: {
          total_changes: compRes.summary.total_changes,
          total_added: compRes.summary.total_added,
          total_removed: compRes.summary.total_removed,
          total_modified: compRes.summary.total_modified,
        },
        changes: compRes.changes,
      };
      setComparison(normalizedComp);

      // Step 2: Real Risk Assessment (Phase 9.2)
      const riskRes = await apiClient.assessMigrationRisk(workspaceId, compRes.comparison_id);
      const normalizedRisk: RiskAssessmentReport = {
        report_id: riskRes.report_id,
        summary: {
          total_changes: compRes.summary.total_changes,
          additive_changes: riskRes.summary.safe_change_count ?? 0,
          removals: compRes.summary.total_removed,
          modifications: compRes.summary.total_modified,
          potentially_breaking: riskRes.summary.potentially_breaking ?? 0,
          requires_review: riskRes.summary.high_count + riskRes.summary.critical_count,
          total_risks: riskRes.risks.length,
          critical_count: riskRes.summary.critical_count,
          high_count: riskRes.summary.high_count,
          medium_count: riskRes.summary.medium_count,
          low_count: riskRes.summary.low_count,
          breaking_change_count: riskRes.summary.breaking_change_count,
        },
        risk_assessments: riskRes.risks,
        report_fingerprint: riskRes.fingerprint,
      };
      setRiskReport(normalizedRisk);

      // Step 3: Real Migration Plan (Phase 9.3)
      const planRes = await apiClient.generateMigrationPlan(workspaceId, compRes.comparison_id);
      const normalizedPlan: MigrationPlan = {
        plan_id: planRes.plan_id,
        plan_status: "GENERATED",
        target_engine: planRes.engine,
        plan_fingerprint: planRes.plan_fingerprint,
        summary: {
          total_operations: planRes.summary.total_operations,
          supported_operations: planRes.summary.total_operations,
          conditional_operations: 0,
          blocked_operations: 0,
          unsupported_operations: 0,
          manual_decision_gates_count: planRes.summary.manual_decision_gates_count,
          dependency_edges_count: 0,
          stages_count: planRes.summary.total_stages,
          destructive_operations_count: 0,
        },
        operations: [],
        stages: planRes.stages.map((st: any) => ({
          stage_id: st.stage_id,
          stage_type: st.stage_type || "NORMAL",
          stage_order: st.stage_index ?? st.stage_order ?? 0,
          operation_ids: (st.operations || []).map((o: any) => o.operation_id),
          operations: st.operations || [],
          description: st.description || `Stage ${st.stage_index ?? st.stage_order ?? 0}`,
        })),
      };
      setPlan(normalizedPlan);

      // Step 4: Real SQL Compilation (Phase 9.4)
      const sqlRes = await apiClient.compileMigrationSql(workspaceId, planRes.plan_id, compRes.engine);
      const normalizedSql: SqlArtifact = {
        artifact_id: sqlRes.artifact_id,
        source_plan_id: sqlRes.plan_id,
        dialect: sqlRes.target_dialect,
        target_engine: sqlRes.target_dialect,
        status: sqlRes.validation_status,
        artifact_fingerprint: sqlRes.artifact_fingerprint,
        rendered_sql_script: sqlRes.forward_sql,
        sql_content: sqlRes.forward_sql,
        rollback_sql: sqlRes.rollback_sql,
        validation: {
          is_valid: sqlRes.validation_errors.length === 0,
          dialect_supported: true,
        },
        summary: {
          total_statements: 1,
          destructive_statements: 0,
          review_required_statements: 0,
          transaction_blocks_count: sqlRes.transactional ? 1 : 0,
          validation_issues_count: sqlRes.validation_errors.length,
        },
        statements: [
          {
            statement_id: `${sqlRes.artifact_id}-stmt-1`,
            source_operation_id: "plan-stage-1",
            source_operation_type: "MIGRATION_FORWARD",
            target_object_name: "schema",
            sql: sqlRes.forward_sql,
            dialect: sqlRes.target_dialect,
            execution_mode: "REVIEW_ONLY",
            is_destructive: false,
            requires_manual_review: true,
          },
        ],
        execution_notice: sqlRes.disclaimer,
      };
      setArtifact(normalizedSql);

      // Step 5: Real Governance Initial Submission (Phase 9.5)
      const reviewRes = await apiClient.submitMigrationReview(workspaceId, {
        artifact_id: sqlRes.artifact_id,
        title: `Schema Migration for ${currentWorkspace?.name || "Workspace"}`,
        description: `Migration plan ${planRes.plan_id} generated for comparison ${compRes.comparison_id}`,
      });
      const normalizedReview: GovernanceReviewRequest = {
        review_id: reviewRes.review_id,
        workspace_id: workspaceId,
        artifact_id: reviewRes.artifact_id,
        artifact_fingerprint: reviewRes.artifact_fingerprint,
        status: reviewRes.status,
        requester_id: reviewRes.requester_id,
        created_at: typeof reviewRes.created_at === "string" ? reviewRes.created_at : new Date(reviewRes.created_at).toISOString(),
        required_approvals: reviewRes.required_approvals,
        policy_version: "v1.0",
        decisions: [],
        safety_gate_results: [],
        audit_events: [],
        is_invalidated: false,
        export_eligibility: reviewRes.status === "APPROVED" ? "ELIGIBLE" : "INELIGIBLE",
      };
      setReview(normalizedReview);

      // Step 6: Real Audit Events
      const auditRes = await apiClient.getMigrationAuditTrail(workspaceId, reviewRes.review_id);
      setAuditEvents(auditRes.events || []);

      setActiveTab("COMPARE");
    } catch (err: any) {
      console.error("Migration pipeline execution failed:", err);
      setActionError(err.message || "Failed to execute migration engineering pipeline.");
    } finally {
      setIsComparing(false);
    }
  };

  const handleRecordDecision = async (decisionType: any, rationale: string) => {
    if (!workspaceId || !review) return;
    try {
      const res = await apiClient.recordMigrationDecision(workspaceId, review.review_id, {
        decision_type: String(decisionType),
        rationale: rationale,
      });
      setReview((prev) => prev ? {
        ...prev,
        status: res.status,
        decisions: res.decisions,
        export_eligibility: res.export_eligibility,
      } : undefined);
      // Reload audit
      const auditRes = await apiClient.getMigrationAuditTrail(workspaceId, review.review_id);
      setAuditEvents(auditRes.events);
    } catch (err: any) {
      setActionError(err.message || "Failed to record governance decision.");
    }
  };

  const criticalCount = riskReport?.summary?.critical_count ?? 0;
  const highCount = riskReport?.summary?.high_count ?? 0;
  const breakingCount = riskReport?.summary?.breaking_change_count ?? riskReport?.summary?.potentially_breaking ?? 0;
  const manualGatesCount = plan?.summary?.manual_gates_count ?? plan?.summary?.manual_decision_gates_count ?? 0;

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

      {actionError && (
        <div className="bg-red-950/80 border border-red-800 text-red-200 px-4 py-3 rounded-lg text-sm flex items-center justify-between">
          <span>{actionError}</span>
          <button
            type="button"
            onClick={() => setActionError(null)}
            className="text-red-400 hover:text-red-200 text-xs font-semibold ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

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
      {activeTab === "OVERVIEW" && comparison && riskReport && plan && review && (
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

      {activeTab === "COMPARE" && comparison && <SchemaDiffExplorer comparison={comparison} />}
      {activeTab === "RISKS" && riskReport && <RiskDetailPanel report={riskReport} />}
      {activeTab === "PLANS" && plan && <MigrationPlanViewer plan={plan} />}
      {activeTab === "SQL" && artifact && <SqlArtifactViewer artifact={artifact} />}
      {activeTab === "GOVERNANCE" && review && (
        <GovernanceReviewPanel review={review} onRecordDecision={handleRecordDecision} />
      )}
      {activeTab === "AUDIT" && review && artifact && (
        <AuditEvidencePanel events={auditEvents} review={review} artifact={artifact} />
      )}
    </div>
  );
}
