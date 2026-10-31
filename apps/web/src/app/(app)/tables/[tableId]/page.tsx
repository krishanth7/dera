"use client";

/**
 * DERA — Table Inspector Route Page
 * Path: /tables/[tableId] (and /app/tables/[tableId])
 * Displays comprehensive structural metadata, columns, keys, indexes, and dependencies.
 */

import React, { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Table2, ArrowLeft, RefreshCw, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { TableInspector, type TableInspectorViewModel } from "@/components/table-inspector";
import { apiClient, type TableDetailItem, type SchemaSummary } from "@/lib/api-client";
import { useWorkspace } from "@/providers/workspace-provider";

export default function TableInspectorPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const { currentWorkspace } = useWorkspace();

  const tableId = typeof params?.tableId === "string" ? params.tableId : "";
  const paramSchemaId = searchParams.get("schemaId") || "";
  const snapshotId = searchParams.get("snapshotId") || "";

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [table, setTable] = useState<TableDetailItem | null>(null);
  const [schema, setSchema] = useState<SchemaSummary | null>(null);
  const [activeSchemaId, setActiveSchemaId] = useState<string>(paramSchemaId);

  useEffect(() => {
    let isCancelled = false;

    async function loadTableMetadata() {
      if (!currentWorkspace?.id || !tableId) return;

      try {
        setLoading(true);
        setError(null);

        let targetSchemaId = activeSchemaId;

        // If schemaId is not provided in query, find the schema containing this table
        if (!targetSchemaId) {
          const schemas = await apiClient.listSchemas(currentWorkspace.id);
          for (const s of schemas) {
            try {
              const res = await apiClient.getTableDetail(s.schema_id, tableId, currentWorkspace.id);
              if (res) {
                targetSchemaId = s.schema_id;
                setActiveSchemaId(targetSchemaId);
                if (!isCancelled) {
                  setTable(res);
                  setSchema(s);
                }
                break;
              }
            } catch {
              // Check next schema
            }
          }
        }

        if (!targetSchemaId) {
          throw new Error(`Table '${tableId}' was not found in any authorized schema.`);
        }

        // Fetch detail if not already resolved above
        const [tableDetail, schemaSummary] = await Promise.all([
          apiClient.getTableDetail(targetSchemaId, tableId, currentWorkspace.id),
          apiClient.getSchemaSummary(targetSchemaId, currentWorkspace.id),
        ]);

        if (!isCancelled) {
          setTable(tableDetail);
          setSchema(schemaSummary);
        }
      } catch (err: unknown) {
        if (!isCancelled) {
          setError(err instanceof Error ? err.message : "Failed to load table inspection metadata");
        }
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    }

    loadTableMetadata();
    return () => {
      isCancelled = true;
    };
  }, [tableId, activeSchemaId, currentWorkspace?.id]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <RefreshCw className="w-8 h-8 animate-spin text-indigo-500" />
        <div className="text-center">
          <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
            Inspecting Database Table...
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Loading verified canonical columns, keys, constraints, and dependencies.
          </p>
        </div>
      </div>
    );
  }

  if (error || !table) {
    return (
      <div className="max-w-xl mx-auto my-12 p-6 rounded-2xl border border-rose-200 dark:border-rose-900/50 bg-rose-50/50 dark:bg-rose-950/20 text-center space-y-4">
        <div className="p-3 bg-rose-100 dark:bg-rose-900/50 text-rose-600 rounded-full w-fit mx-auto">
          <AlertCircle className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
            Table Metadata Unavailable
          </h2>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
            {error || `Table with ID '${tableId}' could not be inspected.`}
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

  const viewModel: TableInspectorViewModel = {
    table,
    schemaId: activeSchemaId,
    databaseName: schema?.database_name,
    sourceEngine: schema?.engine || schema?.source_engine,
    completeness: schema?.completeness,
    isSnapshot: Boolean(snapshotId),
    snapshotFingerprint: snapshotId,
  };

  return <TableInspector viewModel={viewModel} />;
}
