"use client";

import React, { useState } from "react";
import { DiagnosticFinding } from "@/lib/diagnostics/types";
import { SeverityBadge } from "./SeverityBadge";
import { ClassificationBadge } from "./ClassificationBadge";
import {
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  ArrowRight,
  Eye,
  CheckCircle,
} from "lucide-react";

interface FindingsExplorerProps {
  findings: DiagnosticFinding[];
  selectedFinding: DiagnosticFinding | null;
  onSelectFinding: (finding: DiagnosticFinding) => void;
  pageSize?: number;
  className?: string;
}

export function FindingsExplorer({
  findings,
  selectedFinding,
  onSelectFinding,
  pageSize = 10,
  className = "",
}: FindingsExplorerProps) {
  const [currentPage, setCurrentPage] = useState(1);

  const totalPages = Math.max(1, Math.ceil(findings.length / pageSize));
  const safePage = Math.min(currentPage, totalPages);
  const startIndex = (safePage - 1) * pageSize;
  const pageFindings = findings.slice(startIndex, startIndex + pageSize);

  const handlePrevPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  if (findings.length === 0) {
    return (
      <div
        className={`flex flex-col items-center justify-center rounded-lg border border-slate-200 bg-white p-12 text-center shadow-xs dark:border-slate-800 dark:bg-slate-900 ${className}`}
        aria-label="No findings found"
      >
        <CheckCircle className="mb-3 h-10 w-10 text-emerald-500" />
        <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
          No Diagnostic Findings
        </h3>
        <p className="mt-1 max-w-sm text-xs text-slate-500 dark:text-slate-400">
          No findings match the current filter criteria, or the evaluated schema satisfies all checked rules.
        </p>
      </div>
    );
  }

  return (
    <div
      className={`flex flex-col rounded-lg border border-slate-200 bg-white shadow-xs dark:border-slate-800 dark:bg-slate-900 ${className}`}
      aria-label="Diagnostic Findings Table"
    >
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-semibold text-slate-600 dark:border-slate-800 dark:bg-slate-950/60 dark:text-slate-400">
            <tr>
              <th scope="col" className="px-4 py-3">
                Severity
              </th>
              <th scope="col" className="px-4 py-3">
                Finding Title
              </th>
              <th scope="col" className="px-4 py-3">
                Rule ID
              </th>
              <th scope="col" className="px-4 py-3">
                Affected Object
              </th>
              <th scope="col" className="px-4 py-3">
                Classification
              </th>
              <th scope="col" className="px-4 py-3">
                Priority Rank
              </th>
              <th scope="col" className="px-4 py-3 text-right">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
            {pageFindings.map((finding) => {
              const isSelected = selectedFinding?.fingerprint === finding.fingerprint;

              return (
                <tr
                  key={finding.fingerprint}
                  onClick={() => onSelectFinding(finding)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onSelectFinding(finding);
                    }
                  }}
                  tabIndex={0}
                  className={`cursor-pointer transition-colors hover:bg-slate-50/80 focus:bg-slate-50/90 focus:outline-hidden dark:hover:bg-slate-800/40 dark:focus:bg-slate-800/60 ${
                    isSelected
                      ? "bg-blue-50/70 font-medium dark:bg-blue-950/30"
                      : ""
                  }`}
                  aria-selected={isSelected}
                  aria-label={`${finding.severity} finding: ${finding.title} on ${finding.object_id}`}
                >
                  {/* Severity */}
                  <td className="whitespace-nowrap px-4 py-3">
                    <SeverityBadge severity={finding.severity} />
                  </td>

                  {/* Finding Title & Summary */}
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-900 dark:text-slate-100">
                        {finding.title}
                      </span>
                      {finding.is_suppressed && (
                        <span className="rounded-full bg-slate-200 px-1.5 py-0.2 text-[10px] font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                          Suppressed
                        </span>
                      )}
                    </div>
                    <p className="line-clamp-1 max-w-md text-[11px] text-slate-500 dark:text-slate-400">
                      {finding.description}
                    </p>
                  </td>

                  {/* Rule ID */}
                  <td className="whitespace-nowrap px-4 py-3 font-mono text-[11px] text-slate-600 dark:text-slate-300">
                    {finding.rule_id}
                  </td>

                  {/* Affected Object */}
                  <td className="whitespace-nowrap px-4 py-3 font-mono text-[11px] text-blue-600 dark:text-blue-400">
                    {finding.object_id}
                  </td>

                  {/* Classification */}
                  <td className="whitespace-nowrap px-4 py-3">
                    <ClassificationBadge classification={finding.classification} />
                  </td>

                  {/* Priority Rank */}
                  <td className="whitespace-nowrap px-4 py-3">
                    <span
                      className={`inline-flex items-center rounded-md px-1.5 py-0.5 text-[10px] font-semibold ${
                        finding.priority_rank === "URGENT"
                          ? "bg-red-100 text-red-700 dark:bg-red-950/50 dark:text-red-400"
                          : finding.priority_rank === "IMPORTANT"
                          ? "bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-400"
                          : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                      }`}
                    >
                      {finding.priority_rank}
                    </span>
                  </td>

                  {/* Action */}
                  <td className="whitespace-nowrap px-4 py-3 text-right">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectFinding(finding);
                      }}
                      className="inline-flex items-center gap-1 rounded-sm p-1 text-slate-500 hover:text-blue-600 focus:outline-hidden dark:text-slate-400 dark:hover:text-blue-400"
                      aria-label={`Inspect finding ${finding.title}`}
                      title="Inspect finding details"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="flex items-center justify-between border-t border-slate-200 px-4 py-3 text-xs text-slate-600 dark:border-slate-800 dark:text-slate-400">
        <div>
          Page <span className="font-semibold">{safePage}</span> of{" "}
          <span className="font-semibold">{totalPages}</span> ({findings.length} findings)
        </div>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={handlePrevPage}
            disabled={safePage <= 1}
            className="flex items-center gap-1 rounded-md border border-slate-200 px-2 py-1 hover:bg-slate-100 disabled:opacity-40 dark:border-slate-800 dark:hover:bg-slate-800"
            aria-label="Previous Page"
          >
            <ChevronLeft className="h-3.5 w-3.5" />
            Prev
          </button>
          <button
            type="button"
            onClick={handleNextPage}
            disabled={safePage >= totalPages}
            className="flex items-center gap-1 rounded-md border border-slate-200 px-2 py-1 hover:bg-slate-100 disabled:opacity-40 dark:border-slate-800 dark:hover:bg-slate-800"
            aria-label="Next Page"
          >
            Next
            <ChevronRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
