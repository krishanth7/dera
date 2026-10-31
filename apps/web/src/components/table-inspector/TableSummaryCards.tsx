"use client";

/**
 * DERA — Table Inspector Summary Cards
 * Quick stat counters with click-to-tab navigation.
 */

import React from "react";
import { Columns3, KeyRound, Link2, Fingerprint, ShieldAlert, Binary } from "lucide-react";
import type { TableDetailItem } from "@/lib/api-client";
import type { TableInspectorTab } from "./types";

interface TableSummaryCardsProps {
  table: TableDetailItem;
  activeTab: TableInspectorTab;
  onTabChange: (tab: TableInspectorTab) => void;
}

export function TableSummaryCards({ table, activeTab, onTabChange }: TableSummaryCardsProps) {
  const pkColCount = table.primary_key?.columns.length || 0;
  const isCompositePk = pkColCount > 1;

  const cards = [
    {
      tab: "columns" as TableInspectorTab,
      label: "Columns",
      count: table.columns.length,
      detail: `${table.columns.filter((c) => !c.is_nullable).length} NOT NULL`,
      icon: <Columns3 className="w-4 h-4 text-indigo-500" />,
    },
    {
      tab: "constraints" as TableInspectorTab,
      label: "Primary Key",
      count: pkColCount,
      detail: isCompositePk ? `Composite (${pkColCount} cols)` : pkColCount === 1 ? "Single column" : "No PK defined",
      icon: <KeyRound className="w-4 h-4 text-amber-500" />,
    },
    {
      tab: "constraints" as TableInspectorTab,
      label: "Foreign Keys",
      count: table.foreign_keys.length,
      detail: `${table.foreign_keys.length} referenced tables`,
      icon: <Link2 className="w-4 h-4 text-blue-500" />,
    },
    {
      tab: "constraints" as TableInspectorTab,
      label: "Unique Constraints",
      count: table.unique_constraints.length,
      detail: "Unique definitions",
      icon: <Fingerprint className="w-4 h-4 text-teal-500" />,
    },
    {
      tab: "constraints" as TableInspectorTab,
      label: "Check Constraints",
      count: table.check_constraints.length,
      detail: "Validation expressions",
      icon: <ShieldAlert className="w-4 h-4 text-rose-500" />,
    },
    {
      tab: "indexes" as TableInspectorTab,
      label: "Indexes",
      count: table.indexes.length,
      detail: `${table.indexes.filter((i) => i.is_unique).length} unique indexes`,
      icon: <Binary className="w-4 h-4 text-violet-500" />,
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {cards.map((c) => {
        const isSelected = activeTab === c.tab;
        return (
          <button
            key={c.label}
            type="button"
            onClick={() => onTabChange(c.tab)}
            className={`p-3 rounded-xl border text-left transition-all ${
              isSelected
                ? "bg-slate-100 dark:bg-slate-800/90 border-indigo-500 shadow-sm ring-1 ring-indigo-500/20"
                : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700"
            }`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                {c.label}
              </span>
              {c.icon}
            </div>
            <div className="text-xl font-bold font-mono text-slate-900 dark:text-slate-100">
              {c.count}
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate mt-0.5">
              {c.detail}
            </p>
          </button>
        );
      })}
    </div>
  );
}
