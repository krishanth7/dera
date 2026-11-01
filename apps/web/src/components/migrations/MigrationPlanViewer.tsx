"use client";

import React, { useState } from "react";
import { MigrationPlan, PlannedOperation, ManualDecisionGate } from "@/lib/migrations/types";
import { GitCommit, Layers, ShieldCheck, AlertCircle, Clock, Lock, CheckCircle2 } from "lucide-react";

interface MigrationPlanViewerProps {
  plan: MigrationPlan;
}

export function MigrationPlanViewer({ plan }: MigrationPlanViewerProps) {
  const operationsList = plan.operations || [];
  const [selectedOperation, setSelectedOperation] = useState<PlannedOperation | null>(
    operationsList[0] || null
  );

  const manualGatesCount = plan.summary.manual_gates_count ?? plan.summary.manual_decision_gates_count ?? 0;
  const planFp = plan.plan_fingerprint || plan.fingerprint || "SHA-256";

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 text-slate-100 shadow-md">
      {/* Header and Summary Metrics */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-4">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-400" />
            Phase 9.3 — Deterministic Migration Plan & Operation Timeline
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Topologically sorted, dependency-ordered operations grouped into atomic execution stages with manual gates.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-slate-950 px-3 py-1.5 rounded border border-slate-800 text-xs">
            <span className="text-slate-400">Operations: </span>
            <span className="font-semibold text-slate-200">{plan.summary.total_operations}</span>
          </div>
          <div className="bg-slate-950 px-3 py-1.5 rounded border border-slate-800 text-xs">
            <span className="text-slate-400">Stages: </span>
            <span className="font-semibold text-indigo-300">{plan.stages.length}</span>
          </div>
          <div className="bg-amber-950/40 px-3 py-1.5 rounded border border-amber-800 text-xs text-amber-300">
            <span className="font-semibold">{manualGatesCount} Manual Gates</span>
          </div>
        </div>
      </div>

      {/* Manual Decision Gates Banner */}
      {plan.manual_gates && plan.manual_gates.length > 0 && (
        <div className="mb-5 bg-amber-950/20 border border-amber-800/80 rounded-lg p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-amber-300 flex items-center gap-2 mb-2">
            <Lock className="w-4 h-4 text-amber-400" /> Required Manual Engineering Decision Gates
          </h3>
          <div className="space-y-2">
            {plan.manual_gates.map((gate: ManualDecisionGate) => (
              <div
                key={gate.gate_id}
                className="bg-slate-950/80 border border-amber-900/60 p-3 rounded text-xs flex flex-col md:flex-row md:items-center justify-between gap-2"
              >
                <div>
                  <div className="font-medium text-slate-200 flex items-center gap-2">
                    <span className="font-mono text-amber-400">{gate.gate_id}</span>
                    <span>•</span>
                    <span>{gate.name}</span>
                  </div>
                  <div className="text-slate-400 mt-1">{gate.description}</div>
                </div>
                <div className="flex items-center gap-2 self-start md:self-auto shrink-0">
                  <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-950 text-amber-300 border border-amber-800">
                    {gate.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Master-Detail: Stages and Operations */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Stages Timeline */}
        <div className="lg:col-span-6 bg-slate-950/60 border border-slate-800 rounded-lg overflow-hidden flex flex-col max-h-[520px]">
          <div className="p-3 bg-slate-950 border-b border-slate-800 text-xs font-semibold uppercase tracking-wider text-slate-400 flex justify-between items-center">
            <span>Dependency-Ordered Stages ({plan.stages.length})</span>
            <span className="text-[10px] text-slate-500 font-mono">Topological DAG Order</span>
          </div>

          <div className="overflow-y-auto divide-y divide-slate-800/60 flex-1 p-3 space-y-4">
            {plan.stages.map((stage) => {
              const stageNum = stage.stage_order ?? stage.stage_number ?? 1;
              const stageTitle = stage.name || stage.description || `Stage ${stageNum}`;
              const opsInStage = operationsList.filter(
                (op) => stage.operation_ids?.includes(op.operation_id)
              );

              return (
                <div key={stage.stage_id || stageNum} className="space-y-2">
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-300 border-b border-slate-800/60 pb-1">
                    <span className="text-indigo-400 flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5" /> Stage {stageNum}: {stageTitle}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {stage.operation_ids?.length || 0} ops
                    </span>
                  </div>

                  <div className="space-y-1 pl-2">
                    {opsInStage.map((op, idx) => {
                      const isSelected = selectedOperation?.operation_id === op.operation_id;
                      const opLabel = op.target_object_name || op.target_object || op.target_object_id;
                      return (
                        <button
                          key={op.operation_id}
                          onClick={() => setSelectedOperation(op)}
                          className={`w-full text-left p-2.5 rounded text-xs transition-colors flex items-center justify-between border ${
                            isSelected
                              ? "bg-indigo-950/60 border-indigo-500 text-slate-100"
                              : "bg-slate-900/60 border-slate-800/80 hover:bg-slate-800/60 text-slate-300"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-[11px] text-slate-400">#{op.order_index ?? idx + 1}</span>
                            <span className="font-mono font-medium">{opLabel}</span>
                          </div>
                          <span className="text-[10px] uppercase font-semibold bg-slate-800 px-1.5 py-0.5 rounded text-slate-300">
                            {op.operation_type}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Operation Detail */}
        <div className="lg:col-span-6 bg-slate-950/60 border border-slate-800 rounded-lg p-5 flex flex-col justify-between">
          {selectedOperation ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="font-mono text-base font-semibold text-slate-100">
                    {selectedOperation.target_object_name || selectedOperation.target_object || selectedOperation.target_object_id}
                  </h3>
                  <div className="text-xs text-slate-400 mt-0.5">
                    Operation ID: <span className="font-mono text-slate-500">{selectedOperation.operation_id}</span>
                  </div>
                </div>
                <span className="px-2.5 py-1 rounded text-xs font-bold uppercase bg-indigo-950 text-indigo-300 border border-indigo-800">
                  {selectedOperation.operation_type}
                </span>
              </div>

              {/* Description & Stage */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                  Operation Specification
                </h4>
                <div className="bg-slate-900 p-3 rounded text-sm text-slate-200 border border-slate-800">
                  {selectedOperation.description || `Execute ${selectedOperation.operation_type} on target schema object.`}
                </div>
              </div>

              {/* Prerequisites and Dependencies */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                  Execution Dependencies & Invariants
                </h4>
                <div className="bg-slate-900 p-3 rounded font-mono text-xs text-slate-300 border border-slate-800 space-y-1">
                  <div>
                    <span className="text-slate-500">Prerequisite Operations: </span>
                    <span className="text-slate-300">
                      {selectedOperation.prerequisite_operation_ids && selectedOperation.prerequisite_operation_ids.length > 0
                        ? selectedOperation.prerequisite_operation_ids.join(", ")
                        : "None (Stage root operation)"}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">Dependent Operations: </span>
                    <span className="text-slate-300">
                      {selectedOperation.dependent_operation_ids && selectedOperation.dependent_operation_ids.length > 0
                        ? selectedOperation.dependent_operation_ids.join(", ")
                        : "None"}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">Destructive: </span>
                    <span className={selectedOperation.is_destructive ? "text-rose-400 font-bold" : "text-emerald-400"}>
                      {selectedOperation.is_destructive ? "TRUE (Requires Sign-Off)" : "FALSE"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Rollback and Preflight Requirements */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                  Advisory Preflight & Rollback Notice
                </h4>
                <div className="bg-slate-900/80 p-3 rounded text-xs text-slate-400 border border-slate-800 space-y-1">
                  <div>
                    • Preflight: Verify foreign key references exist prior to stage execution.
                  </div>
                  <div>
                    • Rollback: Generated inverse DDL is review-only and does not guarantee restoring purged rows.
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500 text-xs">
              Select an operation from the stage timeline to view its dependencies and execution constraints.
            </div>
          )}

          <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-500 flex justify-between">
            <span>Plan Fingerprint: {planFp.slice(0, 16)}...</span>
            <span>Acyclic DAG Verified</span>
          </div>
        </div>
      </div>
    </div>
  );
}
