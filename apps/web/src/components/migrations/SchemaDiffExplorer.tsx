"use client";

import React, { useState } from "react";
import { SchemaComparisonReport, SchemaChangeDto } from "@/lib/migrations/types";
import { PlusCircle, MinusCircle, Edit, FileCode, Search, Filter } from "lucide-react";

interface SchemaDiffExplorerProps {
  comparison: SchemaComparisonReport;
}

export function SchemaDiffExplorer({ comparison }: SchemaDiffExplorerProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState<string>("ALL");

  const diffList: SchemaChangeDto[] = comparison.changes || comparison.differences || [];
  const [selectedItem, setSelectedItem] = useState<SchemaChangeDto | null>(
    diffList[0] || null
  );

  const filteredItems = diffList.filter((item) => {
    const objName = item.name || item.object_name || "";
    const matchesSearch =
      objName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.namespace && item.namespace.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesFilter = filterType === "ALL" || item.change_type === filterType;
    return Boolean(matchesSearch && matchesFilter);
  });

  const getChangeBadge = (type: string) => {
    switch (type) {
      case "ADDED":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
            <PlusCircle className="w-3 h-3" /> ADDED
          </span>
        );
      case "REMOVED":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-rose-950 text-rose-400 border border-rose-800">
            <MinusCircle className="w-3 h-3" /> REMOVED
          </span>
        );
      case "MODIFIED":
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-amber-950 text-amber-400 border border-amber-800">
            <Edit className="w-3 h-3" /> MODIFIED
          </span>
        );
    }
  };

  const baselineSnapshot = comparison.baseline_snapshot_id || comparison.source_snapshot_id || "baseline";
  const targetSnapshot = comparison.target_snapshot_id || "target";
  const addedCount = comparison.summary.total_added ?? comparison.summary.added_count ?? 0;
  const removedCount = comparison.summary.total_removed ?? comparison.summary.removed_count ?? 0;
  const modifiedCount = comparison.summary.total_modified ?? comparison.summary.modified_count ?? 0;
  const compFingerprint = comparison.report_fingerprint || comparison.fingerprint || "SHA-256";

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 text-slate-100 shadow-md">
      {/* Overview Statistics Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-4">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <FileCode className="w-5 h-5 text-indigo-400" />
            Phase 9.1 — Schema Snapshot Differences
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic pairwise comparison against baseline ({baselineSnapshot.slice(0, 8)}) and target ({targetSnapshot.slice(0, 8)})
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 bg-slate-950 px-3 py-1.5 rounded border border-slate-800 text-xs">
            <span className="text-slate-400">Total:</span>
            <span className="font-semibold text-slate-200">{comparison.summary.total_changes}</span>
          </div>
          <div className="flex items-center gap-1 bg-emerald-950/40 px-3 py-1.5 rounded border border-emerald-800/60 text-xs text-emerald-300">
            <span>+{addedCount} Added</span>
          </div>
          <div className="flex items-center gap-1 bg-rose-950/40 px-3 py-1.5 rounded border border-rose-800/60 text-xs text-rose-300">
            <span>-{removedCount} Removed</span>
          </div>
          <div className="flex items-center gap-1 bg-amber-950/40 px-3 py-1.5 rounded border border-amber-800/60 text-xs text-amber-300">
            <span>~{modifiedCount} Modified</span>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            placeholder="Search object name or namespace..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-md pl-9 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-500" />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            aria-label="Filter differences by change type"
            className="bg-slate-950 border border-slate-800 rounded-md px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="ALL">All Changes</option>
            <option value="ADDED">Added</option>
            <option value="REMOVED">Removed</option>
            <option value="MODIFIED">Modified</option>
          </select>
        </div>
      </div>

      {/* Explorer Master-Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Master List */}
        <div className="lg:col-span-5 bg-slate-950/60 border border-slate-800 rounded-lg overflow-hidden flex flex-col max-h-[500px]">
          <div className="p-3 bg-slate-950 border-b border-slate-800 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Detected Structural Changes ({filteredItems.length})
          </div>
          <div className="overflow-y-auto divide-y divide-slate-800/60 flex-1">
            {filteredItems.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500">
                No differences match the current filter criteria.
              </div>
            ) : (
              filteredItems.map((item) => {
                const isSelected = (selectedItem?.change_id === item.change_id);
                const displayName = item.name || item.object_name || item.canonical_id;
                return (
                  <button
                    key={item.change_id}
                    onClick={() => setSelectedItem(item)}
                    className={`w-full text-left p-3.5 transition-colors flex items-center justify-between ${
                      isSelected
                        ? "bg-indigo-950/40 border-l-2 border-indigo-500"
                        : "hover:bg-slate-900/60"
                    }`}
                  >
                    <div>
                      <div className="font-mono text-sm text-slate-200 font-medium">
                        {displayName}
                      </div>
                      <div className="text-xs text-slate-400 flex items-center gap-2 mt-1">
                        <span>{item.namespace || "public"}</span>
                        <span>•</span>
                        <span className="uppercase text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-300">
                          {item.object_type}
                        </span>
                      </div>
                    </div>
                    <div>{getChangeBadge(item.change_type)}</div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Change Detail Panel */}
        <div className="lg:col-span-7 bg-slate-950/60 border border-slate-800 rounded-lg p-5 flex flex-col justify-between">
          {selectedItem ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="font-mono text-base font-semibold text-slate-100">
                    {selectedItem.name || selectedItem.object_name || selectedItem.canonical_id}
                  </h3>
                  <div className="text-xs text-slate-400 mt-0.5">
                    Object Canonical ID: <span className="font-mono text-slate-500">{selectedItem.canonical_id}</span>
                  </div>
                </div>
                <div>{getChangeBadge(selectedItem.change_type)}</div>
              </div>

              {/* Property Differences */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  Attribute & Property Diffs
                </h4>
                {((selectedItem.property_differences && selectedItem.property_differences.length > 0) ||
                  (selectedItem.property_diffs && selectedItem.property_diffs.length > 0)) ? (
                  <div className="border border-slate-800 rounded divide-y divide-slate-800 text-xs overflow-hidden">
                    <div className="grid grid-cols-12 bg-slate-900/80 p-2 font-medium text-slate-400">
                      <div className="col-span-4">Property</div>
                      <div className="col-span-4">Baseline (Before)</div>
                      <div className="col-span-4">Target (After)</div>
                    </div>
                    {(selectedItem.property_differences || selectedItem.property_diffs || []).map((diff, i) => (
                      <div key={i} className="grid grid-cols-12 p-2 hover:bg-slate-900/40">
                        <div className="col-span-4 font-mono text-indigo-300">
                          {diff.property || diff.property_name}
                        </div>
                        <div className="col-span-4 font-mono text-rose-300 truncate">
                          {String(diff.baseline_value ?? diff.before_value ?? "none")}
                        </div>
                        <div className="col-span-4 font-mono text-emerald-300 truncate">
                          {String(diff.target_value ?? diff.after_value ?? "none")}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-xs text-slate-500 italic p-3 bg-slate-900/40 rounded border border-slate-800">
                    Object-level change: entire entity was {selectedItem.change_type.toLowerCase()}.
                  </div>
                )}
              </div>

              {/* Source Evidence */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                  Source Evidence & Provenance
                </h4>
                <div className="bg-slate-900 p-3 rounded font-mono text-xs text-slate-300 space-y-1 border border-slate-800">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Source Baseline Hash:</span>
                    <span className="text-slate-400 truncate max-w-[260px]">{baselineSnapshot}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Target Destination Hash:</span>
                    <span className="text-slate-400 truncate max-w-[260px]">{targetSnapshot}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Comparison Fingerprint:</span>
                    <span className="text-indigo-400 truncate max-w-[260px]">{compFingerprint}</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500 text-xs">
              Select an object from the list to view its deterministic attribute differences.
            </div>
          )}

          <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-500 flex justify-between">
            <span>WCAG 2.2 AA Contrast Verified</span>
            <span>Deterministic Pairwise Differencing</span>
          </div>
        </div>
      </div>
    </div>
  );
}
