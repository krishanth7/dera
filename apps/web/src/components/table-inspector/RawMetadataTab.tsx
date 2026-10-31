"use client";

/**
 * DERA — Table Inspector Raw Metadata Tab
 * Formatted JSON inspector with provenance details and copy action.
 */

import React, { useState } from "react";
import { Code2, Copy, Check, FileJson, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { TableDetailItem } from "@/lib/api-client";

interface RawMetadataTabProps {
  table: TableDetailItem;
  sourceEngine?: string;
  completeness?: string;
}

export function RawMetadataTab({ table, sourceEngine, completeness }: RawMetadataTabProps) {
  const [copied, setCopied] = useState(false);
  const jsonString = JSON.stringify(table, null, 2);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(jsonString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  return (
    <div className="space-y-4">
      {/* Provenance Card */}
      <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
        <div>
          <span className="text-[11px] text-slate-500 uppercase font-medium block">Database Engine</span>
          <span className="font-mono font-semibold text-slate-900 dark:text-slate-100 uppercase">
            {sourceEngine || "SQL Relational"}
          </span>
        </div>
        <div>
          <span className="text-[11px] text-slate-500 uppercase font-medium block">Metadata Completeness</span>
          <span className="font-mono font-semibold text-slate-900 dark:text-slate-100 capitalize">
            {completeness || "Complete"}
          </span>
        </div>
        <div>
          <span className="text-[11px] text-slate-500 uppercase font-medium block">Canonical Contract</span>
          <span className="font-mono text-slate-700 dark:text-slate-300">Phase 6.2 Structural Specification</span>
        </div>
      </div>

      {/* JSON Viewer */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden bg-slate-950 text-slate-200">
        <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/80 border-b border-slate-800">
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
            <FileJson className="w-4 h-4 text-indigo-400" />
            <span>canonical_table_detail.json</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopy}
            className="h-7 text-xs text-slate-300 hover:text-white hover:bg-slate-800 gap-1.5"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? "Copied" : "Copy JSON"}
          </Button>
        </div>
        <pre className="p-4 text-xs font-mono leading-relaxed overflow-x-auto max-h-[500px]">
          <code>{jsonString}</code>
        </pre>
      </div>
    </div>
  );
}
