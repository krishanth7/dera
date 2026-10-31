"use client";

/**
 * DERA — Dependency Explorer Summary Banner
 * Displays topological counts, cycle status, SCC partitions, and parallel level counts.
 */

import React from "react";
import { GitFork, AlertTriangle, CheckCircle, Network, Layers, ArrowDownUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { DependencyAnalysisResponse } from "@/lib/api-client";
import type { DependencyExplorerView } from "./types";

interface DependencySummaryBannerProps {
  analysis: DependencyAnalysisResponse;
  activeView: DependencyExplorerView;
  onViewChange: (view: DependencyExplorerView) => void;
}

export function DependencySummaryBanner({
  analysis,
  activeView,
  onViewChange,
}: DependencySummaryBannerProps) {
  const cards = [
    {
      view: "summary" as DependencyExplorerView,
      label: "Total Tables",
      value: analysis.total_tables,
      detail: "Canonical entities",
      icon: <Layers className="w-4 h-4 text-indigo-500" />,
    },
    {
      view: "summary" as DependencyExplorerView,
      label: "Dependency Edges",
      value: analysis.total_edges,
      detail: "Verified foreign keys",
      icon: <Network className="w-4 h-4 text-blue-500" />,
    },
    {
      view: "cycles" as DependencyExplorerView,
      label: "Circular Cycles",
      value: analysis.cycle_count,
      detail: analysis.has_cycles ? `${analysis.cyclic_scc_count} cyclic SCCs` : "Acyclic DAG",
      icon: analysis.has_cycles ? (
        <AlertTriangle className="w-4 h-4 text-rose-500" />
      ) : (
        <CheckCircle className="w-4 h-4 text-emerald-500" />
      ),
      highlight: analysis.has_cycles ? "danger" : "success",
    },
    {
      view: "cycles" as DependencyExplorerView,
      label: "Strongly Connected",
      value: analysis.scc_count,
      detail: `${analysis.cyclic_scc_count} cyclic groups`,
      icon: <GitFork className="w-4 h-4 text-teal-500" />,
    },
    {
      view: "ordering" as DependencyExplorerView,
      label: "Parallel Levels",
      value: analysis.levels.length,
      detail: "Migration batches",
      icon: <ArrowDownUp className="w-4 h-4 text-violet-500" />,
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {cards.map((c) => {
        const isSelected = activeView === c.view;

        return (
          <button
            key={c.label}
            type="button"
            onClick={() => onViewChange(c.view)}
            className={`p-3 rounded-xl border text-left transition-all ${
              isSelected
                ? "bg-slate-100 dark:bg-slate-800/90 border-indigo-500 ring-1 ring-indigo-500/20"
                : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700"
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
                {c.label}
              </span>
              {c.icon}
            </div>
            <div className="text-xl font-bold font-mono text-slate-900 dark:text-slate-100">
              {c.value}
            </div>
            <div className="text-[11px] text-slate-500 truncate mt-0.5">
              {c.detail}
            </div>
          </button>
        );
      })}
    </div>
  );
}
