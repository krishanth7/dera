"use client";

import React from "react";
import { TypedEvidence, EvidenceCompleteness } from "@/lib/diagnostics/types";
import {
  FileCode,
  Layers,
  Database,
  Link as LinkIcon,
  CheckCircle,
  AlertCircle,
  ExternalLink,
  Shield,
} from "lucide-react";
import Link from "next/link";

interface EvidenceInspectorProps {
  evidenceList: TypedEvidence[];
  affectedObjectId?: string;
  className?: string;
}

function getCompletenessBadge(completeness?: EvidenceCompleteness) {
  switch (completeness) {
    case "COMPLETE":
      return (
        <span className="inline-flex items-center gap-1 rounded-sm bg-emerald-100 px-1.5 py-0.5 text-[10px] font-medium text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300">
          <CheckCircle className="h-3 w-3" /> Complete
        </span>
      );
    case "PARTIAL":
      return (
        <span className="inline-flex items-center gap-1 rounded-sm bg-amber-100 px-1.5 py-0.5 text-[10px] font-medium text-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
          <AlertCircle className="h-3 w-3" /> Partial
        </span>
      );
    case "RESTRICTED":
      return (
        <span className="inline-flex items-center gap-1 rounded-sm bg-purple-100 px-1.5 py-0.5 text-[10px] font-medium text-purple-800 dark:bg-purple-950/40 dark:text-purple-300">
          <Shield className="h-3 w-3" /> Restricted
        </span>
      );
    case "UNSUPPORTED":
      return (
        <span className="inline-flex items-center gap-1 rounded-sm bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-800 dark:bg-slate-800 dark:text-slate-300">
          Unsupported
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center rounded-sm bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300">
          {completeness || "Unknown"}
        </span>
      );
  }
}

export function EvidenceInspector({
  evidenceList,
  affectedObjectId,
  className = "",
}: EvidenceInspectorProps) {
  if (evidenceList.length === 0) {
    return (
      <div className={`p-4 text-xs text-slate-500 dark:text-slate-400 ${className}`}>
        No detailed evidence records attached to this finding.
      </div>
    );
  }

  return (
    <div className={`space-y-3 ${className}`} aria-label="Evidence Inspector">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
          Verified Evidence ({evidenceList.length})
        </h4>
        {affectedObjectId && (
          <Link
            href={`/app/tables?table=${encodeURIComponent(affectedObjectId)}`}
            className="inline-flex items-center gap-1 text-[11px] font-medium text-blue-600 hover:underline dark:text-blue-400"
            title="Inspect affected object in Table Inspector"
          >
            <span>Inspect in Table View</span>
            <ExternalLink className="h-3 w-3" />
          </Link>
        )}
      </div>

      <div className="space-y-2">
        {evidenceList.map((item, index) => (
          <div
            key={index}
            className="rounded-md border border-slate-200 bg-slate-50/60 p-3 text-xs dark:border-slate-800 dark:bg-slate-950/40"
          >
            {/* Header: Evidence type & completeness */}
            <div className="mb-2 flex flex-wrap items-center justify-between gap-1">
              <div className="flex items-center gap-1.5 font-mono text-[11px] font-medium text-slate-800 dark:text-slate-200">
                <FileCode className="h-3.5 w-3.5 text-blue-500" />
                <span>{item.evidence_type || "OBJECT_EVIDENCE"}</span>
                {item.field_name && (
                  <span className="text-slate-500 dark:text-slate-400">
                    ({item.field_name})
                  </span>
                )}
              </div>
              <div>{getCompletenessBadge(item.completeness)}</div>
            </div>

            {/* Object ID reference */}
            <div className="mb-1 text-[11px]">
              <span className="text-slate-500 dark:text-slate-400">Target Object: </span>
              <span className="font-mono font-medium text-slate-900 dark:text-slate-100">
                {item.object_id}
              </span>
            </div>

            {/* Observed & Expected Values */}
            {item.observed_value !== undefined && (
              <div className="mt-2 rounded-sm bg-slate-100 p-2 font-mono text-[11px] dark:bg-slate-900">
                <span className="text-slate-500 dark:text-slate-400">Observed: </span>
                <span className="text-slate-900 dark:text-slate-100">
                  {typeof item.observed_value === "object"
                    ? JSON.stringify(item.observed_value)
                    : String(item.observed_value)}
                </span>
                {item.expected_value !== undefined && (
                  <div className="mt-1">
                    <span className="text-slate-500 dark:text-slate-400">Expected: </span>
                    <span className="text-emerald-700 dark:text-emerald-400">
                      {typeof item.expected_value === "object"
                        ? JSON.stringify(item.expected_value)
                        : String(item.expected_value)}
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* Evidence message */}
            {item.message && (
              <p className="mt-2 text-[11px] text-slate-600 dark:text-slate-300">
                {item.message}
              </p>
            )}

            {/* Provenance if available */}
            {item.provenance && (
              <div className="mt-2 flex flex-wrap items-center gap-3 border-t border-slate-200/70 pt-2 text-[10px] text-slate-400 dark:border-slate-800">
                {item.provenance.engine && (
                  <span>Engine: {item.provenance.engine}</span>
                )}
                {item.provenance.snapshot_id && (
                  <span>Snapshot: {item.provenance.snapshot_id}</span>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
