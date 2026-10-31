"use client";

/**
 * DERA — Table Inspector Main Component
 * Coordinates table header, summary stat counters, tab switches, and inspectors.
 */

import React, { useState } from "react";
import { Columns3, KeyRound, Binary, GitFork, Code2 } from "lucide-react";
import { TableMetadataHeader } from "./TableMetadataHeader";
import { TableSummaryCards } from "./TableSummaryCards";
import { ColumnsTab } from "./ColumnsTab";
import { ConstraintsTab } from "./ConstraintsTab";
import { IndexesTab } from "./IndexesTab";
import { DependenciesTab } from "./DependenciesTab";
import { RawMetadataTab } from "./RawMetadataTab";
import type { TableInspectorTab, TableInspectorViewModel } from "./types";

interface TableInspectorProps {
  viewModel: TableInspectorViewModel;
}

export function TableInspector({ viewModel }: TableInspectorProps) {
  const [activeTab, setActiveTab] = useState<TableInspectorTab>("columns");
  const { table, schemaId, sourceEngine, completeness } = viewModel;

  const tabs: Array<{ id: TableInspectorTab; label: string; icon: React.ReactNode; count?: number }> = [
    {
      id: "columns",
      label: "Columns",
      icon: <Columns3 className="w-3.5 h-3.5" />,
      count: table.columns.length,
    },
    {
      id: "constraints",
      label: "Constraints & Relations",
      icon: <KeyRound className="w-3.5 h-3.5" />,
      count:
        (table.primary_key ? 1 : 0) +
        table.foreign_keys.length +
        table.unique_constraints.length +
        table.check_constraints.length,
    },
    {
      id: "indexes",
      label: "Indexes",
      icon: <Binary className="w-3.5 h-3.5" />,
      count: table.indexes.length,
    },
    {
      id: "dependencies",
      label: "Dependencies & Cycles",
      icon: <GitFork className="w-3.5 h-3.5" />,
    },
    {
      id: "raw_metadata",
      label: "Raw JSON",
      icon: <Code2 className="w-3.5 h-3.5" />,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Table Metadata Header */}
      <TableMetadataHeader viewModel={viewModel} />

      {/* Summary Cards */}
      <TableSummaryCards table={table} activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Tab Navigation */}
      <div className="border-b border-slate-200 dark:border-slate-800">
        <nav aria-label="Table inspection sections" className="flex space-x-1 sm:space-x-4 overflow-x-auto">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 py-3 px-3 border-b-2 font-medium text-xs whitespace-nowrap transition-colors ${
                  isActive
                    ? "border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400 font-semibold"
                    : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 hover:border-slate-300"
                }`}
              >
                {tab.icon}
                <span>{tab.label}</span>
                {typeof tab.count === "number" && (
                  <span
                    className={`px-1.5 py-0.5 rounded-full text-[10px] font-mono ${
                      isActive
                        ? "bg-indigo-100 dark:bg-indigo-950/70 text-indigo-700 dark:text-indigo-300"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                    }`}
                  >
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Panels */}
      <div>
        {activeTab === "columns" && <ColumnsTab table={table} />}
        {activeTab === "constraints" && <ConstraintsTab table={table} schemaId={schemaId} />}
        {activeTab === "indexes" && <IndexesTab table={table} />}
        {activeTab === "dependencies" && <DependenciesTab table={table} schemaId={schemaId} />}
        {activeTab === "raw_metadata" && (
          <RawMetadataTab table={table} sourceEngine={sourceEngine} completeness={completeness} />
        )}
      </div>
    </div>
  );
}
