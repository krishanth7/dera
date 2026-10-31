"use client";

import React from "react";
import { DiagnosticSeverity, DiagnosticSummary } from "@/lib/diagnostics/types";
import { SeverityBadge } from "./SeverityBadge";

interface SeveritySummaryProps {
  summary: DiagnosticSummary;
  onSeverityClick?: (severity: DiagnosticSeverity) => void;
  className?: string;
}

const SEVERITY_CONFIG: Array<{
  key: keyof Pick<
    DiagnosticSummary,
    | "critical_findings"
    | "high_findings"
    | "medium_findings"
    | "low_findings"
    | "informational_findings"
  >;
  severity: DiagnosticSeverity;
  colorClass: string;
  barClass: string;
}> = [
  {
    key: "critical_findings",
    severity: "CRITICAL",
    colorClass: "text-red-700 dark:text-red-400",
    barClass: "bg-red-600 dark:bg-red-500",
  },
  {
    key: "high_findings",
    severity: "HIGH",
    colorClass: "text-amber-700 dark:text-amber-400",
    barClass: "bg-amber-600 dark:bg-amber-500",
  },
  {
    key: "medium_findings",
    severity: "MEDIUM",
    colorClass: "text-yellow-700 dark:text-yellow-400",
    barClass: "bg-yellow-500 dark:bg-yellow-400",
  },
  {
    key: "low_findings",
    severity: "LOW",
    colorClass: "text-blue-700 dark:text-blue-400",
    barClass: "bg-blue-600 dark:bg-blue-400",
  },
  {
    key: "informational_findings",
    severity: "INFORMATIONAL",
    colorClass: "text-slate-700 dark:text-slate-300",
    barClass: "bg-slate-500 dark:bg-slate-400",
  },
];

export function SeveritySummary({
  summary,
  onSeverityClick,
  className = "",
}: SeveritySummaryProps) {
  const total = summary.total_findings;

  return (
    <div
      className={`rounded-lg border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900 ${className}`}
      aria-label="Severity Distribution Summary"
    >
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
            Severity Distribution
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {total} total finding{total === 1 ? "" : "s"} across all evaluated rules
          </p>
        </div>
      </div>

      {/* Accessible visual bar with non-color fallback text */}
      <div
        className="mb-6 flex h-4 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800"
        role="progressbar"
        aria-valuenow={total}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-label="Findings breakdown by severity"
      >
        {SEVERITY_CONFIG.map(({ key, severity, barClass }) => {
          const count = summary[key] || 0;
          if (count === 0 || total === 0) return null;
          const pct = Math.round((count / total) * 100);

          return (
            <div
              key={severity}
              style={{ width: `${pct}%` }}
              className={`${barClass} transition-all duration-300`}
              title={`${severity}: ${count} (${pct}%)`}
            />
          );
        })}
      </div>

      {/* Grid of severity counts */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {SEVERITY_CONFIG.map(({ key, severity }) => {
          const count = summary[key] || 0;
          const pct = total > 0 ? Math.round((count / total) * 100) : 0;

          return (
            <button
              key={severity}
              type="button"
              onClick={() => onSeverityClick?.(severity)}
              className="flex flex-col rounded-md border border-slate-100 bg-slate-50/50 p-3 text-left transition-colors hover:border-slate-300 hover:bg-slate-100/70 focus:outline-hidden focus:ring-2 focus:ring-blue-500 dark:border-slate-800/80 dark:bg-slate-950/40 dark:hover:border-slate-700 dark:hover:bg-slate-800/50"
              aria-label={`Filter by ${severity} severity, currently ${count} findings`}
            >
              <div className="mb-2">
                <SeverityBadge severity={severity} />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
                  {count}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  {pct}%
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Accessible data table for screen-readers (WCAG 2.2 AA) */}
      <table className="sr-only">
        <caption>Diagnostic Findings by Severity</caption>
        <thead>
          <tr>
            <th scope="col">Severity</th>
            <th scope="col">Count</th>
            <th scope="col">Percentage</th>
          </tr>
        </thead>
        <tbody>
          {SEVERITY_CONFIG.map(({ key, severity }) => {
            const count = summary[key] || 0;
            const pct = total > 0 ? Math.round((count / total) * 100) : 0;
            return (
              <tr key={severity}>
                <td>{severity}</td>
                <td>{count}</td>
                <td>{pct}%</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
