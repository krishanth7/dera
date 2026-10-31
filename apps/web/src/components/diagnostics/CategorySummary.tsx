"use client";

import React from "react";
import { DiagnosticFinding } from "@/lib/diagnostics/types";
import { Database, Link2, GitMerge, FileText, CheckCircle2 } from "lucide-react";

interface CategorySummaryProps {
  findings: DiagnosticFinding[];
  onCategoryClick?: (category: string) => void;
  className?: string;
}

const CATEGORY_META: Record<
  string,
  { label: string; icon: React.ReactNode; description: string }
> = {
  INDEXES: {
    label: "Indexes",
    icon: <Database className="h-4 w-4 text-blue-500" />,
    description: "Duplicate, redundant, and missing secondary indexes.",
  },
  CONSTRAINTS: {
    label: "Constraints",
    icon: <CheckCircle2 className="h-4 w-4 text-emerald-500" />,
    description: "Primary key nullability, uniqueness, and check constraints.",
  },
  RELATIONSHIPS: {
    label: "Relationships",
    icon: <Link2 className="h-4 w-4 text-purple-500" />,
    description: "Foreign key integrity, composite mappings, and targets.",
  },
  DEPENDENCIES: {
    label: "Dependencies",
    icon: <GitMerge className="h-4 w-4 text-indigo-500" />,
    description: "Cycles, SCCs, depth chains, and coupling concentration.",
  },
  MAINTAINABILITY: {
    label: "Maintainability",
    icon: <FileText className="h-4 w-4 text-amber-500" />,
    description: "Table column width, naming conventions, and sprawl.",
  },
};

export function CategorySummary({
  findings,
  onCategoryClick,
  className = "",
}: CategorySummaryProps) {
  // Aggregate category counts
  const categoryCounts = findings.reduce<Record<string, number>>((acc, f) => {
    const cat = f.category || "OTHER";
    acc[cat] = (acc[cat] || 0) + 1;
    return acc;
  }, {});

  const displayedCategories = Object.keys(CATEGORY_META);

  return (
    <div
      className={`rounded-lg border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900 ${className}`}
      aria-label="Diagnostic Categories Summary"
    >
      <div className="mb-4">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
          Rule Categories
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Findings grouped by database engineering domain
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {displayedCategories.map((catKey) => {
          const meta = CATEGORY_META[catKey];
          const count = categoryCounts[catKey] || 0;

          return (
            <button
              key={catKey}
              type="button"
              onClick={() => onCategoryClick?.(catKey)}
              className="flex flex-col justify-between rounded-md border border-slate-100 bg-slate-50/50 p-3 text-left transition-colors hover:border-slate-300 hover:bg-slate-100/70 focus:outline-hidden focus:ring-2 focus:ring-blue-500 dark:border-slate-800/80 dark:bg-slate-950/40 dark:hover:border-slate-700 dark:hover:bg-slate-800/50"
              aria-label={`Filter by ${meta.label} category, ${count} findings`}
            >
              <div>
                <div className="mb-2 flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-200">
                    {meta.icon}
                    {meta.label}
                  </span>
                  <span
                    className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                      count > 0
                        ? "bg-slate-200 text-slate-800 dark:bg-slate-800 dark:text-slate-200"
                        : "bg-slate-100 text-slate-400 dark:bg-slate-900 dark:text-slate-600"
                    }`}
                  >
                    {count}
                  </span>
                </div>
                <p className="line-clamp-2 text-[11px] text-slate-500 dark:text-slate-400">
                  {meta.description}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
