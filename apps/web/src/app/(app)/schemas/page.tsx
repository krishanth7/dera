"use client";

import * as React from "react";
import Link from "next/link";
import {
  ArrowRight,
  Database,
  Layers,
  Plus,
  RefreshCw,
  Search,
  TableProperties,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkspace } from "@/providers/workspace-provider";
import { apiClient, DeraApiError, SchemaSummary } from "@/lib/api-client";

export default function SchemasPage() {
  const { currentWorkspace, loading: workspaceLoading } = useWorkspace();
  const [schemas, setSchemas] = React.useState<SchemaSummary[]>([]);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);
  const [searchQuery, setSearchQuery] = React.useState<string>("");

  const loadSchemas = React.useCallback(async () => {
    if (!currentWorkspace?.id) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.listSchemas(currentWorkspace.id);
      setSchemas(data);
    } catch (err) {
      if (err instanceof DeraApiError) {
        setError(err.problem.detail || err.message);
      } else {
        setError("Failed to load schema representations.");
      }
    } finally {
      setLoading(false);
    }
  }, [currentWorkspace?.id]);

  React.useEffect(() => {
    loadSchemas();
  }, [loadSchemas]);

  const filteredSchemas = React.useMemo(() => {
    return schemas.filter(
      (s) =>
        s.database_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.engine.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [schemas, searchQuery]);

  if (workspaceLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              Schema Explorer
            </h1>
            <Badge variant="outline" className="text-xs">
              {currentWorkspace ? currentWorkspace.name : "Workspace"}
            </Badge>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Browse reverse engineered canonical database catalogs, structural entities, and table definitions.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadSchemas}
            disabled={loading}
            aria-label="Refresh schemas"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Link href="/connections">
            <Button size="sm" className="gap-1.5">
              <Database className="w-4 h-4" />
              Manage Connections
            </Button>
          </Link>
        </div>
      </div>

      {/* Error */}
      {error && (
        <ErrorState
          title="Schema Catalog Unavailable"
          description={error}
          onRetry={loadSchemas}
        />
      )}

      {/* Search */}
      <div className="flex items-center justify-between">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <Input
            placeholder="Search schemas by database name or engine..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-9 text-xs"
            aria-label="Search schemas"
          />
        </div>
      </div>

      {/* Loading */}
      {loading && schemas.length === 0 && (
        <div className="space-y-4">
          <Skeleton className="h-32 w-full rounded-lg" />
          <Skeleton className="h-32 w-full rounded-lg" />
        </div>
      )}

      {/* Empty State */}
      {!loading && schemas.length === 0 && (
        <EmptyState
          title="No Extracted Schemas in Workspace"
          description="Connect a database and run 'Inspect Schema' to reverse engineer its catalog into canonical DERA models."
          icon={<TableProperties className="w-8 h-8 text-slate-400" />}
          action={
            <Link href="/connections">
              <Button size="sm" className="gap-1.5 mt-2">
                <Database className="w-4 h-4" />
                Open Connections
              </Button>
            </Link>
          }
        />
      )}

      {/* Schema Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredSchemas.map((schema) => (
          <Card
            key={schema.schema_id}
            className="hover:border-slate-300 dark:hover:border-slate-700 transition-all flex flex-col justify-between"
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between gap-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Database className="w-4 h-4 text-slate-500" />
                  {schema.database_name}
                </CardTitle>
                <div className="flex items-center gap-1.5">
                  <Badge variant="outline" className="text-[10px] uppercase font-mono">
                    {schema.engine}
                  </Badge>
                  <Badge
                    variant={
                      schema.completeness === "complete"
                        ? "success"
                        : schema.completeness === "partial"
                        ? "warning"
                        : "secondary"
                    }
                    className="text-[10px]"
                  >
                    {schema.completeness}
                  </Badge>
                </div>
              </div>
              <CardDescription className="text-xs">
                Catalog ID: <code className="font-mono">{schema.schema_id}</code>
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Metrics Grid */}
              <div className="grid grid-cols-4 gap-2 text-center p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
                <div>
                  <div className="text-base font-bold text-slate-900 dark:text-slate-100">
                    {schema.namespace_count}
                  </div>
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider">Namespaces</div>
                </div>
                <div>
                  <div className="text-base font-bold text-slate-900 dark:text-slate-100">
                    {schema.table_count}
                  </div>
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider">Tables</div>
                </div>
                <div>
                  <div className="text-base font-bold text-slate-900 dark:text-slate-100">
                    {schema.view_count}
                  </div>
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider">Views</div>
                </div>
                <div>
                  <div className="text-base font-bold text-slate-900 dark:text-slate-100">
                    {schema.foreign_key_count}
                  </div>
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider">FK Links</div>
                </div>
              </div>

              {/* Provenance Footer */}
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 pt-1">
                <span>
                  Source: <strong>{schema.source_engine}</strong>{" "}
                  {schema.source_version && `v${schema.source_version}`}
                </span>
                <Link href={`/schemas/${schema.schema_id}`}>
                  <Button size="sm" variant="outline" className="gap-1 text-xs">
                    Explore Schema
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
