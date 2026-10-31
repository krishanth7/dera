"use client";

import * as React from "react";
import { CanvasEdge, CanvasNode } from "./types";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Key, Layers, Table as TableIcon } from "lucide-react";

interface AccessibleGraphTableProps {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  onSelectNode: (nodeId: string) => void;
  onSelectEdge: (edgeId: string) => void;
}

export const AccessibleGraphTable: React.FC<AccessibleGraphTableProps> = ({
  nodes,
  edges,
  onSelectNode,
  onSelectEdge,
}) => {
  return (
    <div className="w-full h-full overflow-y-auto p-4 bg-slate-950 text-slate-200">
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <TableIcon className="w-5 h-5 text-blue-400" />
            Accessible Relationship Directory
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Tabular representation of all verified database entities and foreign key constraints for screen-reader and keyboard accessibility.
          </p>
        </div>

        {/* Foreign Key Constraints Table */}
        <section aria-labelledby="heading-fk-table" className="space-y-3">
          <h3 id="heading-fk-table" className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            Foreign Key Constraints ({edges.length})
          </h3>

          <div className="border border-slate-800 rounded-lg overflow-x-auto bg-slate-900/60">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-900 border-b border-slate-800 text-slate-400">
                  <th scope="col" className="p-3 font-semibold">Constraint Name</th>
                  <th scope="col" className="p-3 font-semibold">Referencing (Child)</th>
                  <th scope="col" className="p-3 font-semibold">Child Columns</th>
                  <th scope="col" className="p-3 font-semibold text-center">→</th>
                  <th scope="col" className="p-3 font-semibold">Referenced (Parent)</th>
                  <th scope="col" className="p-3 font-semibold">Parent Columns</th>
                  <th scope="col" className="p-3 font-semibold">On Delete</th>
                  <th scope="col" className="p-3 font-semibold">On Update</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 font-mono">
                {edges.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="p-6 text-center text-slate-500 italic">
                      No foreign key relationships in this schema.
                    </td>
                  </tr>
                ) : (
                  edges.map((edge) => (
                    <tr
                      key={edge.id}
                      className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                      onClick={() => onSelectEdge(edge.id)}
                      tabIndex={0}
                      role="row"
                      aria-label={`Constraint ${edge.constraint_name} from ${edge.source_table_name} to ${edge.target_table_name}`}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          onSelectEdge(edge.id);
                        }
                      }}
                    >
                      <td className="p-3 font-medium text-blue-400 break-all">
                        {edge.constraint_name}
                        {edge.is_composite && (
                          <Badge variant="outline" className="ml-2 text-[9px] bg-blue-950 border-blue-800 text-blue-300">
                            Composite
                          </Badge>
                        )}
                        {edge.is_self_loop && (
                          <Badge variant="outline" className="ml-2 text-[9px] bg-purple-950 border-purple-800 text-purple-300">
                            Self-Loop
                          </Badge>
                        )}
                      </td>
                      <td className="p-3 text-slate-300">{edge.source_table_name}</td>
                      <td className="p-3 text-blue-300">({edge.source_columns.join(", ")})</td>
                      <td className="p-3 text-center text-slate-500">→</td>
                      <td className="p-3 text-slate-300">{edge.target_table_name}</td>
                      <td className="p-3 text-emerald-300">({edge.target_columns.join(", ")})</td>
                      <td className="p-3 text-slate-400">{edge.on_delete || "NO ACTION"}</td>
                      <td className="p-3 text-slate-400">{edge.on_update || "NO ACTION"}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* Database Entities (Tables) Table */}
        <section aria-labelledby="heading-entities-table" className="space-y-3">
          <h3 id="heading-entities-table" className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <TableIcon className="w-4 h-4 text-blue-400" />
            Database Tables ({nodes.length})
          </h3>

          <div className="border border-slate-800 rounded-lg overflow-x-auto bg-slate-900/60">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-900 border-b border-slate-800 text-slate-400">
                  <th scope="col" className="p-3 font-semibold">Namespace</th>
                  <th scope="col" className="p-3 font-semibold">Table Name</th>
                  <th scope="col" className="p-3 font-semibold">Column Count</th>
                  <th scope="col" className="p-3 font-semibold">Primary Key</th>
                  <th scope="col" className="p-3 font-semibold">Outgoing FKs</th>
                  <th scope="col" className="p-3 font-semibold">Incoming FKs</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 font-mono">
                {nodes.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-6 text-center text-slate-500 italic">
                      No tables found in this schema.
                    </td>
                  </tr>
                ) : (
                  nodes.map((node) => {
                    const outgoing = edges.filter((e) => e.source_table_id === node.id);
                    const incoming = edges.filter((e) => e.target_table_id === node.id);
                    const pkCols = node.columns.filter((c) => c.is_primary_key).map((c) => c.name);

                    return (
                      <tr
                        key={node.id}
                        className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                        onClick={() => onSelectNode(node.id)}
                        tabIndex={0}
                        role="row"
                        aria-label={`Table ${node.namespace}.${node.name}`}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.preventDefault();
                            onSelectNode(node.id);
                          }
                        }}
                      >
                        <td className="p-3 text-slate-400">{node.namespace}</td>
                        <td className="p-3 font-medium text-slate-100">{node.name}</td>
                        <td className="p-3 text-slate-300">{node.columns.length}</td>
                        <td className="p-3">
                          {pkCols.length > 0 ? (
                            <span className="text-amber-300">({pkCols.join(", ")})</span>
                          ) : (
                            <span className="text-slate-600 italic">None</span>
                          )}
                        </td>
                        <td className="p-3 text-blue-300">{outgoing.length}</td>
                        <td className="p-3 text-emerald-300">{incoming.length}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
};
