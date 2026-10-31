"use client";

/**
 * DERA — Table Inspector Dependencies Tab
 * Summarizes immediate incoming and outgoing relationships, cycle membership,
 * and links directly to the full Dependency Explorer.
 */

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { GitFork, ArrowUpRight, ArrowDownLeft, AlertTriangle, CheckCircle, ExternalLink, RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient, type TableDependencyResponse, type TableRelationshipsResponse, type TableDetailItem } from "@/lib/api-client";
import { useWorkspace } from "@/providers/workspace-provider";

interface DependenciesTabProps {
  table: TableDetailItem;
  schemaId: string;
}

export function DependenciesTab({ table, schemaId }: DependenciesTabProps) {
  const { currentWorkspace } = useWorkspace();
  const [depData, setDepData] = useState<TableDependencyResponse | null>(null);
  const [relData, setRelData] = useState<TableRelationshipsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadDependencies() {
      if (!currentWorkspace?.id || !schemaId || !table.table_id) return;
      try {
        setLoading(true);
        setError(null);
        const [deps, rels] = await Promise.all([
          apiClient.getTableDependencies(schemaId, table.table_id, currentWorkspace.id),
          apiClient.getTableRelationships(schemaId, table.table_id, currentWorkspace.id),
        ]);
        if (!cancelled) {
          setDepData(deps);
          setRelData(rels);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load table dependencies");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadDependencies();
    return () => {
      cancelled = true;
    };
  }, [schemaId, table.table_id, currentWorkspace?.id]);

  if (loading) {
    return (
      <div className="p-8 text-center space-y-3">
        <RefreshCw className="w-6 h-6 animate-spin mx-auto text-indigo-500" />
        <p className="text-xs text-slate-500">Analyzing schema graph dependencies...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 rounded-xl border border-rose-500/20 bg-rose-500/10 text-rose-700 dark:text-rose-400 text-xs">
        {error}
      </div>
    );
  }

  const outgoing = relData?.outgoing || [];
  const incoming = relData?.incoming || [];

  return (
    <div className="space-y-6">
      {/* Cycle & Structural Status Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
        <div className="flex items-center gap-3">
          {depData?.in_cycle ? (
            <div className="p-2 rounded-lg bg-rose-500/10 text-rose-600 border border-rose-500/20">
              <AlertTriangle className="w-5 h-5" />
            </div>
          ) : (
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-600 border border-emerald-500/20">
              <CheckCircle className="w-5 h-5" />
            </div>
          )}
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                {depData?.in_cycle ? "Circular Dependency Detected" : "Acyclic Structural Placement"}
              </h3>
              {depData?.in_cycle && (
                <Badge variant="outline" className="text-[10px] bg-rose-500/10 text-rose-700 dark:text-rose-300 border-rose-500/30">
                  Cyclic SCC ({depData.scc_id})
                </Badge>
              )}
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
              {depData?.in_cycle
                ? "This table is part of a circular foreign key cycle. Deferred constraint resolution or nullable foreign keys required for migration."
                : "This table is safely ordered in the schema DAG without cyclic reference loops."}
            </p>
          </div>
        </div>

        <Link
          href={`/dependencies?schemaId=${encodeURIComponent(schemaId)}&tableId=${encodeURIComponent(table.table_id)}`}
        >
          <Button variant="outline" size="sm" className="gap-1.5 text-xs whitespace-nowrap">
            <GitFork className="w-3.5 h-3.5 text-indigo-500" />
            Deep Dependency Analysis
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Outgoing: Prerequisites (Tables referenced by this table) */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ArrowUpRight className="w-4 h-4 text-blue-500" />
              <h3 className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                Prerequisites (Outgoing Dependencies)
              </h3>
            </div>
            <Badge variant="secondary" className="text-[10px] font-mono">
              {outgoing.length} tables
            </Badge>
          </div>
          <p className="text-[11px] text-slate-500">
            Tables that must exist <strong>before</strong> &ldquo;{table.name}&rdquo; can be populated.
          </p>

          {outgoing.length > 0 ? (
            <div className="space-y-2">
              {outgoing.map((edge) => (
                <div
                  key={edge.edge_id}
                  className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs flex items-center justify-between"
                >
                  <div>
                    <div className="font-mono font-medium text-slate-900 dark:text-slate-100">
                      {edge.target_table_name}
                    </div>
                    <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                      {edge.source_columns.join(", ")} &rarr; {edge.target_columns.join(", ")}
                    </div>
                  </div>
                  <Link
                    href={`/tables/${encodeURIComponent(edge.target_table_id)}?schemaId=${encodeURIComponent(schemaId)}`}
                    className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                    title="Inspect referenced table"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </Link>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 rounded-xl border border-dashed border-slate-200 dark:border-slate-800 text-xs text-slate-500 text-center">
              No outgoing dependencies (root/independent table).
            </div>
          )}
        </div>

        {/* Incoming: Dependents (Tables referencing this table) */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ArrowDownLeft className="w-4 h-4 text-emerald-500" />
              <h3 className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                Dependents (Incoming References)
              </h3>
            </div>
            <Badge variant="secondary" className="text-[10px] font-mono">
              {incoming.length} tables
            </Badge>
          </div>
          <p className="text-[11px] text-slate-500">
            Tables that depend on &ldquo;{table.name}&rdquo; and are affected by schema changes.
          </p>

          {incoming.length > 0 ? (
            <div className="space-y-2">
              {incoming.map((edge) => (
                <div
                  key={edge.edge_id}
                  className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs flex items-center justify-between"
                >
                  <div>
                    <div className="font-mono font-medium text-slate-900 dark:text-slate-100">
                      {edge.source_table_name}
                    </div>
                    <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                      via {edge.constraint_name}
                    </div>
                  </div>
                  <Link
                    href={`/tables/${encodeURIComponent(edge.source_table_id)}?schemaId=${encodeURIComponent(schemaId)}`}
                    className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                    title="Inspect referencing table"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </Link>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 rounded-xl border border-dashed border-slate-200 dark:border-slate-800 text-xs text-slate-500 text-center">
              No dependent tables reference &ldquo;{table.name}&rdquo;.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
