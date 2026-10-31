"use client";

import React, { useState } from "react";
import type { DiagnosticFinding } from "@dera/contracts";
import { SeverityBadge } from "./SeverityBadge";
import { ClassificationBadge } from "./ClassificationBadge";
import { EvidencePanel } from "./EvidencePanel";
import { RecommendationPanel } from "./RecommendationPanel";
import { ChevronDown, ChevronUp, BellOff, Tag, Fingerprint } from "lucide-react";

interface FindingDetailCardProps {
  finding: DiagnosticFinding;
  className?: string;
}

export function FindingDetailCard({ finding, className = "" }: FindingDetailCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div
      className={`border rounded-lg bg-slate-900/40 transition-colors ${
        finding.is_suppressed
          ? "border-slate-800/60 opacity-75"
          : "border-slate-800 hover:border-slate-700"
      } ${className}`}
    >
      <div className="p-4 space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <SeverityBadge
                severity={finding.severity}
                originalSeverity={finding.original_severity}
              />
              <ClassificationBadge classification={finding.classification} />
              {finding.is_suppressed && (
                <span
                  role="status"
                  aria-label="Finding Suppressed: Authorized governance exception is active"
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-purple-500/10 text-purple-300 border border-purple-500/20"
                >
                  <BellOff className="w-3 h-3" aria-hidden="true" />
                  <span>Suppressed ({finding.suppression_id || "Active"})</span>
                </span>
              )}
            </div>
            <h3 className="text-sm font-semibold text-slate-100 pt-1">
              {finding.title || finding.message}
            </h3>
          </div>

          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 text-slate-400 hover:text-slate-200 transition-colors rounded focus:outline-none focus:ring-1 focus:ring-sky-500"
            aria-expanded={isExpanded}
            aria-label={isExpanded ? "Collapse finding details" : "Expand finding details"}
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" aria-hidden="true" />
            ) : (
              <ChevronDown className="w-4 h-4" aria-hidden="true" />
            )}
          </button>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed font-sans">
          {finding.description}
        </p>

        {finding.severity_rationale && (
          <div className="text-[11px] text-slate-400 bg-slate-950/30 p-2 rounded border border-slate-800/40">
            <span className="font-semibold text-slate-300">Severity Rationale: </span>
            <span>{finding.severity_rationale}</span>
          </div>
        )}

        {isExpanded && (
          <div className="pt-3 border-t border-slate-800/60 space-y-3">
            {finding.evidence && finding.evidence.length > 0 && (
              <EvidencePanel
                evidence={finding.evidence}
                confidence={finding.confidence}
                completeness={finding.metadata_completeness}
              />
            )}

            <RecommendationPanel
              recommendation={finding.structured_recommendation}
              fallbackText={finding.recommendation || finding.remediation}
            />

            <div className="flex flex-wrap items-center justify-between text-[10px] text-slate-400 pt-1 font-mono">
              <span className="flex items-center gap-1">
                <Tag className="w-3 h-3" aria-hidden="true" />
                Rule: {finding.rule_id}
              </span>
              {finding.fingerprint && (
                <span className="flex items-center gap-1" title={finding.fingerprint}>
                  <Fingerprint className="w-3 h-3" aria-hidden="true" />
                  Fingerprint: {finding.fingerprint.slice(0, 12)}...
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
