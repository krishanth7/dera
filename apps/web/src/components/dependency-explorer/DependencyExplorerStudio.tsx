"use client";

/**
 * DERA — Dependency Explorer Studio
 * Unified dependency analysis studio coordinating reachability, cycle detection,
 * execution ordering, and accessible tabular inspection.
 */

import React, { useState } from "react";
import Link from "next/link";
import {
  GitFork,
  RotateCw,
  ArrowDownUp,
  TableProperties,
  Network,
  ArrowLeft,
  ExternalLink,
  Layers,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { DependencySummaryBanner } from "./DependencySummaryBanner";
import { TransitiveReachabilityPanel } from "./TransitiveReachabilityPanel";
import { CycleAnalysisPanel } from "./CycleAnalysisPanel";
import { ExecutionOrderingPanel } from "./ExecutionOrderingPanel";
import { AccessibleDependencyTable } from "./AccessibleDependencyTable";
import type { DependencyExplorerViewModel, DependencyExplorerView } from "./types";

interface DependencyExplorerStudioProps {
  viewModel: DependencyExplorerViewModel;
}

export function DependencyExplorerStudio({ viewModel }: DependencyExplorerStudioProps) {
  const { schemaId, databaseName, sourceEngine, analysis, cycles, relationships, initialTableId } =
    viewModel;

  const [activeView, setActiveView] = useState<DependencyExplorerView>("reachability");
  const [selectedTableId, setSelectedTableId] = useState<string>(
    initialTableId || relationships.nodes[0]?.table_id || ""
  );

  const views: Array<{ id: DependencyExplorerView; label: string; icon: React.ReactNode }> = [
    {
      id: "reachability",
      label: "Reachability & Blast Radius",
      icon: <GitFork className="w-3.5 h-3.5" />,
    },
    {
      id: "cycles",
      label: `Cycles & SCCs (${analysis.cycle_count})`,
      icon: <RotateCw className="w-3.5 h-3.5" />,
    },
    {
      id: "ordering",
      label: "Topological Orderings",
      icon: <ArrowDownUp className="w-3.5 h-3.5" />,
    },
    {
      id: "accessible_table",
      label: "Accessible Table View",
      icon: <TableProperties className="w-3.5 h-3.5" />,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Studio Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <GitFork className="w-5 h-5 text-indigo-500" />
              Dependency Analysis & Cycle Detection
            </h1>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Topological table orderings, reachability traversal, strongly connected components, and circular dependency resolution.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {selectedTableId && (
            <Link
              href={`/tables/${encodeURIComponent(selectedTableId)}?schemaId=${encodeURIComponent(schemaId)}`}
            >
              <Button variant="outline" size="sm" className="gap-1.5 text-xs">
                Inspect Focused Table
                <ExternalLink className="w-3.5 h-3.5" />
              </Button>
            </Link>
          )}
          <Link
            href={`/relationships?schemaId=${encodeURIComponent(schemaId)}&selectedTableId=${encodeURIComponent(selectedTableId)}`}
          >
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <Network className="w-3.5 h-3.5 text-indigo-500" />
              Open in ER Canvas
            </Button>
          </Link>
          <Link href={`/schemas/${encodeURIComponent(schemaId)}`}>
            <Button variant="ghost" size="sm" className="gap-1.5 text-xs">
              <ArrowLeft className="w-3.5 h-3.5" />
              Schema Explorer
            </Button>
          </Link>
        </div>
      </div>

      {/* Metrics Banner */}
      <DependencySummaryBanner
        analysis={analysis}
        activeView={activeView}
        onViewChange={setActiveView}
      />

      {/* View Switcher Tabs */}
      <div className="border-b border-slate-200 dark:border-slate-800">
        <nav aria-label="Dependency views" className="flex space-x-1 sm:space-x-4 overflow-x-auto">
          {views.map((v) => {
            const isActive = activeView === v.id;
            return (
              <button
                key={v.id}
                type="button"
                onClick={() => setActiveView(v.id)}
                className={`flex items-center gap-2 py-3 px-3 border-b-2 font-medium text-xs whitespace-nowrap transition-colors ${
                  isActive
                    ? "border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400 font-semibold"
                    : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 hover:border-slate-300"
                }`}
              >
                {v.icon}
                <span>{v.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* View Panels */}
      <div>
        {activeView === "reachability" && (
          <TransitiveReachabilityPanel
            relationships={relationships}
            schemaId={schemaId}
            selectedTableId={selectedTableId}
            onSelectTable={setSelectedTableId}
          />
        )}
        {activeView === "cycles" && (
          <CycleAnalysisPanel
            cycleReport={cycles}
            schemaId={schemaId}
            onSelectTable={setSelectedTableId}
          />
        )}
        {activeView === "ordering" && (
          <ExecutionOrderingPanel
            analysis={analysis}
            onSelectTable={setSelectedTableId}
          />
        )}
        {activeView === "accessible_table" && (
          <AccessibleDependencyTable
            analysis={analysis}
            relationships={relationships}
            cycles={cycles}
            schemaId={schemaId}
            onSelectTable={setSelectedTableId}
          />
        )}
      </div>
    </div>
  );
}
