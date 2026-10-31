"use client";

/**
 * DERA — Accessible Dependency Table Component
 * WCAG 2.2 AA compliant tabular view providing complete non-visual dependency inspection.
 */

import React, { useMemo } from "react";
import Link from "next/link";
import { ExternalLink, CheckCircle, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { DependencyAnalysisResponse, RelationshipGraphResponse, CycleReportResponse } from "@/lib/api-client";

interface AccessibleDependencyTableProps {
  analysis: DependencyAnalysisResponse;
  relationships: RelationshipGraphResponse;
  cycles: CycleReportResponse;
  schemaId: string;
  onSelectTable?: (tableId: string) => void;
}

export function AccessibleDependencyTable({
  analysis,
  relationships,
  cycles,
  schemaId,
  onSelectTable,
}: AccessibleDependencyTableProps) {
  // Pre-calculate lookup maps
  const nodeNameMap = useMemo(() => {
    const map = new Map<string, { name: string; namespace: string }>();
    relationships.nodes.forEach((n) => map.set(n.table_id, { name: n.name, namespace: n.namespace }));
    return map;
  }, [relationships.nodes]);

  const creationOrderIndexMap = useMemo(() => {
    const map = new Map<string, number>();
    analysis.creation_order.forEach((tid, idx) => map.set(tid, idx + 1));
    return map;
  }, [analysis.creation_order]);

  const levelIndexMap = useMemo(() => {
    const map = new Map<string, number>();
    analysis.levels.forEach((lvl) => {
      lvl.table_ids.forEach((tid) => map.set(tid, lvl.level_index));
    });
    return map;
  }, [analysis.levels]);

  const cycleMap = useMemo(() => {
    const map = new Map<string, string>(); // tableId -> sccId
    cycles.components.forEach((scc) => {
      if (scc.is_cyclic) {
        scc.table_ids.forEach((tid) => map.set(tid, scc.scc_id));
      }
    });
    return map;
  }, [cycles.components]);

  const { outgoingMap, incomingMap } = useMemo(() => {
    const out = new Map<string, string[]>();
    const inc = new Map<string, string[]>();

    relationships.edges.forEach((e) => {
      if (!out.has(e.source_table_id)) out.set(e.source_table_id, []);
      out.get(e.source_table_id)!.push(e.target_table_name);

      if (!inc.has(e.target_table_id)) inc.set(e.target_table_id, []);
      inc.get(e.target_table_id)!.push(e.source_table_name);
    });

    return { outgoingMap: out, incomingMap: inc };
  }, [relationships.edges]);

  const sortedNodes = useMemo(() => {
    return [...relationships.nodes].sort((a, b) => {
      const idxA = creationOrderIndexMap.get(a.table_id) || 99999;
      const idxB = creationOrderIndexMap.get(b.table_id) || 99999;
      return idxA - idxB;
    });
  }, [relationships.nodes, creationOrderIndexMap]);

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden bg-white dark:bg-slate-900 shadow-sm">
        <table className="w-full text-left border-collapse text-xs">
          <caption className="sr-only">
            Complete database schema dependency catalog and execution orderings
          </caption>
          <thead>
            <tr className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-[11px] font-semibold text-slate-600 dark:text-slate-300">
              <th scope="col" className="px-4 py-3 w-16">
                Order
              </th>
              <th scope="col" className="px-4 py-3">
                Table Name
              </th>
              <th scope="col" className="px-4 py-3 w-28">
                Migration Level
              </th>
              <th scope="col" className="px-4 py-3">
                Dependencies (Prerequisites)
              </th>
              <th scope="col" className="px-4 py-3">
                Dependents (Referenced By)
              </th>
              <th scope="col" className="px-4 py-3 w-28">
                Cycle Status
              </th>
              <th scope="col" className="px-4 py-3 w-20 text-right">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {sortedNodes.map((node) => {
              const orderIdx = creationOrderIndexMap.get(node.table_id);
              const levelIdx = levelIndexMap.get(node.table_id);
              const sccId = cycleMap.get(node.table_id);
              const outgoing = outgoingMap.get(node.table_id) || [];
              const incoming = incomingMap.get(node.table_id) || [];

              return (
                <tr
                  key={node.table_id}
                  className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors"
                >
                  <td className="px-4 py-3 font-mono text-slate-500 font-semibold">
                    #{orderIdx || "—"}
                  </td>
                  <td className="px-4 py-3">
                    <div className="space-y-0.5">
                      <div className="font-mono font-semibold text-slate-900 dark:text-slate-100">
                        {node.name}
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {node.namespace}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant="outline" className="font-mono text-[10px]">
                      Level {levelIdx ?? "—"}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    {outgoing.length > 0 ? (
                      <div className="flex flex-wrap gap-1 font-mono text-[11px]">
                        {outgoing.map((p) => (
                          <span
                            key={p}
                            className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                          >
                            {p}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-slate-400 text-[11px]">None (Root)</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {incoming.length > 0 ? (
                      <div className="flex flex-wrap gap-1 font-mono text-[11px]">
                        {incoming.map((c) => (
                          <span
                            key={c}
                            className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                          >
                            {c}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-slate-400 text-[11px]">None</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {sccId ? (
                      <Badge variant="outline" className="text-[10px] bg-rose-500/10 text-rose-700 dark:text-rose-300 border-rose-500/30 gap-1 font-mono">
                        <AlertTriangle className="w-2.5 h-2.5" />
                        In Cycle
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-[10px] text-emerald-700 dark:text-emerald-400 border-emerald-500/30 gap-1 font-mono">
                        <CheckCircle className="w-2.5 h-2.5" />
                        Acyclic
                      </Badge>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      href={`/tables/${encodeURIComponent(node.table_id)}?schemaId=${encodeURIComponent(schemaId)}`}
                      className="inline-flex items-center gap-1 text-indigo-600 dark:text-indigo-400 hover:underline font-medium text-[11px]"
                    >
                      Inspect <ExternalLink className="w-3 h-3" />
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
