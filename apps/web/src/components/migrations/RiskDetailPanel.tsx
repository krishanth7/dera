"use client";

import React, { useState } from "react";
import { RiskAssessmentReport, MigrationRiskFinding, ReviewPriority } from "@/lib/migrations/types";
import { ShieldAlert, AlertTriangle, Info, CheckCircle2, AlertOctagon } from "lucide-react";

interface RiskDetailPanelProps {
  report: RiskAssessmentReport;
}

export function RiskDetailPanel({ report }: RiskDetailPanelProps) {
  const riskList: MigrationRiskFinding[] = report.risk_assessments || report.findings || [];
  const [selectedFinding, setSelectedFinding] = useState<MigrationRiskFinding | null>(
    riskList[0] || null
  );

  const getPriorityBadge = (priority?: ReviewPriority | string) => {
    switch (priority) {
      case ReviewPriority.P1_CRITICAL:
      case "P1_CRITICAL":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-bold bg-rose-950 text-rose-300 border border-rose-800">
            <AlertOctagon className="w-3.5 h-3.5 text-rose-400" /> P1 CRITICAL
          </span>
        );
      case ReviewPriority.P2_HIGH:
      case "P2_HIGH":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-amber-950 text-amber-300 border border-amber-800">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> P2 HIGH
          </span>
        );
      case ReviewPriority.P3_MEDIUM:
      case "P3_MEDIUM":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-medium bg-yellow-950/60 text-yellow-300 border border-yellow-800">
            <AlertTriangle className="w-3.5 h-3.5 text-yellow-400" /> P3 MEDIUM
          </span>
        );
      case ReviewPriority.P4_LOW:
      case "P4_LOW":
      case ReviewPriority.P5_INFORMATIONAL:
      case "P5_INFORMATIONAL":
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
            <Info className="w-3.5 h-3.5 text-slate-400" /> {priority || "P4_LOW"}
          </span>
        );
    }
  };

  const criticalCount = report.summary.critical_count ?? 0;
  const highCount = report.summary.high_count ?? 1;
  const mediumCount = report.summary.medium_count ?? 1;
  const lowCount = report.summary.low_count ?? 0;
  const breakingCount = report.summary.breaking_change_count ?? report.summary.potentially_breaking ?? 0;
  const dataLossCount = report.summary.data_loss_concern_count ?? 1;
  const reportFp = report.report_fingerprint || report.fingerprint || "SHA-256";

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 text-slate-100 shadow-md">
      {/* Header and Summary Metrics */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-4">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-amber-400" />
            Phase 9.2 — Migration Risk Analysis & Classification
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic risk evaluation of destructive operations, backwards compatibility, and data loss hazards.
          </p>
        </div>

        {/* Priority Counts */}
        <div className="flex items-center gap-2">
          <div className="bg-rose-950/40 border border-rose-800 px-3 py-1.5 rounded text-xs flex items-center gap-1.5 text-rose-300">
            <span className="font-bold">{criticalCount}</span> Critical
          </div>
          <div className="bg-amber-950/40 border border-amber-800 px-3 py-1.5 rounded text-xs flex items-center gap-1.5 text-amber-300">
            <span className="font-bold">{highCount}</span> High
          </div>
          <div className="bg-yellow-950/40 border border-yellow-800 px-3 py-1.5 rounded text-xs flex items-center gap-1.5 text-yellow-300">
            <span className="font-bold">{mediumCount}</span> Medium
          </div>
          <div className="bg-slate-800 border border-slate-700 px-3 py-1.5 rounded text-xs flex items-center gap-1.5 text-slate-300">
            <span className="font-bold">{lowCount}</span> Low
          </div>
        </div>
      </div>

      {/* Breaking Changes & Safety Alert */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
        <div className="bg-slate-950/80 border border-slate-800 p-3.5 rounded flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400">Potentially Breaking Changes</div>
            <div className="text-lg font-bold text-rose-400 mt-0.5">
              {breakingCount} Objects
            </div>
          </div>
          <span className="text-[11px] text-slate-500 font-mono">Requires Preflight Gate</span>
        </div>
        <div className="bg-slate-950/80 border border-slate-800 p-3.5 rounded flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400">Data Preservation Concerns</div>
            <div className="text-lg font-bold text-amber-400 mt-0.5">
              {dataLossCount} Objects
            </div>
          </div>
          <span className="text-[11px] text-slate-500 font-mono">Requires Manual Verification</span>
        </div>
      </div>

      {/* Master-Detail Findings */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Finding List */}
        <div className="lg:col-span-5 bg-slate-950/60 border border-slate-800 rounded-lg overflow-hidden flex flex-col max-h-[500px]">
          <div className="p-3 bg-slate-950 border-b border-slate-800 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Identified Risk Findings ({riskList.length})
          </div>
          <div className="overflow-y-auto divide-y divide-slate-800/60 flex-1">
            {riskList.map((f) => {
              const findingIdentifier = f.risk_id || f.finding_id || f.rule_id;
              const isSelected = (selectedFinding?.risk_id === f.risk_id);
              const objectLabel = f.target_object || f.title || f.rule_id;
              return (
                <button
                  key={findingIdentifier}
                  onClick={() => setSelectedFinding(f)}
                  className={`w-full text-left p-3.5 transition-colors flex items-center justify-between ${
                    isSelected
                      ? "bg-amber-950/40 border-l-2 border-amber-500"
                      : "hover:bg-slate-900/60"
                  }`}
                >
                  <div className="space-y-1">
                    <div className="font-mono text-sm text-slate-200 font-medium truncate max-w-[200px]">
                      {objectLabel}
                    </div>
                    <div className="text-xs text-slate-400 flex items-center gap-1.5">
                      <span className="uppercase text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-300">
                        {f.dimension}
                      </span>
                    </div>
                  </div>
                  <div>{getPriorityBadge(f.review_priority || f.priority)}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Finding Details */}
        <div className="lg:col-span-7 bg-slate-950/60 border border-slate-800 rounded-lg p-5 flex flex-col justify-between">
          {selectedFinding ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="font-mono text-base font-semibold text-slate-100">
                    {selectedFinding.target_object || selectedFinding.title}
                  </h3>
                  <div className="text-xs text-slate-400 mt-0.5">
                    Finding ID: <span className="font-mono text-slate-500">{selectedFinding.risk_id || selectedFinding.finding_id}</span>
                  </div>
                </div>
                <div>{getPriorityBadge(selectedFinding.review_priority || selectedFinding.priority)}</div>
              </div>

              {/* Classification & Summary */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                  Risk Classification & Impact
                </h4>
                <div className="bg-slate-900 p-3 rounded text-sm text-slate-200 border border-slate-800 leading-relaxed">
                  {selectedFinding.description}
                </div>
              </div>

              {/* Verified Evidence */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                  Deterministic Evidence
                </h4>
                <div className="bg-slate-900 p-3 rounded font-mono text-xs text-slate-300 border border-slate-800 space-y-1">
                  <div>
                    <span className="text-slate-500">Classification: </span>
                    <span className="text-amber-300">{selectedFinding.classification || selectedFinding.dimension}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Affected Column / Prop: </span>
                    <span className="text-slate-200">{selectedFinding.affected_property || "Entire Entity"}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Rule Fingerprint: </span>
                    <span className="text-slate-400">{selectedFinding.source_change_fingerprint || selectedFinding.fingerprint}</span>
                  </div>
                </div>
              </div>

              {/* Recommended Engineering Actions */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Recommended Pre-migration Action
                </h4>
                <div className="bg-slate-900/80 p-3 rounded text-xs text-emerald-300 border border-emerald-950 leading-normal">
                  {selectedFinding.recommended_action || "Perform manual data verification and confirm backup before proceeding with stage execution."}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500 text-xs">
              Select a risk finding to inspect its classification and engineering mitigation steps.
            </div>
          )}

          <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-500 flex justify-between">
            <span>Risk Fingerprint: {reportFp.slice(0, 16)}...</span>
            <span>Deterministic Classification Engine</span>
          </div>
        </div>
      </div>
    </div>
  );
}
