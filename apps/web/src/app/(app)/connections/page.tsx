"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Database,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  ExternalLink,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  Layers,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { useWorkspace } from "@/providers/workspace-provider";
import {
  apiClient,
  ConnectionItem,
  ConnectionTestResult,
  DeraApiError,
} from "@/lib/api-client";

export default function ConnectionsPage() {
  const router = useRouter();
  const { currentWorkspace, loading: workspaceLoading } = useWorkspace();
  const [connections, setConnections] = React.useState<ConnectionItem[]>([]);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);
  const [searchQuery, setSearchQuery] = React.useState<string>("");
  const [engineFilter, setEngineFilter] = React.useState<string>("all");

  // Testing & Inspection State
  const [testingId, setTestingId] = React.useState<string | null>(null);
  const [testResult, setTestResult] = React.useState<{ id: string; result: ConnectionTestResult } | null>(null);
  const [inspectingId, setInspectingId] = React.useState<string | null>(null);

  // Deletion State
  const [deletingConnection, setDeletingConnection] = React.useState<ConnectionItem | null>(null);
  const [deleteLoading, setDeleteLoading] = React.useState<boolean>(false);

  const loadConnections = React.useCallback(async () => {
    if (!currentWorkspace?.id) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.listConnections(currentWorkspace.id);
      setConnections(data);
    } catch (err) {
      if (err instanceof DeraApiError) {
        setError(err.problem.detail || err.message);
      } else {
        setError("Failed to load workspace connections.");
      }
    } finally {
      setLoading(false);
    }
  }, [currentWorkspace?.id]);

  React.useEffect(() => {
    loadConnections();
  }, [loadConnections]);

  const handleTestConnection = async (conn: ConnectionItem) => {
    if (!currentWorkspace?.id) return;
    setTestingId(conn.id);
    setTestResult(null);
    try {
      const res = await apiClient.testConnection(currentWorkspace.id, conn.id);
      setTestResult({ id: conn.id, result: res });
      await loadConnections();
    } catch (err) {
      setTestResult({
        id: conn.id,
        result: {
          success: false,
          latency_ms: 0,
          engine: conn.engine,
          error_code: "TEST_FAILED",
          error_message: err instanceof Error ? err.message : "Connection diagnostic probe failed.",
        },
      });
    } finally {
      setTestingId(null);
    }
  };

  const handleInspectSchema = async (conn: ConnectionItem) => {
    if (!currentWorkspace?.id) return;
    setInspectingId(conn.id);
    try {
      const schemaSummary = await apiClient.inspectConnection(currentWorkspace.id, conn.id);
      router.push(`/schemas/${schemaSummary.schema_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to inspect schema.");
      setInspectingId(null);
    }
  };

  const handleDelete = async () => {
    if (!currentWorkspace?.id || !deletingConnection) return;
    setDeleteLoading(true);
    try {
      await apiClient.deleteConnection(currentWorkspace.id, deletingConnection.id);
      setDeletingConnection(null);
      await loadConnections();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete connection.");
    } finally {
      setDeleteLoading(false);
    }
  };

  const filteredConnections = React.useMemo(() => {
    return connections.filter((conn) => {
      const matchesSearch =
        conn.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        conn.database.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (conn.host && conn.host.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchesEngine = engineFilter === "all" || conn.engine === engineFilter;
      return matchesSearch && matchesEngine;
    });
  }, [connections, searchQuery, engineFilter]);

  const getEngineBadge = (engine: string, provider: string) => {
    if (provider === "supabase") {
      return <Badge variant="success">Supabase</Badge>;
    }
    switch (engine) {
      case "postgresql":
        return <Badge variant="default">PostgreSQL</Badge>;
      case "mysql":
        return <Badge className="bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200">MySQL</Badge>;
      case "mariadb":
        return <Badge className="bg-sky-100 text-sky-900 dark:bg-sky-950 dark:text-sky-200">MariaDB</Badge>;
      case "sqlite":
        return <Badge variant="secondary">SQLite (Contained)</Badge>;
      default:
        return <Badge variant="outline">{engine}</Badge>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "connected":
        return (
          <Badge variant="success" className="gap-1">
            <CheckCircle2 className="w-3 h-3" /> Connected
          </Badge>
        );
      case "failed":
        return (
          <Badge variant="destructive" className="gap-1">
            <XCircle className="w-3 h-3" /> Failed
          </Badge>
        );
      case "testing":
        return (
          <Badge variant="warning" className="gap-1">
            <Clock className="w-3 h-3 animate-spin" /> Testing...
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="gap-1 text-slate-500">
            <AlertCircle className="w-3 h-3" /> Not Tested
          </Badge>
        );
    }
  };

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
              Database Connections
            </h1>
            <Badge variant="outline" className="text-xs">
              {currentWorkspace ? currentWorkspace.name : "Personal Workspace"}
            </Badge>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Manage target database connections with strict read-only enforcement and credential isolation.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadConnections}
            disabled={loading}
            aria-label="Refresh connections list"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Link href="/connections/new">
            <Button size="sm" className="gap-1.5">
              <Plus className="w-4 h-4" />
              Add Connection
            </Button>
          </Link>
        </div>
      </div>

      {/* Global Error Banner */}
      {error && (
        <ErrorState
          title="Connection Service Error"
          description={error}
          onRetry={loadConnections}
        />
      )}

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <Input
            placeholder="Search connections or databases..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-9 text-xs"
            aria-label="Search connections"
          />
        </div>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <span className="text-xs text-slate-500">Engine:</span>
          <select
            value={engineFilter}
            onChange={(e) => setEngineFilter(e.target.value)}
            className="h-9 px-2 text-xs border border-slate-200 dark:border-slate-800 rounded-md bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-1 focus:ring-slate-900 dark:focus:ring-slate-100"
            aria-label="Filter by database engine"
          >
            <option value="all">All Engines</option>
            <option value="postgresql">PostgreSQL</option>
            <option value="sqlite">SQLite</option>
            <option value="mysql">MySQL</option>
            <option value="mariadb">MariaDB</option>
          </select>
        </div>
      </div>

      {/* Loading Skeletons */}
      {loading && connections.length === 0 && (
        <div className="space-y-4">
          <Skeleton className="h-28 w-full rounded-lg" />
          <Skeleton className="h-28 w-full rounded-lg" />
        </div>
      )}

      {/* Empty State */}
      {!loading && connections.length === 0 && (
        <EmptyState
          title="No Database Connections"
          description="Connect an authorized PostgreSQL, Supabase, MySQL, MariaDB, or contained SQLite instance to extract schemas and analyze relationships."
          icon={<Database className="w-8 h-8 text-slate-400" />}
          action={
            <Link href="/connections/new">
              <Button size="sm" className="gap-1.5 mt-2">
                <Plus className="w-4 h-4" />
                Add First Connection
              </Button>
            </Link>
          }
        />
      )}

      {/* No Search Results */}
      {!loading && connections.length > 0 && filteredConnections.length === 0 && (
        <div className="text-center py-12 border border-dashed border-slate-200 dark:border-slate-800 rounded-lg">
          <p className="text-xs text-slate-500">No database connections match your search query or filter.</p>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setSearchQuery("");
              setEngineFilter("all");
            }}
            className="mt-2 text-xs"
          >
            Clear Filters
          </Button>
        </div>
      )}

      {/* Connections List Cards */}
      <div className="grid grid-cols-1 gap-4">
        {filteredConnections.map((conn) => {
          const isTesting = testingId === conn.id;
          const isInspecting = inspectingId === conn.id;
          const currentTest = testResult?.id === conn.id ? testResult.result : null;

          return (
            <Card
              key={conn.id}
              className="hover:border-slate-300 dark:hover:border-slate-700 transition-colors"
            >
              <CardContent className="p-5">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  {/* Connection Details */}
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <Link
                        href={`/connections/${conn.id}`}
                        className="text-base font-semibold text-slate-900 dark:text-slate-100 hover:underline flex items-center gap-1.5"
                      >
                        {conn.name}
                        <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                      </Link>
                      {getEngineBadge(conn.engine, conn.provider)}
                      {getStatusBadge(isTesting ? "testing" : conn.status)}
                    </div>

                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
                      <span>
                        <strong className="font-medium text-slate-700 dark:text-slate-300">Database:</strong>{" "}
                        <code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded font-mono text-[11px]">
                          {conn.database}
                        </code>
                      </span>
                      {conn.host && (
                        <span>
                          <strong className="font-medium text-slate-700 dark:text-slate-300">Host:</strong>{" "}
                          <code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded font-mono text-[11px]">
                            {conn.host}:{conn.port || "default"}
                          </code>
                        </span>
                      )}
                      <span>
                        <strong className="font-medium text-slate-700 dark:text-slate-300">TLS:</strong>{" "}
                        {conn.ssl_mode}
                      </span>
                      {conn.last_tested_at && (
                        <span>
                          <strong className="font-medium text-slate-700 dark:text-slate-300">Last Tested:</strong>{" "}
                          {new Date(conn.last_tested_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions Bar */}
                  <div className="flex items-center gap-2 shrink-0">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleTestConnection(conn)}
                      disabled={isTesting || isInspecting}
                      className="text-xs gap-1"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 ${isTesting ? "animate-spin" : ""}`} />
                      Test
                    </Button>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => handleInspectSchema(conn)}
                      disabled={isTesting || isInspecting}
                      className="text-xs gap-1"
                    >
                      <Layers className={`w-3.5 h-3.5 ${isInspecting ? "animate-spin" : ""}`} />
                      Inspect Schema
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setDeletingConnection(conn)}
                      disabled={isTesting || isInspecting}
                      className="text-xs text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/40 p-2"
                      aria-label={`Delete ${conn.name}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {/* Inline Test Feedback */}
                {currentTest && (
                  <div
                    className={`mt-4 p-3 rounded-md text-xs border ${
                      currentTest.success
                        ? "bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-300 dark:border-emerald-800"
                        : "bg-red-50 text-red-800 border-red-200 dark:bg-red-950/30 dark:text-red-300 dark:border-red-800"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {currentTest.success ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-600" />
                      )}
                      <span className="font-medium">
                        {currentTest.success
                          ? `Connection verified in ${currentTest.latency_ms}ms${
                              currentTest.server_version ? ` (Server: ${currentTest.server_version})` : ""
                            }`
                          : `Connection probe failed: ${currentTest.error_message || "Unknown error"}`}
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Delete Confirmation Modal */}
      <Dialog
        open={Boolean(deletingConnection)}
        onOpenChange={(open) => !open && setDeletingConnection(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Database Connection</DialogTitle>
            <DialogDescription>
              Are you sure you want to remove connection &ldquo;{deletingConnection?.name}&rdquo;?
              This will not modify your target database. Existing schema snapshots will remain preserved.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDeletingConnection(null)}
              disabled={deleteLoading}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={handleDelete}
              disabled={deleteLoading}
            >
              {deleteLoading ? "Deleting..." : "Delete Connection"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
