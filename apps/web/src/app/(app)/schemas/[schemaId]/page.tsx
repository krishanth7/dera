"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  Database,
  ExternalLink,
  Eye,
  FileText,
  Filter,
  Folder,
  FolderOpen,
  Key,
  Layers,
  Link as LinkIcon,
  List,
  Network,
  RefreshCw,
  Search,
  ShieldCheck,
  Table as TableIcon,
  TableProperties,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useWorkspace } from "@/providers/workspace-provider";
import {
  apiClient,
  DeraApiError,
  NamespaceItem,
  SchemaSummary,
  TableDetailItem,
  TableSummaryItem,
} from "@/lib/api-client";

export default function SchemaExplorerStudioPage() {
  const params = useParams<{ schemaId: string }>();
  const router = useRouter();
  const { currentWorkspace, loading: workspaceLoading } = useWorkspace();
  const schemaId = params.schemaId;

  // Schema state
  const [schemaSummary, setSchemaSummary] = React.useState<SchemaSummary | null>(null);
  const [namespaces, setNamespaces] = React.useState<NamespaceItem[]>([]);
  const [tables, setTables] = React.useState<TableSummaryItem[]>([]);
  const [loadingSchema, setLoadingSchema] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);

  // Tree & Selection state
  const [selectedNamespace, setSelectedNamespace] = React.useState<string>("all");
  const [selectedTableId, setSelectedTableId] = React.useState<string | null>(null);
  const [selectedTableDetail, setSelectedTableDetail] = React.useState<TableDetailItem | null>(null);
  const [loadingTableDetail, setLoadingTableDetail] = React.useState<boolean>(false);
  const [tableDetailError, setTableDetailError] = React.useState<string | null>(null);

  // Expanded Tree Nodes
  const [expandedNamespaces, setExpandedNamespaces] = React.useState<Record<string, boolean>>({
    public: true,
  });

  // Search & Filtering
  const [searchQuery, setSearchQuery] = React.useState<string>("");
  const [typeFilter, setTypeFilter] = React.useState<string>("all");

  // Load Schema, Namespaces, and Tables
  const loadSchemaData = React.useCallback(async () => {
    if (!currentWorkspace?.id || !schemaId) return;
    setLoadingSchema(true);
    setError(null);
    try {
      const [summary, nsList, tblList] = await Promise.all([
        apiClient.getSchemaSummary(schemaId, currentWorkspace.id),
        apiClient.listNamespaces(schemaId, currentWorkspace.id),
        apiClient.listTables(schemaId, currentWorkspace.id, { limit: 500 }),
      ]);
      setSchemaSummary(summary);
      setNamespaces(nsList);
      setTables(tblList.tables);

      // Auto-expand namespaces
      const initialExpanded: Record<string, boolean> = {};
      nsList.forEach((n) => {
        initialExpanded[n.name] = true;
      });
      setExpandedNamespaces(initialExpanded);
    } catch (err) {
      if (err instanceof DeraApiError) {
        setError(err.problem.detail || err.message);
      } else {
        setError("Failed to load schema representation.");
      }
    } finally {
      setLoadingSchema(false);
    }
  }, [currentWorkspace?.id, schemaId]);

  React.useEffect(() => {
    loadSchemaData();
  }, [loadSchemaData]);

  // Load Table Detail when a table is selected
  const loadTableDetail = React.useCallback(
    async (tableId: string) => {
      if (!currentWorkspace?.id || !schemaId) return;
      setLoadingTableDetail(true);
      setTableDetailError(null);
      try {
        const detail = await apiClient.getTableDetail(schemaId, tableId, currentWorkspace.id);
        setSelectedTableDetail(detail);
      } catch (err) {
        if (err instanceof DeraApiError) {
          setTableDetailError(err.problem.detail || err.message);
        } else {
          setTableDetailError("Failed to load table details.");
        }
      } finally {
        setLoadingTableDetail(false);
      }
    },
    [currentWorkspace?.id, schemaId]
  );

  React.useEffect(() => {
    if (selectedTableId) {
      loadTableDetail(selectedTableId);
    } else {
      setSelectedTableDetail(null);
    }
  }, [selectedTableId, loadTableDetail]);

  const toggleNamespace = (nsName: string) => {
    setExpandedNamespaces((prev) => ({
      ...prev,
      [nsName]: !prev[nsName],
    }));
  };

  // Filtered Tables
  const filteredTables = React.useMemo(() => {
    return tables.filter((t) => {
      const matchesSearch =
        t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.namespace.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesNamespace =
        selectedNamespace === "all" || t.namespace === selectedNamespace;
      const matchesType = typeFilter === "all" || t.table_type === typeFilter;
      return matchesSearch && matchesNamespace && matchesType;
    });
  }, [tables, searchQuery, selectedNamespace, typeFilter]);

  // Group tables by namespace for the tree
  const tablesByNamespace = React.useMemo(() => {
    const map: Record<string, TableSummaryItem[]> = {};
    filteredTables.forEach((t) => {
      if (!map[t.namespace]) map[t.namespace] = [];
      map[t.namespace].push(t);
    });
    return map;
  }, [filteredTables]);

  if (workspaceLoading || loadingSchema) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Skeleton className="h-[600px] w-full rounded-lg" />
          <Skeleton className="h-[600px] md:col-span-3 w-full rounded-lg" />
        </div>
      </div>
    );
  }

  if (error || !schemaSummary) {
    return (
      <div className="space-y-6">
        <Link href="/schemas">
          <Button variant="ghost" size="sm" className="gap-1 text-xs">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Schemas
          </Button>
        </Link>
        <ErrorState
          title="Schema Explorer Error"
          description={error || "Schema catalog could not be retrieved."}
          onRetry={loadSchemaData}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Top Header & Breadcrumb */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-3">
        <div className="flex items-center gap-3">
          <Link href="/schemas">
            <Button variant="ghost" size="sm" className="p-1.5 h-8 text-xs" aria-label="Back to schemas">
              <ArrowLeft className="w-4 h-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Database className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                {schemaSummary.database_name}
              </h1>
              <Badge variant="outline" className="text-[10px] uppercase font-mono">
                {schemaSummary.engine}
              </Badge>
              <Badge
                variant={schemaSummary.completeness === "complete" ? "success" : "warning"}
                className="text-[10px]"
              >
                {schemaSummary.completeness}
              </Badge>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {schemaSummary.table_count} tables, {schemaSummary.namespace_count} namespaces &bull; Source:{" "}
              {schemaSummary.source_engine}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {selectedTableId && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedTableId(null)}
              className="text-xs"
            >
              Schema Overview
            </Button>
          )}
          <Button
            asChild
            variant="outline"
            size="sm"
            className="text-xs gap-1.5"
          >
            <Link href={`/relationships?schemaId=${schemaId}`}>
              <Network className="w-3.5 h-3.5 text-blue-500" />
              <span>View ER Diagram</span>
            </Link>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={loadSchemaData}
            className="text-xs gap-1.5"
            aria-label="Refresh schema metadata"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Split-Pane Explorer Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[640px]">
        {/* Left Navigation Tree (4 cols) */}
        <div className="lg:col-span-4 flex flex-col gap-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3 h-full">
          {/* Tree Search & Filter Header */}
          <div className="space-y-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" />
              <Input
                placeholder="Search tables..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 h-8 text-xs"
                aria-label="Search schema tables"
              />
            </div>
            <div className="flex items-center gap-2">
              <select
                value={selectedNamespace}
                onChange={(e) => setSelectedNamespace(e.target.value)}
                className="w-1/2 h-7 px-2 text-[11px] border border-slate-200 dark:border-slate-800 rounded bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                aria-label="Filter by namespace"
              >
                <option value="all">All Namespaces</option>
                {namespaces.map((ns) => (
                  <option key={ns.namespace_id} value={ns.name}>
                    {ns.name} ({ns.table_count})
                  </option>
                ))}
              </select>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="w-1/2 h-7 px-2 text-[11px] border border-slate-200 dark:border-slate-800 rounded bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                aria-label="Filter by object type"
              >
                <option value="all">All Types</option>
                <option value="TABLE">Tables Only</option>
                <option value="VIEW">Views Only</option>
              </select>
            </div>
          </div>

          <div className="border-t border-slate-100 dark:border-slate-800 my-1" />

          {/* Navigation Tree View */}
          <div
            className="flex-1 overflow-y-auto pr-1 space-y-1 font-mono text-xs"
            role="tree"
            aria-label="Database Schema Tree"
          >
            {Object.keys(tablesByNamespace).length === 0 ? (
              <div className="text-center py-8 text-slate-400 text-xs font-sans">
                No matching tables or views.
              </div>
            ) : (
              Object.entries(tablesByNamespace).map(([nsName, nsTables]) => {
                const isExpanded = expandedNamespaces[nsName] ?? true;
                return (
                  <div key={nsName} className="space-y-0.5" role="treeitem" aria-expanded={isExpanded}>
                    {/* Namespace Node */}
                    <button
                      type="button"
                      onClick={() => toggleNamespace(nsName)}
                      className="w-full flex items-center justify-between px-2 py-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold"
                    >
                      <div className="flex items-center gap-1.5">
                        {isExpanded ? (
                          <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                        )}
                        {isExpanded ? (
                          <FolderOpen className="w-3.5 h-3.5 text-amber-500" />
                        ) : (
                          <Folder className="w-3.5 h-3.5 text-amber-500" />
                        )}
                        <span>{nsName}</span>
                      </div>
                      <Badge variant="outline" className="text-[10px] px-1 py-0">
                        {nsTables.length}
                      </Badge>
                    </button>

                    {/* Tables Children */}
                    {isExpanded && (
                      <div className="pl-4 space-y-0.5 border-l border-slate-200 dark:border-slate-800 ml-2">
                        {nsTables.map((tbl) => {
                          const isSelected = selectedTableId === tbl.table_id;
                          return (
                            <button
                              key={tbl.table_id}
                              type="button"
                              role="treeitem"
                              aria-selected={isSelected}
                              onClick={() => setSelectedTableId(tbl.table_id)}
                              className={`w-full flex items-center justify-between px-2 py-1.5 rounded text-left transition-colors ${
                                isSelected
                                  ? "bg-blue-600 text-white font-medium"
                                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                              }`}
                            >
                              <div className="flex items-center gap-1.5 truncate">
                                {tbl.table_type === "VIEW" ? (
                                  <Eye className={`w-3.5 h-3.5 ${isSelected ? "text-white" : "text-sky-500"}`} />
                                ) : (
                                  <TableIcon className={`w-3.5 h-3.5 ${isSelected ? "text-white" : "text-slate-400"}`} />
                                )}
                                <span className="truncate">{tbl.name}</span>
                              </div>
                              <span
                                className={`text-[10px] px-1 rounded ${
                                  isSelected
                                    ? "bg-blue-700 text-white"
                                    : "bg-slate-100 dark:bg-slate-800 text-slate-500"
                                }`}
                              >
                                {tbl.column_count}c
                              </span>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Main Content Pane (8 cols) */}
        <div className="lg:col-span-8 flex flex-col gap-4">
          {!selectedTableId ? (
            /* Schema Overview Mode */
            <div className="space-y-4">
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-base flex items-center gap-2">
                        <Database className="w-4 h-4 text-slate-500" />
                        Schema Catalog Overview
                      </CardTitle>
                      <CardDescription className="text-xs">
                        High-level metrics and canonical structure for {schemaSummary.database_name}.
                      </CardDescription>
                    </div>
                    <Badge variant="outline" className="font-mono text-xs">
                      {schemaSummary.schema_id}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Metric Tiles */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 text-center">
                      <div className="text-xl font-bold text-slate-900 dark:text-slate-100">
                        {schemaSummary.namespace_count}
                      </div>
                      <div className="text-[11px] text-slate-500 font-medium">Namespaces</div>
                    </div>
                    <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 text-center">
                      <div className="text-xl font-bold text-slate-900 dark:text-slate-100">
                        {schemaSummary.table_count}
                      </div>
                      <div className="text-[11px] text-slate-500 font-medium">Tables</div>
                    </div>
                    <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 text-center">
                      <div className="text-xl font-bold text-slate-900 dark:text-slate-100">
                        {schemaSummary.view_count}
                      </div>
                      <div className="text-[11px] text-slate-500 font-medium">Views</div>
                    </div>
                    <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 text-center">
                      <div className="text-xl font-bold text-slate-900 dark:text-slate-100">
                        {schemaSummary.foreign_key_count}
                      </div>
                      <div className="text-[11px] text-slate-500 font-medium">FK Links</div>
                    </div>
                  </div>

                  {/* Provenance Box */}
                  <div className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/40 space-y-1.5 text-xs">
                    <div className="flex items-center gap-1.5 font-semibold text-slate-800 dark:text-slate-200">
                      <ShieldCheck className="w-4 h-4 text-emerald-600" />
                      Canonical Metadata Provenance
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-slate-600 dark:text-slate-400 text-[11px]">
                      <div>
                        Source Engine: <strong>{schemaSummary.source_engine}</strong>
                      </div>
                      <div>
                        Server Version: <strong>{schemaSummary.source_version || "Reported Live"}</strong>
                      </div>
                      <div>
                        Connector Version: <strong>{schemaSummary.connector_version}</strong>
                      </div>
                      <div>
                        Completeness: <strong>{schemaSummary.completeness}</strong>
                      </div>
                      <div>
                        Collected: <strong>{new Date(schemaSummary.collection_timestamp).toLocaleString()}</strong>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Quick Table Directory */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Database Tables & Views ({filteredTables.length})</CardTitle>
                  <CardDescription className="text-xs">
                    Select any table from the list or the left navigation tree to inspect its columns, constraints, and indexes.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 font-medium">
                          <th className="pb-2">Table Name</th>
                          <th className="pb-2">Namespace</th>
                          <th className="pb-2">Type</th>
                          <th className="pb-2 text-right">Columns</th>
                          <th className="pb-2 text-center">Primary Key</th>
                          <th className="pb-2 text-right">FK Links</th>
                          <th className="pb-2 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono text-[11px]">
                        {filteredTables.map((t) => (
                          <tr key={t.table_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                            <td className="py-2.5 font-semibold text-slate-900 dark:text-slate-100">
                              {t.name}
                            </td>
                            <td className="py-2.5 text-slate-500">{t.namespace}</td>
                            <td className="py-2.5">
                              <Badge variant="outline" className="text-[10px]">
                                {t.table_type}
                              </Badge>
                            </td>
                            <td className="py-2.5 text-right font-bold">{t.column_count}</td>
                            <td className="py-2.5 text-center">
                              {t.has_primary_key ? (
                                <Key className="w-3.5 h-3.5 text-amber-500 inline-block" />
                              ) : (
                                <span className="text-slate-300">&mdash;</span>
                              )}
                            </td>
                            <td className="py-2.5 text-right font-medium">{t.foreign_key_count}</td>
                            <td className="py-2.5 text-right font-sans">
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => setSelectedTableId(t.table_id)}
                                className="h-6 text-[11px] px-2"
                              >
                                Inspect &rarr;
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            /* Table Inspector Mode */
            <div className="space-y-4">
              {loadingTableDetail && (
                <div className="space-y-4">
                  <Skeleton className="h-16 w-full rounded-lg" />
                  <Skeleton className="h-96 w-full rounded-lg" />
                </div>
              )}

              {tableDetailError && (
                <ErrorState
                  title="Table Details Unavailable"
                  description={tableDetailError}
                  onRetry={() => loadTableDetail(selectedTableId)}
                />
              )}

              {!loadingTableDetail && selectedTableDetail && (
                <Card>
                  {/* Table Header */}
                  <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <CardTitle className="text-base font-bold font-mono">
                            {selectedTableDetail.namespace}.{selectedTableDetail.name}
                          </CardTitle>
                          <Badge variant="outline" className="text-[10px]">
                            {selectedTableDetail.table_type}
                          </Badge>
                        </div>
                        <p className="text-xs text-slate-500 font-mono">
                          Object ID: {selectedTableDetail.table_id}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary" className="text-xs gap-1">
                          <List className="w-3 h-3" />
                          {selectedTableDetail.columns.length} Columns
                        </Badge>
                        <Badge variant="secondary" className="text-xs gap-1">
                          <LinkIcon className="w-3 h-3" />
                          {selectedTableDetail.foreign_keys.length} Foreign Keys
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>

                  <CardContent className="pt-4">
                    <Tabs defaultValue="columns">
                      <TabsList className="mb-4">
                        <TabsTrigger value="columns">
                          Columns ({selectedTableDetail.columns.length})
                        </TabsTrigger>
                        <TabsTrigger value="constraints">
                          Constraints (
                          {(selectedTableDetail.primary_key ? 1 : 0) +
                            selectedTableDetail.foreign_keys.length +
                            selectedTableDetail.unique_constraints.length +
                            selectedTableDetail.check_constraints.length}
                          )
                        </TabsTrigger>
                        <TabsTrigger value="indexes">
                          Indexes ({selectedTableDetail.indexes.length})
                        </TabsTrigger>
                        <TabsTrigger value="provenance">
                          Provenance & Quality
                        </TabsTrigger>
                      </TabsList>

                      {/* Columns Tab */}
                      <TabsContent value="columns">
                        <div className="overflow-x-auto rounded border border-slate-200 dark:border-slate-800">
                          <table className="w-full text-left text-xs">
                            <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 font-medium">
                              <tr>
                                <th className="p-2.5">#</th>
                                <th className="p-2.5">Name</th>
                                <th className="p-2.5">Native Type</th>
                                <th className="p-2.5">Canonical Type</th>
                                <th className="p-2.5">Nullable</th>
                                <th className="p-2.5">Default Expression</th>
                                <th className="p-2.5 text-center">PK</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-mono text-[11px]">
                              {selectedTableDetail.columns.map((col) => (
                                <tr key={col.column_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                                  <td className="p-2.5 text-slate-400">{col.ordinal_position}</td>
                                  <td className="p-2.5 font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                                    {col.is_primary_key && (
                                      <Key className="w-3 h-3 text-amber-500 shrink-0" />
                                    )}
                                    {col.name}
                                  </td>
                                  <td className="p-2.5 text-blue-600 dark:text-blue-400 font-semibold">
                                    {col.native_type}
                                  </td>
                                  <td className="p-2.5 text-slate-500">{col.canonical_type}</td>
                                  <td className="p-2.5">
                                    {col.is_nullable ? (
                                      <Badge variant="outline" className="text-[10px] text-slate-500">
                                        YES
                                      </Badge>
                                    ) : (
                                      <Badge variant="secondary" className="text-[10px]">
                                        NO
                                      </Badge>
                                    )}
                                  </td>
                                  <td className="p-2.5 text-slate-500 truncate max-w-xs">
                                    {col.default_expression || <span className="text-slate-300">&mdash;</span>}
                                  </td>
                                  <td className="p-2.5 text-center">
                                    {col.is_primary_key ? (
                                      <Badge variant="warning" className="text-[10px]">
                                        PK
                                      </Badge>
                                    ) : (
                                      <span className="text-slate-300">&mdash;</span>
                                    )}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </TabsContent>

                      {/* Constraints Tab */}
                      <TabsContent value="constraints" className="space-y-4">
                        {/* Primary Key */}
                        <div>
                          <h4 className="text-xs font-semibold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-2">
                            Primary Key
                          </h4>
                          {selectedTableDetail.primary_key ? (
                            <div className="p-3 rounded border border-amber-200 dark:border-amber-900/40 bg-amber-50/40 dark:bg-amber-950/20 text-xs space-y-1">
                              <div className="flex items-center gap-2">
                                <Key className="w-4 h-4 text-amber-600" />
                                <span className="font-mono font-semibold text-slate-900 dark:text-slate-100">
                                  {selectedTableDetail.primary_key.name}
                                </span>
                              </div>
                              <p className="text-slate-600 dark:text-slate-400 text-[11px]">
                                Constrained Columns:{" "}
                                <code className="font-mono font-semibold">
                                  ({selectedTableDetail.primary_key.columns.join(", ")})
                                </code>
                              </p>
                            </div>
                          ) : (
                            <p className="text-xs text-slate-400 italic">No primary key defined on this table.</p>
                          )}
                        </div>

                        {/* Foreign Keys */}
                        <div>
                          <h4 className="text-xs font-semibold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-2">
                            Foreign Key Constraints ({selectedTableDetail.foreign_keys.length})
                          </h4>
                          {selectedTableDetail.foreign_keys.length === 0 ? (
                            <p className="text-xs text-slate-400 italic">No foreign key constraints defined.</p>
                          ) : (
                            <div className="space-y-2">
                              {selectedTableDetail.foreign_keys.map((fk) => (
                                <div
                                  key={fk.constraint_id}
                                  className="p-3 rounded border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs space-y-1.5"
                                >
                                  <div className="flex items-center justify-between">
                                    <span className="font-mono font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                                      <LinkIcon className="w-3.5 h-3.5 text-blue-500" />
                                      {fk.name}
                                    </span>
                                    <div className="flex items-center gap-1 text-[10px]">
                                      {fk.on_delete && <Badge variant="outline">DEL: {fk.on_delete}</Badge>}
                                      {fk.on_update && <Badge variant="outline">UPD: {fk.on_update}</Badge>}
                                    </div>
                                  </div>
                                  <p className="text-[11px] text-slate-600 dark:text-slate-400 font-mono">
                                    ({fk.source_columns.join(", ")}) &rarr; {fk.referenced_table_name} (
                                    {fk.referenced_columns.join(", ")})
                                  </p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Unique Constraints */}
                        {selectedTableDetail.unique_constraints.length > 0 && (
                          <div>
                            <h4 className="text-xs font-semibold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-2">
                              Unique Constraints ({selectedTableDetail.unique_constraints.length})
                            </h4>
                            <div className="space-y-1.5">
                              {selectedTableDetail.unique_constraints.map((u) => (
                                <div
                                  key={u.constraint_id}
                                  className="p-2.5 rounded border border-slate-200 dark:border-slate-800 text-xs font-mono"
                                >
                                  <strong className="text-slate-900 dark:text-slate-100">{u.name}</strong>: (
                                  {u.columns.join(", ")})
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Check Constraints */}
                        {selectedTableDetail.check_constraints.length > 0 && (
                          <div>
                            <h4 className="text-xs font-semibold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-2">
                              Check Constraints ({selectedTableDetail.check_constraints.length})
                            </h4>
                            <div className="space-y-1.5">
                              {selectedTableDetail.check_constraints.map((chk) => (
                                <div
                                  key={chk.constraint_id}
                                  className="p-2.5 rounded border border-slate-200 dark:border-slate-800 text-xs font-mono bg-slate-50/50 dark:bg-slate-800/40"
                                >
                                  <span className="font-semibold text-slate-900 dark:text-slate-100">
                                    {chk.name}:
                                  </span>{" "}
                                  <code className="text-slate-600 dark:text-slate-400">
                                    {chk.raw_expression || "CHECK"}
                                  </code>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </TabsContent>

                      {/* Indexes Tab */}
                      <TabsContent value="indexes">
                        {selectedTableDetail.indexes.length === 0 ? (
                          <p className="text-xs text-slate-400 italic">No secondary indexes declared on this table.</p>
                        ) : (
                          <div className="overflow-x-auto rounded border border-slate-200 dark:border-slate-800">
                            <table className="w-full text-left text-xs font-mono">
                              <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 font-medium">
                                <tr>
                                  <th className="p-2.5">Index Name</th>
                                  <th className="p-2.5">Indexed Columns</th>
                                  <th className="p-2.5">Unique</th>
                                  <th className="p-2.5">Primary</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-[11px]">
                                {selectedTableDetail.indexes.map((idx) => (
                                  <tr key={idx.index_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                                    <td className="p-2.5 font-semibold text-slate-900 dark:text-slate-100">
                                      {idx.name}
                                    </td>
                                    <td className="p-2.5 text-blue-600 dark:text-blue-400">
                                      ({idx.columns.join(", ")})
                                    </td>
                                    <td className="p-2.5">
                                      {idx.is_unique ? (
                                        <Badge variant="success" className="text-[10px]">
                                          UNIQUE
                                        </Badge>
                                      ) : (
                                        <Badge variant="outline" className="text-[10px]">
                                          NON-UNIQUE
                                        </Badge>
                                      )}
                                    </td>
                                    <td className="p-2.5">
                                      {idx.is_primary ? (
                                        <Badge variant="warning" className="text-[10px]">
                                          PRIMARY
                                        </Badge>
                                      ) : (
                                        <span className="text-slate-300">&mdash;</span>
                                      )}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </TabsContent>

                      {/* Provenance Tab */}
                      <TabsContent value="provenance" className="space-y-3">
                        <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/40 text-xs space-y-2">
                          <h4 className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                            <ShieldCheck className="w-4 h-4 text-emerald-600" />
                            Table Level Inspection Provenance
                          </h4>
                          <p className="text-slate-600 dark:text-slate-400">
                            Extracted via authorized DERA Connector without schema inference or LLM hallucination.
                          </p>
                          <dl className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-200 dark:border-slate-800 text-[11px]">
                            <div>
                              <dt className="text-slate-400">Target Schema ID</dt>
                              <dd className="font-mono font-medium">{schemaSummary.schema_id}</dd>
                            </div>
                            <div>
                              <dt className="text-slate-400">Table Canonical ID</dt>
                              <dd className="font-mono font-medium">{selectedTableDetail.table_id}</dd>
                            </div>
                            <div>
                              <dt className="text-slate-400">Source Engine</dt>
                              <dd className="font-medium">{schemaSummary.source_engine}</dd>
                            </div>
                            <div>
                              <dt className="text-slate-400">Collection Timestamp</dt>
                              <dd className="font-medium">
                                {new Date(schemaSummary.collection_timestamp).toLocaleString()}
                              </dd>
                            </div>
                          </dl>
                        </div>
                      </TabsContent>
                    </Tabs>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
