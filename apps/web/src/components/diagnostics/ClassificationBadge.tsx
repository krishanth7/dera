"use client";

import React from "react";
import type { FindingClassificationType } from "@dera/contracts";
import { Wrench, Sparkles, AlertOctagon, HelpCircle, FileText } from "lucide-react";

interface ClassificationBadgeProps {
  classification?: FindingClassificationType | string;
  className?: string;
}

export function ClassificationBadge({ classification, className = "" }: ClassificationBadgeProps) {
  const normClass = (classification || "potential_engineering_concern").toLowerCase();

  const config: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
    confirmed_structural_defect: {
      label: "Confirmed Structural Defect",
      icon: <AlertOctagon className="w-3 h-3" aria-hidden="true" />,
      color: "border-red-500/20 bg-red-950/20 text-red-300",
    },
    potential_engineering_concern: {
      label: "Potential Engineering Concern",
      icon: <Wrench className="w-3 h-3" aria-hidden="true" />,
      color: "border-amber-500/20 bg-amber-950/20 text-amber-300",
    },
    optimization_candidate: {
      label: "Optimization Candidate",
      icon: <Sparkles className="w-3 h-3" aria-hidden="true" />,
      color: "border-emerald-500/20 bg-emerald-950/20 text-emerald-300",
    },
    maintainability_concern: {
      label: "Maintainability Concern",
      icon: <Wrench className="w-3 h-3" aria-hidden="true" />,
      color: "border-indigo-500/20 bg-indigo-950/20 text-indigo-300",
    },
    naming_convention_deviation: {
      label: "Naming Deviation",
      icon: <FileText className="w-3 h-3" aria-hidden="true" />,
      color: "border-cyan-500/20 bg-cyan-950/20 text-cyan-300",
    },
    metadata_limitation: {
      label: "Metadata Limitation",
      icon: <HelpCircle className="w-3 h-3" aria-hidden="true" />,
      color: "border-purple-500/20 bg-purple-950/20 text-purple-300",
    },
    informational_observation: {
      label: "Informational Observation",
      icon: <FileText className="w-3 h-3" aria-hidden="true" />,
      color: "border-slate-500/20 bg-slate-900/30 text-slate-300",
    },
  };

  const current = config[normClass] || {
    label: normClass.replace(/_/g, " "),
    icon: <Wrench className="w-3 h-3" aria-hidden="true" />,
    color: "border-slate-500/20 bg-slate-900/30 text-slate-300",
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium border ${current.color} ${className}`}
      aria-label={`Finding Classification: ${current.label}`}
    >
      {current.icon}
      <span>{current.label}</span>
    </span>
  );
}
