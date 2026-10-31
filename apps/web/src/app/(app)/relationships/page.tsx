"use client";

import * as React from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import {
  AlertCircle,
  Database,
  ExternalLink,
  Layers,
  Network,
  RefreshCw,
  Search,
  Table as TableIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { useWorkspace } from "@/providers/workspace-provider";
import {
  apiClient,
  DeraApiError,
  RelationshipGraphResponse,
  SchemaSummary,
} from "@/lib/api-client";
import {
  AccessibleGraphTable,
  buildGraphModel,
  CanvasEdge,
  CanvasNode,
  computeDeterministicLayout,
  ERCanvas,
  ERToolbar,
  GraphBounds,
  GraphFilters,
  GraphLegend,
  GraphStatus,
  RelationshipDetails,
  ViewportState,
} from "@/components/er-diagram";

function RelationshipsStudioContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const schemaIdParam = searchParams.get("schemaId");

  const { currentWorkspace, loading: workspaceLoading } = useWorkspace();

  // Schemas list & selection
  const [schemas, setSchemas] = React.useState<SchemaSummary[]>([]);
  const [selectedSchemaId, setSelectedSchemaId] = React.useState<string | null>(schemaIdParam);
  const [loadingSchemas, setLoadingSchemas] = React.useState<boolean>(true);

  // Graph data & states
  const [rawGraph, setRawGraph] = React.useState<RelationshipGraphResponse | null>(null);
  const [loadingGraph, setLoadingGraph] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string | null>(null);

  // Rendered models & layout
  const [nodes, setNodes] = React.useState<CanvasNode[]>([]);
  const [edges, setEdges] = React.useState<CanvasEdge[]>([]);
  const [bounds, setBounds] = React.useState<GraphBounds>({
    minX: 0,
    minY: 0,
    maxX: 0,
    maxY: 0,
    width: 0,
    height: 0,
  });

  // Viewport & UI controls
  const [viewport, setViewport] = React.useState<ViewportState>({ x: 40, y: 40, zoom: 0.9 });
  const [orientation, setOrientation] = React.useState<"LR" | "TB">("LR");
  const [viewMode, setViewMode] = React.useState<"canvas" | "table">("canvas");
  const [showLegend, setShowLegend] = React.useState<boolean>(false);
  const [showFilters, setShowFilters] = React.useState<boolean>(true);

  // Search & Filtering
  const [searchQuery, setSearchQuery] = React.useState<string>("");
  const [selectedNamespace, setSelectedNamespace] = React.useState<string | null>(null);
  const [hideIsolated, setHideIsolated] = React.useState<boolean>(false);

  // Selection
  const [selectedNodeId, setSelectedNodeId] = React.useState<string | null>(null);
  const [selectedEdgeId, setSelectedEdgeId] = React.useState<string | null>(null);

  // Load available schemas in current workspace
  React.useEffect(() => {
    if (!currentWorkspace?.id) {
      setLoadingSchemas(false);
      return;
    }

    let isMounted = true;
    async function fetchSchemas() {
      setLoadingSchemas(true);
      try {
        const list = await apiClient.listSchemas(currentWorkspace!.id);
        if (isMounted) {
          setSchemas(list);
          if (list.length > 0 && !selectedSchemaId) {
            setSelectedSchemaId(list[0].schema_id);
          }
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load schemas");
        }
      } finally {
        if (isMounted) setLoadingSchemas(false);
      }
    }

    fetchSchemas();
    return () => {
      isMounted = false;
    };
  }, [currentWorkspace?.id]);

  // Synchronize URL search params with selectedSchemaId
  React.useEffect(() => {
    if (schemaIdParam && schemaIdParam !== selectedSchemaId) {
      setSelectedSchemaId(schemaIdParam);
    }
  }, [schemaIdParam]);

  // Load Graph and Table Columns for selected schema
  const loadGraphData = React.useCallback(async () => {
    if (!currentWorkspace?.id || !selectedSchemaId) {
      setRawGraph(null);
      setNodes([]);
      setEdges([]);
      return;
    }

    setLoadingGraph(true);
    setError(null);
    setSelectedNodeId(null);
    setSelectedEdgeId(null);

    try {
      // Fetch verified relationship graph
      const graphData = await apiClient.getSchemaRelationships(
        selectedSchemaId,
        currentWorkspace.id
      );

      // Fetch table summaries to enrich node columns
      let tableSummaries: Array<{ table_id: string; columns?: any[] }> = [];
      try {
        const tableListRes = await apiClient.listTables(selectedSchemaId, currentWorkspace.id, {
          limit: 100,
        });
        tableSummaries = tableListRes.tables || [];
      } catch {
        // Fall back gracefully to graph node names if table listing fails
      }

      // Enrich raw nodes with column lists if available
      const enrichedNodes = graphData.nodes.map((n) => {
        const matched = tableSummaries.find((t) => t.table_id === n.table_id);
        return {
          table_id: n.table_id,
          namespace: n.namespace,
          name: n.name,
          columns: matched?.columns || [],
        };
      });

      setRawGraph(graphData);

      // Process models and layout
      const model = buildGraphModel({
        database_name: graphData.database_name,
        engine: graphData.engine,
        nodes: enrichedNodes,
        edges: graphData.edges,
      });

      const { positionedNodes, bounds: computedBounds } = computeDeterministicLayout(
        model.nodes,
        model.edges,
        {
          orientation,
          rankSeparation: 100,
          nodeSeparation: 40,
        }
      );

      setNodes(positionedNodes);
      setEdges(model.edges);
      setBounds(computedBounds);

      // Center initial viewport
      setViewport({ x: 50, y: 50, zoom: 0.85 });
    } catch (err) {
      if (err instanceof DeraApiError) {
        setError(err.problem.detail || err.message);
      } else {
        setError("Failed to retrieve foreign key relationship graph.");
      }
    } finally {
      setLoadingGraph(false);
    }
  }, [currentWorkspace?.id, selectedSchemaId, orientation]);

  React.useEffect(() => {
    loadGraphData();
  }, [loadGraphData]);

  // Manual Node Repositioning
  const handleUpdateNodePosition = React.useCallback((nodeId: string, x: number, y: number) => {
    setNodes((prevNodes) =>
      prevNodes.map((n) => (n.id === nodeId ? { ...n, x, y } : n))
    );
  }, []);

  // Filter nodes & edges
  const filteredNodes = React.useMemo(() => {
    const q = searchQuery.toLowerCase().trim();

    return nodes.filter((node) => {
      // 1. Namespace filter
      if (selectedNamespace && node.namespace !== selectedNamespace) {
        return false;
      }

      // 2. Hide isolated tables filter
      if (hideIsolated) {
        const hasEdges = edges.some(
          (e) => e.source_table_id === node.id || e.target_table_id === node.id
        );
        if (!hasEdges) return false;
      }

      // 3. Search query filter
      if (q) {
        const matchName = node.name.toLowerCase().includes(q);
        const matchNamespace = node.namespace.toLowerCase().includes(q);
        const matchCols = (node.columns || []).some((c) => c.name.toLowerCase().includes(q));
        const matchFk = edges.some(
          (e) =>
            (e.source_table_id === node.id || e.target_table_id === node.id) &&
            e.constraint_name.toLowerCase().includes(q)
        );

        if (!matchName && !matchNamespace && !matchCols && !matchFk) {
          return false;
        }
      }

      return true;
    });
  }, [nodes, edges, searchQuery, selectedNamespace, hideIsolated]);

  const visibleNodeIds = React.useMemo(
    () => new Set(filteredNodes.map((n) => n.id)),
    [filteredNodes]
  );

  const filteredEdges = React.useMemo(() => {
    return edges.filter(
      (e) => visibleNodeIds.has(e.source_table_id) && visibleNodeIds.has(e.target_table_id)
    );
  }, [edges, visibleNodeIds]);

  // Available namespaces for dropdown
  const availableNamespaces = React.useMemo(() => {
    return Array.from(new Set(nodes.map((n) => n.namespace))).sort();
  }, [nodes]);

  // Viewport action handlers
  const handleZoomIn = () => {
    setViewport((v) => ({ ...v, zoom: Math.min(v.zoom * 1.15, 2.5) }));
  };

  const handleZoomOut = () => {
    setViewport((v) => ({ ...v, zoom: Math.max(v.zoom * 0.85, 0.2) }));
  };

  const handleResetView = () => {
    setViewport({ x: 40, y: 40, zoom: 1.0 });
  };

  const handleFitToView = () => {
    if (filteredNodes.length === 0) return;
    const minX = Math.min(...filteredNodes.map((n) => n.x));
    const minY = Math.min(...filteredNodes.map((n) => n.y));
    const maxX = Math.max(...filteredNodes.map((n) => n.x + n.width));
    const maxY = Math.max(...filteredNodes.map((n) => n.y + n.height));

    const graphWidth = maxX - minX + 100;
    const graphHeight = maxY - minY + 100;

    // Default container estimation
    const containerWidth = typeof window !== "undefined" ? window.innerWidth - 320 : 1000;
    const containerHeight = typeof window !== "undefined" ? window.innerHeight - 200 : 700;

    const scaleX = containerWidth / graphWidth;
    const scaleY = containerHeight / graphHeight;
    const zoom = Math.min(Math.max(Math.min(scaleX, scaleY), 0.2), 1.2);

    const x = (containerWidth - graphWidth * zoom) / 2 - minX * zoom;
    const y = (containerHeight - graphHeight * zoom) / 2 - minY * zoom;

    setViewport({ x: Math.round(x), y: Math.round(y), zoom });
  };

  const handleAutoLayout = () => {
    if (!rawGraph) return;
    const { positionedNodes, bounds: computedBounds } = computeDeterministicLayout(
      nodes,
      edges,
      {
        orientation,
        rankSeparation: 100,
        nodeSeparation: 40,
      }
    );
    setNodes(positionedNodes);
    setBounds(computedBounds);
  };

  const handleToggleOrientation = () => {
    const next = orientation === "LR" ? "TB" : "LR";
    setOrientation(next);
  };

  // Keyboard shortcuts
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if typing in an input
      if ((e.target as HTMLElement).tagName === "INPUT") return;

      if (e.key === "+" || e.key === "=") {
        e.preventDefault();
        handleZoomIn();
      } else if (e.key === "-" || e.key === "_") {
        e.preventDefault();
        handleZoomOut();
      } else if (e.key === "f" || e.key === "F") {
        e.preventDefault();
        handleFitToView();
      } else if (e.key === "r" || e.key === "R") {
        e.preventDefault();
        handleResetView();
      } else if (e.key === "Escape") {
        setSelectedNodeId(null);
        setSelectedEdgeId(null);
        setShowLegend(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [filteredNodes]);

  // Selected item references for details panel
  const selectedNode = React.useMemo(() => {
    return nodes.find((n) => n.id === selectedNodeId) || null;
  }, [nodes, selectedNodeId]);

  const selectedEdge = React.useMemo(() => {
    return edges.find((e) => e.id === selectedEdgeId) || null;
  }, [edges, selectedEdgeId]);

  // Counts for status
  const compositeCount = edges.filter((e) => e.is_composite).length;
  const selfLoopCount = edges.filter((e) => e.is_self_loop).length;

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] -m-6 overflow-hidden bg-slate-950">
      {/* Top Header & Schema Selector Bar */}
      <div className="px-4 py-3 bg-slate-900 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Network className="w-5 h-5 text-blue-500" />
            <h1 className="text-base font-bold text-slate-100 tracking-tight">
              ER Diagram Canvas
            </h1>
          </div>

          {/* Schema Selector Dropdown */}
          {schemas.length > 0 && (
            <div className="flex items-center gap-1.5 ml-2">
              <span className="text-xs text-slate-400">Schema:</span>
              <select
                value={selectedSchemaId || ""}
                onChange={(e) => {
                  setSelectedSchemaId(e.target.value);
                  router.push(`/relationships?schemaId=${e.target.value}`);
                }}
                className="h-8 px-2 bg-slate-950 border border-slate-700 rounded text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 font-medium"
                aria-label="Select database schema"
              >
                {schemas.map((s) => (
                  <option key={s.schema_id} value={s.schema_id}>
                    {s.database_name} ({s.engine} • {s.table_count} tables)
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {selectedSchemaId && (
            <Button asChild variant="outline" size="sm" className="h-8 text-xs gap-1.5 bg-slate-800 border-slate-700 text-slate-200 hover:bg-slate-700">
              <Link href={`/schemas/${selectedSchemaId}`}>
                <TableIcon className="w-3.5 h-3.5 text-blue-400" />
                <span>Open Schema Explorer</span>
              </Link>
            </Button>
          )}

          <Button
            variant="ghost"
            size="sm"
            onClick={loadGraphData}
            disabled={loadingGraph}
            className="h-8 w-8 p-0 text-slate-400 hover:text-slate-200"
            aria-label="Refresh relationship graph"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingGraph ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Graph Status Summary Bar */}
      {rawGraph && (
        <GraphStatus
          databaseName={rawGraph.database_name}
          engine={rawGraph.engine}
          nodeCount={rawGraph.node_count}
          edgeCount={rawGraph.edge_count}
          compositeCount={compositeCount}
          selfLoopCount={selfLoopCount}
        />
      )}

      {/* Workspace Loading / Error / Empty States */}
      {loadingSchemas || loadingGraph ? (
        <div className="flex-1 p-6 space-y-4">
          <Skeleton className="h-10 w-full bg-slate-900" />
          <Skeleton className="h-96 w-full bg-slate-900" />
        </div>
      ) : error ? (
        <div className="p-6">
          <ErrorState
            title="Failed to Load ER Diagram"
            description={error}
            onRetry={loadGraphData}
          />
        </div>
      ) : schemas.length === 0 ? (
        <div className="p-6">
          <EmptyState
            title="No Schemas Available"
            description="Inspect a database connection to generate verified canonical schemas and relationship graphs."
            icon={<Database className="w-8 h-8 text-slate-500" />}
            action={
              <Button asChild variant="primary" size="sm">
                <Link href="/connections">Manage Connections</Link>
              </Button>
            }
          />
        </div>
      ) : nodes.length === 0 ? (
        <div className="p-6">
          <EmptyState
            title="No Tables or Relationships Found"
            description="The selected schema does not contain any verified tables or foreign keys."
            icon={<Network className="w-8 h-8 text-slate-500" />}
          />
        </div>
      ) : (
        /* Main Interactive Studio Canvas & Panels */
        <div className="flex-1 relative flex overflow-hidden">
          {/* Main View Area */}
          <div className="flex-1 relative flex flex-col h-full overflow-hidden">
            {/* Floating Top Controls Bar (Toolbar & Filters) */}
            <div className="absolute top-3 left-3 right-3 z-10 flex flex-col gap-2 pointer-events-none">
              <div className="pointer-events-auto">
                <ERToolbar
                  zoom={viewport.zoom}
                  orientation={orientation}
                  viewMode={viewMode}
                  showLegend={showLegend}
                  showFilters={showFilters}
                  onZoomIn={handleZoomIn}
                  onZoomOut={handleZoomOut}
                  onFitToView={handleFitToView}
                  onResetView={handleResetView}
                  onAutoLayout={handleAutoLayout}
                  onToggleOrientation={handleToggleOrientation}
                  onToggleViewMode={() => setViewMode((m) => (m === "canvas" ? "table" : "canvas"))}
                  onToggleLegend={() => setShowLegend((l) => !l)}
                  onToggleFilters={() => setShowFilters((f) => !f)}
                />
              </div>

              {showFilters && (
                <div className="pointer-events-auto">
                  <GraphFilters
                    searchQuery={searchQuery}
                    selectedNamespace={selectedNamespace}
                    hideIsolated={hideIsolated}
                    availableNamespaces={availableNamespaces}
                    totalNodes={nodes.length}
                    filteredNodes={filteredNodes.length}
                    onSearchChange={setSearchQuery}
                    onNamespaceChange={setSelectedNamespace}
                    onToggleHideIsolated={() => setHideIsolated((h) => !h)}
                    onClearFilters={() => {
                      setSearchQuery("");
                      setSelectedNamespace(null);
                      setHideIsolated(false);
                    }}
                  />
                </div>
              )}
            </div>

            {/* Floating Legend Overlay */}
            {showLegend && (
              <div className="absolute top-24 right-4 z-20">
                <GraphLegend onClose={() => setShowLegend(false)} />
              </div>
            )}

            {/* View Mode Switching */}
            {viewMode === "canvas" ? (
              <ERCanvas
                nodes={filteredNodes}
                edges={filteredEdges}
                selectedNodeId={selectedNodeId}
                selectedEdgeId={selectedEdgeId}
                viewport={viewport}
                onViewportChange={setViewport}
                onSelectNode={setSelectedNodeId}
                onSelectEdge={setSelectedEdgeId}
                onUpdateNodePosition={handleUpdateNodePosition}
              />
            ) : (
              <AccessibleGraphTable
                nodes={filteredNodes}
                edges={filteredEdges}
                onSelectNode={(id) => {
                  setSelectedNodeId(id);
                  setSelectedEdgeId(null);
                }}
                onSelectEdge={(id) => {
                  setSelectedEdgeId(id);
                  setSelectedNodeId(null);
                }}
              />
            )}
          </div>

          {/* Collapsible Details Panel */}
          {(selectedNode || selectedEdge) && (
            <RelationshipDetails
              selectedNode={selectedNode}
              selectedEdge={selectedEdge}
              allNodes={nodes}
              allEdges={edges}
              schemaId={selectedSchemaId || ""}
              onSelectNode={(id) => {
                setSelectedNodeId(id);
                setSelectedEdgeId(null);
              }}
              onSelectEdge={(id) => {
                setSelectedEdgeId(id);
                setSelectedNodeId(null);
              }}
              onClose={() => {
                setSelectedNodeId(null);
                setSelectedEdgeId(null);
              }}
            />
          )}
        </div>
      )}
    </div>
  );
}

export default function RelationshipsPage() {
  return (
    <React.Suspense
      fallback={
        <div className="p-6 space-y-4">
          <Skeleton className="h-10 w-full bg-slate-900" />
          <Skeleton className="h-96 w-full bg-slate-900" />
        </div>
      }
    >
      <RelationshipsStudioContent />
    </React.Suspense>
  );
}
