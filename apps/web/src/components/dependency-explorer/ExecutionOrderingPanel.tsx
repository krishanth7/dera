"use client";

/**
 * DERA — Topological Execution Ordering Panel
 * Displays verified Creation Order, Drop Order, and Parallel Migration Levels.
 */

import React, { useState } from "react";
import { ArrowDownUp, Layers, ArrowDown, ArrowUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { DependencyAnalysisResponse } from "@/lib/api-client";

interface ExecutionOrderingPanelProps {
  analysis: DependencyAnalysisResponse;
  onSelectTable?: (tableId: string) => void;
}

export function ExecutionOrderingPanel({
  analysis,
  onSelectTable,
}: ExecutionOrderingPanelProps) {
  const [orderingTab, setOrderingTab] = useState<"creation" | "drop" | "levels">("levels");

  return (
    <div className="space-y-6">
      {/* Sub-tab selection */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 space-x-4">
        <button
          type="button"
          onClick={() => setOrderingTab("levels")}
          className={`py-2 px-1 border-b-2 text-xs font-medium transition-colors ${
            orderingTab === "levels"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          Parallel Migration Levels ({analysis.levels.length})
        </button>
        <button
          type="button"
          onClick={() => setOrderingTab("creation")}
          className={`py-2 px-1 border-b-2 text-xs font-medium transition-colors ${
            orderingTab === "creation"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          Topological Creation Order ({analysis.creation_order.length})
        </button>
        <button
          type="button"
          onClick={() => setOrderingTab("drop")}
          className={`py-2 px-1 border-b-2 text-xs font-medium transition-colors ${
            orderingTab === "drop"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          Reverse Drop Order ({analysis.drop_order.length})
        </button>
      </div>

      {/* 1. Parallel Migration Levels */}
      {orderingTab === "levels" && (
        <div className="space-y-3">
          <p className="text-xs text-slate-500">
            Parallel migration levels represent batches of independent tables that can be populated concurrently without foreign key deadlocks.
          </p>

          <div className="space-y-3">
            {analysis.levels.map((lvl) => (
              <div
                key={lvl.level_index}
                className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm text-xs space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="font-mono text-[10px] bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800">
                      LEVEL {lvl.level_index}
                    </Badge>
                    <span className="text-slate-500 font-medium text-[11px]">
                      {lvl.table_ids.length} table{lvl.table_ids.length === 1 ? "" : "s"}
                    </span>
                  </div>
                  {lvl.level_index === 0 && (
                    <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold uppercase">
                      Independent Root Tables
                    </span>
                  )}
                </div>

                <div className="flex flex-wrap gap-1.5 pt-1">
                  {lvl.table_ids.map((tid) => (
                    <button
                      key={tid}
                      type="button"
                      onClick={() => onSelectTable?.(tid)}
                      className="px-2.5 py-1 rounded-lg bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 font-mono text-xs hover:border-indigo-500 hover:text-indigo-600 transition-colors"
                    >
                      {tid}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 2. Linear Creation Order */}
      {orderingTab === "creation" && (
        <div className="space-y-3">
          <p className="text-xs text-slate-500">
            Strict linear creation sequence ensuring all referenced parent tables exist before children are instantiated.
          </p>
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 divide-y divide-slate-100 dark:divide-slate-800 text-xs">
            {analysis.creation_order.map((tid, idx) => (
              <div
                key={tid}
                className="px-4 py-2.5 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="font-mono text-slate-400 text-[11px] w-8">
                    #{idx + 1}
                  </span>
                  <button
                    type="button"
                    onClick={() => onSelectTable?.(tid)}
                    className="font-mono font-medium text-slate-800 dark:text-slate-200 hover:text-indigo-600 hover:underline"
                  >
                    {tid}
                  </button>
                </div>
                <ArrowDown className="w-3.5 h-3.5 text-slate-400" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. Reverse Drop Order */}
      {orderingTab === "drop" && (
        <div className="space-y-3">
          <p className="text-xs text-slate-500">
            Safe teardown sequence: referencing child tables are dropped first, preventing RESTRICT or CASCADE constraint violations.
          </p>
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 divide-y divide-slate-100 dark:divide-slate-800 text-xs">
            {analysis.drop_order.map((tid, idx) => (
              <div
                key={tid}
                className="px-4 py-2.5 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="font-mono text-slate-400 text-[11px] w-8">
                    #{idx + 1}
                  </span>
                  <button
                    type="button"
                    onClick={() => onSelectTable?.(tid)}
                    className="font-mono font-medium text-slate-800 dark:text-slate-200 hover:text-indigo-600 hover:underline"
                  >
                    {tid}
                  </button>
                </div>
                <ArrowUp className="w-3.5 h-3.5 text-slate-400" />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
