"use client";

/**
 * DERA — Dependency Explorer Route Page
 * Path: /dependencies (and /app/dependencies)
 * Coordinates full topological ordering, reachability blast radius, and cycle detection.
 */

import React, { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { GitFork, RefreshCw, AlertCircle, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DependencyExplorerStudio,
  type DependencyExplorerViewModel,
} from "@/components/dependency-explorer";
import {
  apiClient,
  type SchemaSummary,
  type DependencyAnalysisResponse,
  type CycleReportResponse,
  type RelationshipGraphResponse,
} from "@/lib/api-client";
import { useWorkspace } from "@/providers/workspace-provider";

export default function DependenciesPage() {
  const searchParams = useSearchParams();
  const { currentWorkspace } = useWorkspace();

  const querySchemaId = searchParams.get("schemaId") || "";
  const queryTableId = searchParams.get("tableId") || "";

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [schemas, setSchemas] = useState<SchemaSummary[]>([]);
  const [activeSchema, setActiveSchema] = useState<SchemaSummary | null>(null);

  const [analysis, setAnalysis] = useState<DependencyAnalysisResponse | null>(null);
  const [cycles, setCycles] = useState<CycleReportResponse | null>(null);
  const [relationships, setRelationships] = useState<RelationshipGraphResponse | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadDependencyData() {
      if (!currentWorkspace?.id) return;

      try {
        setLoading(true);
        setError(null);

        const schemaList = await apiClient.listSchemas(currentWorkspace.id);
        if (schemaList.length === 0) {
          throw new Error("No database schemas available in this workspace. Please inspect a connection first.");
        }

        if (!cancelled) setSchemas(schemaList);

        const targetSchema =
          (querySchemaId ? schemaList.find((s) => s.schema_id === querySchemaId) : null) ||
          schemaList[0];

        if (!cancelled) setActiveSchema(targetSchema);

        const [depRes, cycleRes, relRes] = await Promise.all([
          apiClient.getSchemaDependencies(targetSchema.schema_id, currentWorkspace.id),
          apiClient.getSchemaCycles(targetSchema.schema_id, currentWorkspace.id),
          apiClient.getSchemaRelationships(targetSchema.schema_id, currentWorkspace.id),
        ]);

        if (!cancelled) {
          setAnalysis(depRes);
          setCycles(cycleRes);
          setRelationships(relRes);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load dependency analysis");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadDependencyData();
    return () => {
      cancelled = true;
    };
  }, [querySchemaId, currentWorkspace?.id]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <RefreshCw className="w-8 h-8 animate-spin text-indigo-500" />
        <div className="text-center">
          <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
            Analyzing Schema Dependencies...
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Running Tarjan SCC, Johnson cycle enumeration, and topological sorting algorithms.
          </p>
        </div>
      </div>
    );
  }

  if (error || !analysis || !cycles || !relationships || !activeSchema) {
    return (
      <div className="max-w-xl mx-auto my-12 p-6 rounded-2xl border border-rose-200 dark:border-rose-900/50 bg-rose-50/50 dark:bg-rose-950/20 text-center space-y-4">
        <div className="p-3 bg-rose-100 dark:bg-rose-900/50 text-rose-600 rounded-full w-fit mx-auto">
          <AlertCircle className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
            Dependency Analysis Unavailable
          </h2>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
            {error || "Unable to retrieve dependency graphs for this schema."}
          </p>
        </div>
        <div className="pt-2 flex justify-center gap-3">
          <Link href="/schemas">
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <ArrowLeft className="w-3.5 h-3.5" />
              Return to Schemas
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  const viewModel: DependencyExplorerViewModel = {
    schemaId: activeSchema.schema_id,
    databaseName: activeSchema.database_name,
    sourceEngine: activeSchema.engine || activeSchema.source_engine,
    completeness: activeSchema.completeness,
    analysis,
    cycles,
    relationships,
    initialTableId: queryTableId,
  };

  return <DependencyExplorerStudio viewModel={viewModel} />;
}
