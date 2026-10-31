"use client";

import React from "react";
import type { DiagnosticSeverityLevel } from "@dera/contracts";
import { AlertCircle, AlertTriangle, Info, ShieldAlert, CheckCircle2 } from "lucide-react";

interface SeverityBadgeProps {
  severity: DiagnosticSeverityLevel | string;
  originalSeverity?: DiagnosticSeverityLevel | string;
  className?: string;
}

export function SeverityBadge({ severity, originalSeverity, className = "" }: SeverityBadgeProps) {
  const normSev = (severity || "informational").toLowerCase();

  const config = {
    critical: {
      label: "Critical Defect",
      srText: "Critical Severity: Immediate structural or integrity failure requiring urgent remediation",
      icon: <ShieldAlert className="w-3.5 h-3.5" aria-hidden="true" />,
      badgeClass: "bg-red-500/10 text-red-400 border-red-500/30",
    },
    high: {
      label: "High Priority",
      srText: "High Severity: Substantial schema discrepancy or performance constraint",
      icon: <AlertCircle className="w-3.5 h-3.5" aria-hidden="true" />,
      badgeClass: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    },
    medium: {
      label: "Medium Priority",
      srText: "Medium Severity: Optimization candidate or architectural dependency concern",
      icon: <AlertTriangle className="w-3.5 h-3.5" aria-hidden="true" />,
      badgeClass: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
    },
    low: {
      label: "Low Priority",
      srText: "Low Severity: Maintainability guideline or naming convention deviation",
      icon: <Info className="w-3.5 h-3.5" aria-hidden="true" />,
      badgeClass: "bg-blue-500/10 text-blue-400 border-blue-500/30",
    },
    informational: {
      label: "Informational",
      srText: "Informational: Diagnostic observation or metadata capability state",
      icon: <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />,
      badgeClass: "bg-slate-500/10 text-slate-300 border-slate-500/30",
    },
  }[normSev] || {
    label: normSev.toUpperCase(),
    srText: `Severity level ${normSev}`,
    icon: <Info className="w-3.5 h-3.5" aria-hidden="true" />,
    badgeClass: "bg-slate-500/10 text-slate-300 border-slate-500/30",
  };

  const isAdjusted = originalSeverity && originalSeverity.toLowerCase() !== normSev;

  return (
    <div className={`inline-flex items-center gap-1.5 ${className}`}>
      <span
        role="status"
        aria-label={config.srText}
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border ${config.badgeClass}`}
      >
        {config.icon}
        <span>{config.label}</span>
      </span>
      {isAdjusted && (
        <span
          className="text-[10px] text-slate-400 italic"
          aria-label={`Adjusted from ${originalSeverity} under conservative severity policy`}
        >
          (Adjusted from {originalSeverity})
        </span>
      )}
    </div>
  );
}
