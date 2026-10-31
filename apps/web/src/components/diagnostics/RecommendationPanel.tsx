"use client";

import React from "react";
import type { StructuredRecommendationItem } from "@dera/contracts";
import { Lightbulb, AlertTriangle, CheckSquare, Shield } from "lucide-react";

interface RecommendationPanelProps {
  recommendation?: StructuredRecommendationItem | null;
  fallbackText?: string | null;
  className?: string;
}

export function RecommendationPanel({
  recommendation,
  fallbackText,
  className = "",
}: RecommendationPanelProps) {
  if (!recommendation && !fallbackText) {
    return null;
  }

  return (
    <div className={`space-y-3 bg-indigo-950/20 border border-indigo-500/20 rounded-lg p-3.5 ${className}`}>
      <div className="flex items-center justify-between pb-2 border-b border-indigo-500/20">
        <div className="flex items-center gap-2">
          <Lightbulb className="w-4 h-4 text-amber-300" aria-hidden="true" />
          <h4 className="text-xs font-semibold text-indigo-200 uppercase tracking-wider">
            Advisory Engineering Action
          </h4>
        </div>
        <span className="text-[10px] text-indigo-300/80 font-mono flex items-center gap-1">
          <Shield className="w-3 h-3 text-emerald-400" aria-hidden="true" />
          Read-Only / No Automated DDL
        </span>
      </div>

      {recommendation ? (
        <div className="space-y-2.5 text-xs text-slate-300">
          <div>
            <span className="font-semibold text-slate-100 block mb-1">
              {recommendation.title}
            </span>
            <p className="text-slate-300 leading-relaxed bg-slate-900/60 border border-slate-800/60 p-2.5 rounded font-sans">
              {recommendation.suggested_action}
            </p>
          </div>

          {recommendation.risk_considerations && (
            <div className="flex items-start gap-2 bg-amber-950/20 border border-amber-500/20 p-2 rounded text-[11px] text-amber-200">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" aria-hidden="true" />
              <div>
                <span className="font-semibold">Risk Considerations: </span>
                <span>{recommendation.risk_considerations}</span>
              </div>
            </div>
          )}

          {recommendation.verification_steps && recommendation.verification_steps.length > 0 && (
            <div className="pt-1">
              <span className="font-semibold text-slate-200 block text-[11px] mb-1">
                Verification Steps:
              </span>
              <ul className="space-y-1 list-none pl-0 text-[11px]">
                {recommendation.verification_steps.map((step, idx) => (
                  <li key={idx} className="flex items-start gap-1.5 text-slate-300">
                    <CheckSquare className="w-3.5 h-3.5 text-sky-400 shrink-0 mt-0.5" aria-hidden="true" />
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <p className="text-xs text-slate-300 leading-relaxed font-sans bg-slate-900/60 p-2.5 rounded border border-slate-800/60">
          {fallbackText}
        </p>
      )}
    </div>
  );
}
