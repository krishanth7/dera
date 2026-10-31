"use client";

/**
 * DERA — Table Inspector Header Component
 * Displays table identity, namespace, engine provenance, completeness,
 * snapshot status, and quick studio navigation actions.
 */

import React, { useState } from "react";
import Link from "next/link";
import {
  Table2,
  Database,
  Network,
  GitFork,
  ArrowLeft,
  Copy,
  Check,
  ShieldCheck,
  Camera,
  Layers,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { TableInspectorViewModel } from "./types";

interface TableMetadataHeaderProps {
  viewModel: TableInspectorViewModel;
}

export function TableMetadataHeader({ viewModel }: TableMetadataHeaderProps) {
  const { table, schemaId, databaseName, sourceEngine, completeness, isSnapshot, snapshotFingerprint } =
    viewModel;
  const [copied, setCopied] = useState(false);

  const handleCopyName = async () => {
    try {
      await navigator.clipboard.writeText(table.name);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback if clipboard API restricted
    }
  };

  const getCompletenessVariant = (status?: string) => {
    switch (status?.toLowerCase()) {
      case "complete":
        return "success";
      case "partial":
        return "warning";
      case "restricted":
        return "destructive";
      default:
        return "secondary";
    }
  };

  return (
    <div className="space-y-4">
      {/* Breadcrumb Navigation */}
      <nav aria-label="Breadcrumb" className="flex items-center space-x-2 text-xs text-slate-500 dark:text-slate-400">
        <Link href="/schemas" className="hover:text-slate-800 dark:hover:text-slate-200 transition-colors">
          Schemas
        </Link>
        <span>/</span>
        <Link
          href={`/schemas/${encodeURIComponent(schemaId)}`}
          className="hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
        >
          {databaseName || "Schema Details"}
        </Link>
        <span>/</span>
        <span className="text-slate-900 dark:text-slate-100 font-medium">
          {table.namespace}.{table.name}
        </span>
      </nav>

      {/* Snapshot Banner if Applicable */}
      {isSnapshot && (
        <div className="flex items-center space-x-2 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-700 dark:text-amber-400 text-xs">
          <Camera className="w-4 h-4 shrink-0" />
          <span>
            Viewing <strong>Immutable Snapshot</strong> metadata (SHA-256:{" "}
            <code className="font-mono text-[11px] bg-amber-500/10 px-1 py-0.5 rounded">
              {snapshotFingerprint ? snapshotFingerprint.substring(0, 16) + "..." : "N/A"}
            </code>
            ). Structural data is historically preserved.
          </span>
        </div>
      )}

      {/* Main Title & Action Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="p-2 bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 rounded-lg border border-indigo-200 dark:border-indigo-900">
              <Table2 className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 font-mono">
                  {table.name}
                </h1>
                <button
                  type="button"
                  onClick={handleCopyName}
                  title="Copy table name"
                  aria-label="Copy table name"
                  className="p-1 rounded text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  {copied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
              <div className="flex flex-wrap items-center gap-2 mt-1">
                <Badge variant="outline" className="text-xs font-mono">
                  namespace: {table.namespace}
                </Badge>
                <Badge variant="secondary" className="text-xs uppercase">
                  {table.table_type || "TABLE"}
                </Badge>
                {sourceEngine && (
                  <Badge variant="outline" className="text-xs uppercase text-slate-600 dark:text-slate-300">
                    <Database className="w-3 h-3 mr-1 inline" />
                    {sourceEngine}
                  </Badge>
                )}
                {completeness && (
                  <Badge variant={getCompletenessVariant(completeness)} className="text-xs capitalize">
                    <ShieldCheck className="w-3 h-3 mr-1 inline" />
                    {completeness}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Studio Navigation Actions */}
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" size="sm" className="gap-1.5 text-xs" asChild>
            <Link
              href={`/relationships?schemaId=${encodeURIComponent(schemaId)}&selectedTableId=${encodeURIComponent(table.table_id)}`}
            >
              <Network className="w-3.5 h-3.5 text-indigo-500" />
              View in ER Canvas
            </Link>
          </Button>
          <Button variant="outline" size="sm" className="gap-1.5 text-xs" asChild>
            <Link
              href={`/dependencies?schemaId=${encodeURIComponent(schemaId)}&tableId=${encodeURIComponent(table.table_id)}`}
            >
              <GitFork className="w-3.5 h-3.5 text-blue-500" />
              Explore Dependencies
            </Link>
          </Button>
          <Button variant="ghost" size="sm" className="gap-1.5 text-xs" asChild>
            <Link href={`/schemas/${encodeURIComponent(schemaId)}`}>
              <ArrowLeft className="w-3.5 h-3.5" />
              Back to Schema
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
