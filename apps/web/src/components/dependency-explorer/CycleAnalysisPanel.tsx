"use client";

/**
 * DERA — Cycle Analysis & Strongly Connected Components Panel
 * Displays elementary cycles (Tarjan & Johnson algorithms), breakability strategies,
 * and SCC partitions.
 */

import React from "react";
import Link from "next/link";
import {
  AlertTriangle,
  CheckCircle,
  RotateCw,
  GitFork,
  ExternalLink,
  ShieldCheck,
  Info,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { CycleReportResponse } from "@/lib/api-client";

interface CycleAnalysisPanelProps {
  cycleReport: CycleReportResponse;
  schemaId: string;
  onSelectTable?: (tableId: string) => void;
}

export function CycleAnalysisPanel({
  cycleReport,
  schemaId,
  onSelectTable,
}: CycleAnalysisPanelProps) {
  const { has_cycles, cycle_count, cyclic_scc_count, cycles, components } = cycleReport;

  const cyclicSCCs = components.filter((c) => c.is_cyclic);
  const acyclicSCCs = components.filter((c) => !c.is_cyclic);

  return (
    <div className="space-y-6">
      {/* Overview Banner */}
      <div
        className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
          has_cycles
            ? "border-amber-500/30 bg-amber-500/10 text-amber-900 dark:text-amber-200"
            : "border-emerald-500/30 bg-emerald-500/10 text-emerald-900 dark:text-emerald-200"
        }`}
      >
        <div className="flex items-center gap-3">
          {has_cycles ? (
            <div className="p-2 rounded-lg bg-amber-500/20 text-amber-600 dark:text-amber-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
          ) : (
            <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">
              <CheckCircle className="w-5 h-5" />
            </div>
          )}
          <div>
            <h3 className="text-sm font-bold">
              {has_cycles
                ? `${cycle_count} Circular Dependency Cycle${cycle_count === 1 ? "" : "s"} Detected`
                : "No Circular Dependency Cycles Discovered"}
            </h3>
            <p className="text-xs opacity-90 mt-0.5">
              {has_cycles
                ? `${cyclic_scc_count} strongly connected component${
                    cyclic_scc_count === 1 ? "" : "s"
                  } contain mutual or cyclic foreign keys.`
                : "The schema relationship graph is a Directed Acyclic Graph (DAG). Execution orderings are completely deterministic."}
            </p>
          </div>
        </div>

        <div className="text-xs font-mono font-medium self-end sm:self-center">
          Algorithm: Tarjan SCC & Johnson Cycle Enumeration
        </div>
      </div>

      {/* Elementary Cycles Section */}
      {has_cycles && cycles.length > 0 && (
        <section aria-labelledby="cycles-heading" className="space-y-3">
          <div className="flex items-center gap-2">
            <RotateCw className="w-4 h-4 text-amber-500" />
            <h3 id="cycles-heading" className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              Elementary Dependency Cycles ({cycles.length})
            </h3>
          </div>

          <div className="grid grid-cols-1 gap-3">
            {cycles.map((c) => (
              <div
                key={c.cycle_id}
                className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm text-xs space-y-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-slate-900 dark:text-slate-100">
                      {c.cycle_id}
                    </span>
                    <Badge variant="outline" className="text-[10px] uppercase font-mono">
                      {c.cycle_kind}
                    </Badge>
                    <Badge variant="secondary" className="text-[10px]">
                      Length: {c.length}
                    </Badge>
                  </div>
                  {c.breakability_strategy && (
                    <Badge variant="outline" className="text-[10px] text-indigo-600 dark:text-indigo-400 border-indigo-500/30">
                      Strategy: {c.breakability_strategy}
                    </Badge>
                  )}
                </div>

                {/* Table sequence loop */}
                <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 space-y-1">
                  <span className="text-[11px] text-slate-500 uppercase font-medium block">
                    Circular Table Sequence:
                  </span>
                  <div className="flex flex-wrap items-center gap-1.5 font-mono text-xs">
                    {c.table_ids.map((tid, idx) => (
                      <React.Fragment key={`${c.cycle_id}-${tid}-${idx}`}>
                        <button
                          type="button"
                          onClick={() => onSelectTable?.(tid)}
                          className="px-2 py-0.5 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-indigo-600 dark:text-indigo-400 hover:underline font-medium"
                        >
                          {tid}
                        </button>
                        <span className="text-slate-400">&rarr;</span>
                      </React.Fragment>
                    ))}
                    <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-700 dark:text-amber-300 font-semibold">
                      {c.table_ids[0]}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Strongly Connected Components (SCCs) */}
      <section aria-labelledby="scc-heading" className="space-y-3">
        <div className="flex items-center gap-2">
          <GitFork className="w-4 h-4 text-indigo-500" />
          <h3 id="scc-heading" className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            Strongly Connected Components ({components.length})
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {components.map((scc) => (
            <div
              key={scc.scc_id}
              className={`p-3.5 rounded-xl border text-xs space-y-2 ${
                scc.is_cyclic
                  ? "border-amber-500/40 bg-amber-500/5 dark:bg-amber-950/10"
                  : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-slate-900 dark:text-slate-100">
                  {scc.scc_id}
                </span>
                <Badge
                  variant={scc.is_cyclic ? "destructive" : "secondary"}
                  className="text-[10px] uppercase font-mono"
                >
                  {scc.is_cyclic ? "Cyclic SCC" : "Acyclic Component"}
                </Badge>
              </div>

              <div className="text-slate-600 dark:text-slate-400 space-y-1">
                <span className="text-[11px] text-slate-500 block">
                  Member Tables ({scc.size}):
                </span>
                <div className="flex flex-wrap gap-1 font-mono text-[11px]">
                  {scc.table_ids.map((tid) => (
                    <button
                      key={tid}
                      type="button"
                      onClick={() => onSelectTable?.(tid)}
                      className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:text-indigo-600 hover:underline"
                    >
                      {tid}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Guidance Alert */}
      <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 text-xs text-slate-600 dark:text-slate-400 space-y-2">
        <div className="flex items-center gap-1.5 font-semibold text-slate-800 dark:text-slate-200">
          <Info className="w-4 h-4 text-indigo-500" />
          <span>Understanding Database Cycles & Resolution</span>
        </div>
        <p className="leading-relaxed">
          Circular dependencies in relational databases occur when table A references table B, and table B references table A (or through an indirect chain). When restoring backups or executing migrations, mutually dependent tables cannot be created in pure linear order unless foreign key constraints are either created <em>after</em> tables or configured with <code className="font-mono text-indigo-500">DEFERRABLE INITIALLY DEFERRED</code> semantics.
        </p>
      </div>
    </div>
  );
}
