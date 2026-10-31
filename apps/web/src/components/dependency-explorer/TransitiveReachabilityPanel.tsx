"use client";

/**
 * DERA — Transitive Reachability & Impact Analysis Panel
 * Computes upstream prerequisites and downstream blast radius with depth controls.
 */

import React, { useState, useMemo } from "react";
import Link from "next/link";
import {
  ArrowUpRight,
  ArrowDownLeft,
  Sliders,
  ExternalLink,
  ShieldAlert,
  Layers,
  ArrowRight,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { RelationshipGraphResponse } from "@/lib/api-client";
import type { DependencyDepth } from "./types";

interface TransitiveReachabilityPanelProps {
  relationships: RelationshipGraphResponse;
  schemaId: string;
  selectedTableId: string;
  onSelectTable: (tableId: string) => void;
}

export function TransitiveReachabilityPanel({
  relationships,
  schemaId,
  selectedTableId,
  onSelectTable,
}: TransitiveReachabilityPanelProps) {
  const [depth, setDepth] = useState<DependencyDepth>(2);
  const maxDepthNum = depth === "transitive" ? 999 : depth;

  const nodeMap = useMemo(() => {
    const map = new Map<string, { id: string; name: string; namespace: string }>();
    relationships.nodes.forEach((n) => map.set(n.table_id, { id: n.table_id, name: n.name, namespace: n.namespace }));
    return map;
  }, [relationships.nodes]);

  // Build adjacency lists:
  // In FK graph: child -> parent (child references parent).
  // Upstream (prerequisites): child -> parents
  // Downstream (dependents): parent -> children
  const { upstreamMap, downstreamMap } = useMemo(() => {
    const up = new Map<string, Array<{ targetId: string; constraintName: string }>>();
    const down = new Map<string, Array<{ sourceId: string; constraintName: string }>>();

    relationships.edges.forEach((e) => {
      // up: source depends on target
      if (!up.has(e.source_table_id)) up.set(e.source_table_id, []);
      up.get(e.source_table_id)!.push({ targetId: e.target_table_id, constraintName: e.constraint_name });

      // down: target is referenced by source
      if (!down.has(e.target_table_id)) down.set(e.target_table_id, []);
      down.get(e.target_table_id)!.push({ sourceId: e.source_table_id, constraintName: e.constraint_name });
    });

    return { upstreamMap: up, downstreamMap: down };
  }, [relationships.edges]);

  // Compute bounded BFS reachability
  const { upstreamNodes, downstreamNodes } = useMemo(() => {
    if (!selectedTableId) return { upstreamNodes: [], downstreamNodes: [] };

    // 1. Upstream BFS (Prerequisites)
    const visitedUp = new Map<string, number>(); // tableId -> depth
    const queueUp: Array<{ id: string; d: number }> = [{ id: selectedTableId, d: 0 }];
    visitedUp.set(selectedTableId, 0);

    while (queueUp.length > 0) {
      const { id, d } = queueUp.shift()!;
      if (d >= maxDepthNum) continue;

      const neighbors = upstreamMap.get(id) || [];
      for (const n of neighbors) {
        if (!visitedUp.has(n.targetId)) {
          visitedUp.set(n.targetId, d + 1);
          queueUp.push({ id: n.targetId, d: d + 1 });
        }
      }
    }

    // 2. Downstream BFS (Dependents)
    const visitedDown = new Map<string, number>();
    const queueDown: Array<{ id: string; d: number }> = [{ id: selectedTableId, d: 0 }];
    visitedDown.set(selectedTableId, 0);

    while (queueDown.length > 0) {
      const { id, d } = queueDown.shift()!;
      if (d >= maxDepthNum) continue;

      const neighbors = downstreamMap.get(id) || [];
      for (const n of neighbors) {
        if (!visitedDown.has(n.sourceId)) {
          visitedDown.set(n.sourceId, d + 1);
          queueDown.push({ id: n.sourceId, d: d + 1 });
        }
      }
    }

    const upList = Array.from(visitedUp.entries())
      .filter(([id]) => id !== selectedTableId)
      .map(([id, d]) => ({
        id,
        depth: d,
        name: nodeMap.get(id)?.name || id,
        namespace: nodeMap.get(id)?.namespace || "",
      }))
      .sort((a, b) => a.depth - b.depth || a.name.localeCompare(b.name));

    const downList = Array.from(visitedDown.entries())
      .filter(([id]) => id !== selectedTableId)
      .map(([id, d]) => ({
        id,
        depth: d,
        name: nodeMap.get(id)?.name || id,
        namespace: nodeMap.get(id)?.namespace || "",
      }))
      .sort((a, b) => a.depth - b.depth || a.name.localeCompare(b.name));

    return { upstreamNodes: upList, downstreamNodes: downList };
  }, [selectedTableId, maxDepthNum, upstreamMap, downstreamMap, nodeMap]);

  const selectedNode = nodeMap.get(selectedTableId);

  return (
    <div className="space-y-6">
      {/* Table Selector & Depth Controller */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm text-xs">
        <div className="flex items-center gap-2">
          <label htmlFor="focus-table-select" className="text-slate-500 font-medium whitespace-nowrap">
            Focus Table:
          </label>
          <select
            id="focus-table-select"
            value={selectedTableId}
            onChange={(e) => onSelectTable(e.target.value)}
            className="h-8 px-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 font-mono text-xs text-slate-800 dark:text-slate-200 max-w-xs"
          >
            {relationships.nodes.map((n) => (
              <option key={n.table_id} value={n.table_id}>
                {n.namespace}.{n.name}
              </option>
            ))}
          </select>
        </div>

        {/* Depth Pills */}
        <div className="flex items-center gap-1.5">
          <span className="text-slate-500 font-medium flex items-center gap-1 mr-1">
            <Sliders className="w-3.5 h-3.5" />
            Traversal Depth:
          </span>
          {([1, 2, 3, "transitive"] as const).map((d) => (
            <button
              key={String(d)}
              type="button"
              onClick={() => setDepth(d)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                depth === d
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
              }`}
            >
              {d === "transitive" ? "Full Transitive" : `${d} Level${d > 1 ? "s" : ""}`}
            </button>
          ))}
        </div>
      </div>

      {/* Selected Table Summary & Impact Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs space-y-1">
          <span className="text-slate-500 font-medium text-[11px] uppercase block">
            Target Entity
          </span>
          <div className="font-mono font-bold text-sm text-slate-900 dark:text-slate-100">
            {selectedNode?.namespace}.{selectedNode?.name}
          </div>
          <div className="pt-1">
            <Link
              href={`/tables/${encodeURIComponent(selectedTableId)}?schemaId=${encodeURIComponent(schemaId)}`}
              className="text-indigo-600 dark:text-indigo-400 hover:underline inline-flex items-center gap-1"
            >
              Inspect Table Metadata <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
        </div>

        <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs space-y-1">
          <span className="text-slate-500 font-medium text-[11px] uppercase block">
            Upstream Prerequisites
          </span>
          <div className="font-mono font-bold text-lg text-blue-600 dark:text-blue-400">
            {upstreamNodes.length} tables
          </div>
          <div className="text-slate-500 text-[11px]">
            Must exist before &ldquo;{selectedNode?.name}&rdquo;
          </div>
        </div>

        <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs space-y-1">
          <span className="text-slate-500 font-medium text-[11px] uppercase block">
            Downstream Blast Radius
          </span>
          <div className="font-mono font-bold text-lg text-rose-600 dark:text-rose-400">
            {downstreamNodes.length} tables
          </div>
          <div className="text-slate-500 text-[11px]">
            Impacted if &ldquo;{selectedNode?.name}&rdquo; is modified
          </div>
        </div>
      </div>

      {/* 2 Columns: Upstream vs Downstream Reachability */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Upstream Prerequisites */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ArrowUpRight className="w-4 h-4 text-blue-500" />
              <h3 className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                Upstream Prerequisites ({upstreamNodes.length})
              </h3>
            </div>
            <span className="text-[11px] text-slate-400 font-mono">
              Depth &le; {depth === "transitive" ? "&infin;" : depth}
            </span>
          </div>

          {upstreamNodes.length > 0 ? (
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 divide-y divide-slate-100 dark:divide-slate-800 text-xs">
              {upstreamNodes.map((n) => (
                <div
                  key={n.id}
                  className="px-4 py-2.5 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/40"
                >
                  <div className="flex items-center gap-2.5">
                    <Badge variant="outline" className="font-mono text-[10px] w-12 text-center justify-center">
                      d={n.depth}
                    </Badge>
                    <button
                      type="button"
                      onClick={() => onSelectTable(n.id)}
                      className="font-mono font-medium text-slate-800 dark:text-slate-200 hover:text-indigo-600 hover:underline"
                    >
                      {n.namespace}.{n.name}
                    </button>
                  </div>
                  <Link
                    href={`/tables/${encodeURIComponent(n.id)}?schemaId=${encodeURIComponent(schemaId)}`}
                    className="p-1 rounded text-slate-400 hover:text-slate-700"
                    title="Inspect table"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </Link>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 rounded-xl border border-dashed border-slate-200 dark:border-slate-800 text-center text-xs text-slate-500">
              No upstream prerequisites at selected depth.
            </div>
          )}
        </div>

        {/* Downstream Blast Radius */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ArrowDownLeft className="w-4 h-4 text-rose-500" />
              <h3 className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                Downstream Dependents ({downstreamNodes.length})
              </h3>
            </div>
            <span className="text-[11px] text-slate-400 font-mono">
              Depth &le; {depth === "transitive" ? "&infin;" : depth}
            </span>
          </div>

          {downstreamNodes.length > 0 ? (
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 divide-y divide-slate-100 dark:divide-slate-800 text-xs">
              {downstreamNodes.map((n) => (
                <div
                  key={n.id}
                  className="px-4 py-2.5 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/40"
                >
                  <div className="flex items-center gap-2.5">
                    <Badge variant="outline" className="font-mono text-[10px] w-12 text-center justify-center text-rose-600 border-rose-500/30">
                      d={n.depth}
                    </Badge>
                    <button
                      type="button"
                      onClick={() => onSelectTable(n.id)}
                      className="font-mono font-medium text-slate-800 dark:text-slate-200 hover:text-indigo-600 hover:underline"
                    >
                      {n.namespace}.{n.name}
                    </button>
                  </div>
                  <Link
                    href={`/tables/${encodeURIComponent(n.id)}?schemaId=${encodeURIComponent(schemaId)}`}
                    className="p-1 rounded text-slate-400 hover:text-slate-700"
                    title="Inspect table"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </Link>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 rounded-xl border border-dashed border-slate-200 dark:border-slate-800 text-center text-xs text-slate-500">
              No downstream dependents at selected depth.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
