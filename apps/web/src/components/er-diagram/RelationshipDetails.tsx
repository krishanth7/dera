"use client";

import * as React from "react";
import Link from "next/link";
import {
  X,
  ArrowRight,
  Database,
  Key,
  ShieldCheck,
  ExternalLink,
  Table as TableIcon,
  Layers,
  ArrowUpRight,
  ArrowDownLeft,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CanvasEdge, CanvasNode } from "./types";

interface RelationshipDetailsProps {
  selectedNode: CanvasNode | null;
  selectedEdge: CanvasEdge | null;
  allNodes: CanvasNode[];
  allEdges: CanvasEdge[];
  schemaId: string;
  onSelectNode: (nodeId: string) => void;
  onSelectEdge: (edgeId: string) => void;
  onClose: () => void;
}

export const RelationshipDetails: React.FC<RelationshipDetailsProps> = ({
  selectedNode,
  selectedEdge,
  allNodes,
  allEdges,
  schemaId,
  onSelectNode,
  onSelectEdge,
  onClose,
}) => {
  if (!selectedNode && !selectedEdge) return null;

  return (
    <aside
      aria-label="Relationship and entity details"
      className="w-80 md:w-96 bg-slate-900/95 backdrop-blur-md border-l border-slate-800 h-full flex flex-col shadow-2xl z-20 overflow-hidden"
    >
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {selectedEdge ? (
            <>
              <Layers className="w-4 h-4 text-blue-400" />
              <h2 className="text-sm font-semibold text-slate-100 truncate">
                Relationship Details
              </h2>
            </>
          ) : (
            <>
              <TableIcon className="w-4 h-4 text-emerald-400" />
              <h2 className="text-sm font-semibold text-slate-100 truncate">
                Table Entity Details
              </h2>
            </>
          )}
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-200 p-1 rounded-md"
          aria-label="Close details panel"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5 text-xs text-slate-300">
        {selectedEdge && (
          <div className="space-y-4">
            {/* Constraint Title & Type */}
            <div>
              <div className="text-[11px] text-slate-500 font-mono">FOREIGN KEY CONSTRAINT</div>
              <div className="text-sm font-mono font-bold text-slate-100 mt-0.5 break-all">
                {selectedEdge.constraint_name}
              </div>
              <div className="flex gap-1.5 mt-2">
                {selectedEdge.is_composite && (
                  <Badge variant="outline" className="text-[10px] bg-blue-950/40 border-blue-800 text-blue-300">
                    Composite ({selectedEdge.source_columns.length} columns)
                  </Badge>
                )}
                {selectedEdge.is_self_loop && (
                  <Badge variant="outline" className="text-[10px] bg-purple-950/40 border-purple-800 text-purple-300">
                    Self-Referencing
                  </Badge>
                )}
                {selectedEdge.is_parallel && (
                  <Badge variant="outline" className="text-[10px] bg-slate-800 border-slate-700 text-slate-300">
                    Parallel FK #{selectedEdge.parallel_index + 1} of {selectedEdge.parallel_total}
                  </Badge>
                )}
              </div>
            </div>

            {/* Referencing (Source) -> Referenced (Target) Tables */}
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-[10px] text-slate-500">REFERENCING (CHILD)</div>
                  <button
                    onClick={() => onSelectNode(selectedEdge.source_table_id)}
                    className="font-mono font-medium text-blue-400 hover:underline"
                  >
                    {selectedEdge.source_table_name}
                  </button>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-500" />
                <div className="text-right">
                  <div className="text-[10px] text-slate-500">REFERENCED (PARENT)</div>
                  <button
                    onClick={() => onSelectNode(selectedEdge.target_table_id)}
                    className="font-mono font-medium text-emerald-400 hover:underline"
                  >
                    {selectedEdge.target_table_name}
                  </button>
                </div>
              </div>
            </div>

            {/* Ordered Column Pair Mapping */}
            <div>
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                Column Mapping
              </div>
              <div className="border border-slate-800 rounded-lg overflow-hidden bg-slate-950">
                <table className="w-full text-left font-mono">
                  <thead>
                    <tr className="bg-slate-900 border-b border-slate-800 text-slate-400 text-[10px]">
                      <th className="py-1.5 px-3">Child Column</th>
                      <th className="py-1.5 px-2 text-center">→</th>
                      <th className="py-1.5 px-3">Parent Column</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-900">
                    {selectedEdge.column_pairs.map((pair, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/40">
                        <td className="py-2 px-3 text-blue-300 font-medium">{pair.source_column}</td>
                        <td className="py-2 px-2 text-center text-slate-500">→</td>
                        <td className="py-2 px-3 text-emerald-300 font-medium">{pair.target_column}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Referential Actions */}
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-500">ON DELETE</div>
                <div className="font-mono font-semibold text-slate-200 mt-0.5">
                  {selectedEdge.on_delete || "NO ACTION"}
                </div>
              </div>
              <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-500">ON UPDATE</div>
                <div className="font-mono font-semibold text-slate-200 mt-0.5">
                  {selectedEdge.on_update || "NO ACTION"}
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedNode && !selectedEdge && (
          <div className="space-y-4">
            {/* Table Name & Namespace */}
            <div>
              <div className="text-[11px] text-slate-500 font-mono uppercase">{selectedNode.namespace}</div>
              <div className="text-base font-bold text-slate-100 font-mono mt-0.5">
                {selectedNode.name}
              </div>
              <div className="flex gap-1.5 mt-2">
                <Badge variant="outline" className="text-[10px] bg-slate-800 border-slate-700 text-slate-300">
                  {selectedNode.columns.length} columns
                </Badge>
                {selectedNode.has_primary_key && (
                  <Badge variant="outline" className="text-[10px] bg-amber-950/40 border-amber-800 text-amber-300">
                    Primary Key Defined
                  </Badge>
                )}
              </div>
            </div>

            {/* Link to Schema Explorer Table Inspector */}
            <Button asChild variant="outline" size="sm" className="w-full text-xs gap-1.5 bg-slate-950 border-slate-800 hover:bg-slate-800">
              <Link href={`/schemas/${schemaId}?table=${selectedNode.id}`}>
                <ExternalLink className="w-3.5 h-3.5" />
                <span>View Full Table in Explorer</span>
              </Link>
            </Button>

            {/* Columns Preview */}
            <div>
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                Columns ({selectedNode.columns.length})
              </div>
              <div className="border border-slate-800 rounded-lg max-h-56 overflow-y-auto bg-slate-950 divide-y divide-slate-900 font-mono">
                {selectedNode.columns.map((col) => (
                  <div key={col.name} className="px-3 py-1.5 flex items-center justify-between text-[11px]">
                    <div className="flex items-center gap-1.5 truncate">
                      {col.is_primary_key && (
                        <span className="px-1 py-0.2 rounded text-[8px] font-bold bg-amber-600 text-white">
                          PK
                        </span>
                      )}
                      {col.is_foreign_key && (
                        <span className="px-1 py-0.2 rounded text-[8px] font-bold bg-blue-600 text-white">
                          FK
                        </span>
                      )}
                      <span className={col.is_primary_key ? "text-amber-200 font-medium" : "text-slate-200"}>
                        {col.name}
                      </span>
                    </div>
                    <span className="text-slate-500 text-[10px] ml-2 shrink-0">{col.native_type}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Relationships Connected to this Table */}
            {(() => {
              const outgoing = allEdges.filter((e) => e.source_table_id === selectedNode.id);
              const incoming = allEdges.filter((e) => e.target_table_id === selectedNode.id);

              return (
                <div className="space-y-3">
                  <div>
                    <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                      <ArrowUpRight className="w-3.5 h-3.5 text-blue-400" />
                      References ({outgoing.length})
                    </div>
                    {outgoing.length === 0 ? (
                      <div className="text-slate-500 italic text-[11px]">Does not reference other tables</div>
                    ) : (
                      <div className="space-y-1.5">
                        {outgoing.map((e) => (
                          <button
                            key={e.id}
                            onClick={() => onSelectEdge(e.id)}
                            className="w-full text-left p-2 rounded bg-slate-950 hover:bg-slate-800 border border-slate-800/80 transition-colors"
                          >
                            <div className="font-mono text-blue-400 font-medium">{e.constraint_name}</div>
                            <div className="text-[10px] text-slate-400 mt-0.5">
                              → {e.target_table_name} ({e.target_columns.join(", ")})
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  <div>
                    <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                      <ArrowDownLeft className="w-3.5 h-3.5 text-emerald-400" />
                      Referenced By ({incoming.length})
                    </div>
                    {incoming.length === 0 ? (
                      <div className="text-slate-500 italic text-[11px]">No tables reference this table</div>
                    ) : (
                      <div className="space-y-1.5">
                        {incoming.map((e) => (
                          <button
                            key={e.id}
                            onClick={() => onSelectEdge(e.id)}
                            className="w-full text-left p-2 rounded bg-slate-950 hover:bg-slate-800 border border-slate-800/80 transition-colors"
                          >
                            <div className="font-mono text-emerald-400 font-medium">{e.source_table_name}</div>
                            <div className="text-[10px] text-slate-400 mt-0.5">
                              via {e.constraint_name} ({e.source_columns.join(", ")})
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })()}
          </div>
        )}
      </div>
    </aside>
  );
};
