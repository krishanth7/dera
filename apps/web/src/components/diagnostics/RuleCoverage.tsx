"use client";

import React from "react";
import { ReportExplainabilitySummary } from "@/lib/diagnostics/types";
import { deriveCoverageStats } from "@/lib/diagnostics/formatters";
import { ShieldAlert, Info, AlertTriangle } from "lucide-react";

interface RuleCoverageProps {
  explainability?: ReportExplainabilitySummary;
  className?: string;
}

export function RuleCoverage({ explainability, className = "" }: RuleCoverageProps) {
  const stats = deriveCoverageStats(explainability);

  return (
    <div
      className={`rounded-lg border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900 ${className}`}
      aria-label="Diagnostic Rule Coverage"
    >
      <div className="mb-4 flex flex-col justify-between gap-1 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
            Diagnostic Rule Coverage
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Accounting of registered rules executed against schema capabilities
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
            {stats.coveragePercentage}%
          </span>
          <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
            Coverage
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div
        className="mb-4 h-2.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800"
        role="progressbar"
        aria-valuenow={stats.coveragePercentage}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Diagnostic Rule Coverage Percentage"
      >
        <div
          className="h-full bg-blue-600 transition-all duration-300 dark:bg-blue-500"
          style={{ width: `${stats.coveragePercentage}%` }}
        />
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        <div className="rounded-md border border-slate-100 bg-slate-50/50 p-2.5 dark:border-slate-800 dark:bg-slate-950/40">
          <span className="block text-[11px] font-medium text-slate-500 dark:text-slate-400">
            Registered Rules
          </span>
          <span className="text-lg font-bold text-slate-900 dark:text-slate-100">
            {stats.totalRegistered}
          </span>
        </div>

        <div className="rounded-md border border-slate-100 bg-slate-50/50 p-2.5 dark:border-slate-800 dark:bg-slate-950/40">
          <span className="block text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
            Evaluated
          </span>
          <span className="text-lg font-bold text-slate-900 dark:text-slate-100">
            {stats.evaluated}
          </span>
        </div>

        <div className="rounded-md border border-slate-100 bg-slate-50/50 p-2.5 dark:border-slate-800 dark:bg-slate-950/40">
          <span className="block text-[11px] font-medium text-amber-600 dark:text-amber-400">
            Skipped
          </span>
          <span className="text-lg font-bold text-slate-900 dark:text-slate-100">
            {stats.skipped}
          </span>
        </div>

        <div className="rounded-md border border-slate-100 bg-slate-50/50 p-2.5 dark:border-slate-800 dark:bg-slate-950/40">
          <span className="block text-[11px] font-medium text-purple-600 dark:text-purple-400">
            Unsupported
          </span>
          <span className="text-lg font-bold text-slate-900 dark:text-slate-100">
            {stats.unsupported}
          </span>
        </div>

        <div className="rounded-md border border-slate-100 bg-slate-50/50 p-2.5 dark:border-slate-800 dark:bg-slate-950/40">
          <span className="block text-[11px] font-medium text-orange-600 dark:text-orange-400">
            Partial Metadata
          </span>
          <span className="text-lg font-bold text-slate-900 dark:text-slate-100">
            {stats.insufficientMetadata}
          </span>
        </div>
      </div>

      {/* Coverage Limitations Callout (Adhering to Section 16-17) */}
      <div className="mt-4 flex items-start gap-2 rounded-md border border-blue-100 bg-blue-50/60 p-3 text-[12px] text-blue-900 dark:border-blue-900/50 dark:bg-blue-950/30 dark:text-blue-200">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-blue-600 dark:text-blue-400" />
        <div>
          <span className="font-semibold">Coverage Formula & Operational Scope: </span>
          <span>
            Coverage represents <code>(Evaluated Rules / Total Applicable Rules) × 100</code>.
            Rule coverage measures diagnostic inspection completeness and does not reflect database runtime performance, storage health, or application defect absence.
          </span>
        </div>
      </div>
    </div>
  );
}
