"use client";

import React from "react";
import { DiagnosticFinding } from "@/lib/diagnostics/types";
import { SeverityBadge } from "./SeverityBadge";
import { ClassificationBadge } from "./ClassificationBadge";
import { EvidenceInspector } from "./EvidenceInspector";
import { RecommendationPanel } from "./RecommendationPanel";
import { SuppressionControls } from "./SuppressionControls";
import {
  X,
  ShieldAlert,
  Info,
  Clock,
  ExternalLink,
  Fingerprint,
  Layers,
} from "lucide-react";
import Link from "next/link";

interface FindingDetailsProps {
  finding: DiagnosticFinding | null;
  onClose: () => void;
  onApplySuppression?: (fingerprint: string, reason: string, durationDays: number) => void;
  onRevokeSuppression?: (fingerprint: string) => void;
  className?: string;
}

export function FindingDetails({
  finding,
  onClose,
  onApplySuppression,
  onRevokeSuppression,
  className = "",
}: FindingDetailsProps) {
  if (!finding) return null;

  return (
    <div
      className={`flex flex-col rounded-lg border border-slate-200 bg-white shadow-lg dark:border-slate-800 dark:bg-slate-900 ${className}`}
      role="region"
      aria-label={`Details for finding: ${finding.title}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between border-b border-slate-200 p-5 dark:border-slate-800">
        <div className="space-y-1.5">
          <div className="flex flex-wrap items-center gap-2">
            <SeverityBadge severity={finding.severity} />
            <ClassificationBadge classification={finding.classification} />
            <span className="font-mono text-xs text-slate-500 dark:text-slate-400">
              {finding.rule_id} v{finding.rule_version}
            </span>
          </div>
          <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
            {finding.title}
          </h3>
          <p className="text-xs text-slate-600 dark:text-slate-300">
            {finding.description}
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-200"
          aria-label="Close details panel"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="space-y-6 overflow-y-auto p-5 text-xs max-h-[calc(100vh-200px)]">
        {/* Severity Rationale Callout */}
        {finding.severity_rationale && (
          <div className="rounded-md border border-slate-200 bg-slate-50/80 p-3.5 dark:border-slate-800 dark:bg-slate-950/40">
            <div className="mb-1 flex items-center gap-1.5 font-semibold text-slate-800 dark:text-slate-200">
              <Info className="h-4 w-4 text-blue-500" />
              <span>Severity Rationale</span>
            </div>
            <p className="text-slate-600 dark:text-slate-400">
              {finding.severity_rationale}
            </p>
          </div>
        )}

        {/* Affected Object & Fingerprint */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 rounded-md border border-slate-200/80 p-3 dark:border-slate-800">
          <div>
            <span className="block text-[11px] font-medium text-slate-500 dark:text-slate-400">
              Affected Database Object
            </span>
            <div className="mt-1 flex items-center gap-2">
              <span className="font-mono font-semibold text-blue-600 dark:text-blue-400">
                {finding.object_id}
              </span>
              <Link
                href={`/app/tables?table=${encodeURIComponent(finding.object_id)}`}
                className="text-slate-400 hover:text-blue-600 dark:hover:text-blue-400"
                title="View in Table Inspector"
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>

          <div>
            <span className="block text-[11px] font-medium text-slate-500 dark:text-slate-400">
              Stable Cryptographic Fingerprint
            </span>
            <div className="mt-1 flex items-center gap-1.5 font-mono text-[11px] text-slate-700 dark:text-slate-300">
              <Fingerprint className="h-3.5 w-3.5 text-slate-400" />
              <span className="truncate" title={finding.fingerprint}>
                {finding.fingerprint}
              </span>
            </div>
          </div>
        </div>

        {/* Structured Recommendation */}
        <RecommendationPanel
          recommendation={
            finding.structured_recommendation
              ? {
                  recommendation_id: finding.structured_recommendation.recommendation_id,
                  rule_id: finding.structured_recommendation.rule_id,
                  title: finding.structured_recommendation.title,
                  description: finding.structured_recommendation.title,
                  suggested_action: finding.structured_recommendation.action,
                  risk_considerations: finding.structured_recommendation.risk_considerations.join(" "),
                  verification_steps: finding.structured_recommendation.verification_steps,
                  limitations: "Advisory only; DERA does not execute migrations automatically.",
                  version: "1.0.0",
                  is_advisory: true,
                }
              : null
          }
          fallbackText={finding.recommendation}
        />

        {/* Typed Evidence Inspector */}
        <EvidenceInspector
          evidenceList={finding.evidence}
          affectedObjectId={finding.object_id}
        />

        {/* Suppression Governance */}
        <SuppressionControls
          finding={finding}
          onApplySuppression={onApplySuppression}
          onRevokeSuppression={onRevokeSuppression}
        />
      </div>
    </div>
  );
}
