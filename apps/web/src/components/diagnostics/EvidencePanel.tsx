"use client";

import React from "react";
import type { DiagnosticEvidenceItem, EvidenceCompletenessType, FindingConfidenceType } from "@dera/contracts";
import { Database, CheckCircle, AlertTriangle, ShieldCheck, Lock } from "lucide-react";

interface EvidencePanelProps {
  evidence: DiagnosticEvidenceItem[];
  confidence?: FindingConfidenceType;
  completeness?: EvidenceCompletenessType;
  className?: string;
}

export function EvidencePanel({
  evidence,
  confidence = "verified",
  completeness = "complete",
  className = "",
}: EvidencePanelProps) {
  return (
    <div className={`space-y-3 bg-slate-950/40 border border-slate-800/80 rounded-lg p-3.5 ${className}`}>
      <div className="flex items-center justify-between pb-2 border-b border-slate-800/60">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-sky-400" aria-hidden="true" />
          <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
            Verified Supporting Evidence ({evidence.length})
          </h4>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span
            className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium border ${
              confidence === "verified"
                ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/20"
                : "bg-amber-500/10 text-amber-300 border-amber-500/20"
            }`}
            aria-label={`Evidence Status: ${confidence}`}
          >
            <ShieldCheck className="w-3 h-3" aria-hidden="true" />
            <span>Confidence: {confidence.toUpperCase()}</span>
          </span>
          <span
            className="text-[10px] text-slate-400"
            aria-label={`Metadata Completeness: ${completeness}`}
          >
            Completeness: {completeness}
          </span>
        </div>
      </div>

      {evidence.length === 0 ? (
        <p className="text-xs text-slate-400 italic">No detailed evidence records attached.</p>
      ) : (
        <div className="space-y-2">
          {evidence.map((item, idx) => (
            <div
              key={`${item.object_id}-${item.field_name}-${idx}`}
              className="bg-slate-900/60 border border-slate-800/40 rounded p-2.5 text-xs font-mono space-y-1.5"
            >
              <div className="flex items-center justify-between text-slate-300 font-sans">
                <span className="font-semibold text-sky-300">{item.object_id}</span>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider font-mono">
                  {item.field_name}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-800/40 text-[11px]">
                <div>
                  <span className="text-slate-400 font-sans">Observed: </span>
                  <span className="text-slate-200">
                    {typeof item.observed_value === "object"
                      ? JSON.stringify(item.observed_value)
                      : String(item.observed_value)}
                  </span>
                </div>
                {item.expected_value !== undefined && (
                  <div>
                    <span className="text-slate-400 font-sans">Expected: </span>
                    <span className="text-emerald-300">{String(item.expected_value)}</span>
                  </div>
                )}
              </div>
              {item.message && (
                <p className="text-[11px] font-sans text-slate-300 italic pt-1">{item.message}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
