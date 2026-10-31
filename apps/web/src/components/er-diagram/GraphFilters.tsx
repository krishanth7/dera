"use client";

import * as React from "react";
import { Search, X, Filter } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface GraphFiltersProps {
  searchQuery: string;
  selectedNamespace: string | null;
  hideIsolated: boolean;
  availableNamespaces: string[];
  totalNodes: number;
  filteredNodes: number;
  onSearchChange: (query: string) => void;
  onNamespaceChange: (namespace: string | null) => void;
  onToggleHideIsolated: () => void;
  onClearFilters: () => void;
}

export const GraphFilters: React.FC<GraphFiltersProps> = ({
  searchQuery,
  selectedNamespace,
  hideIsolated,
  availableNamespaces,
  totalNodes,
  filteredNodes,
  onSearchChange,
  onNamespaceChange,
  onToggleHideIsolated,
  onClearFilters,
}) => {
  const hasActiveFilters = searchQuery !== "" || selectedNamespace !== null || hideIsolated;

  return (
    <div className="flex flex-wrap items-center gap-3 p-3 bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-lg text-xs text-slate-300">
      {/* Search Input */}
      <div className="relative flex-1 min-w-[200px]">
        <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
        <Input
          type="text"
          placeholder="Search tables, columns, constraints..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="h-8 pl-8 pr-7 bg-slate-950 border-slate-800 text-xs text-slate-200 placeholder:text-slate-500 focus-visible:ring-1 focus-visible:ring-blue-500"
        />
        {searchQuery && (
          <button
            onClick={() => onSearchChange("")}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
            aria-label="Clear search"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Namespace Filter */}
      {availableNamespaces.length > 1 && (
        <div className="flex items-center gap-1.5">
          <span className="text-slate-400">Namespace:</span>
          <select
            value={selectedNamespace || ""}
            onChange={(e) => onNamespaceChange(e.target.value || null)}
            className="h-8 px-2 bg-slate-950 border border-slate-800 rounded text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
            aria-label="Filter by namespace"
          >
            <option value="">All Namespaces</option>
            {availableNamespaces.map((ns) => (
              <option key={ns} value={ns}>
                {ns}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Hide Isolated Tables Toggle */}
      <label className="flex items-center gap-2 cursor-pointer select-none text-slate-300 hover:text-slate-100">
        <input
          type="checkbox"
          checked={hideIsolated}
          onChange={onToggleHideIsolated}
          className="rounded border-slate-700 bg-slate-950 text-blue-600 focus:ring-blue-500 w-3.5 h-3.5"
        />
        <span>Hide isolated tables</span>
      </label>

      {/* Filter status & clear action */}
      <div className="flex items-center gap-2 ml-auto">
        <span className="text-slate-400 font-mono">
          {filteredNodes} of {totalNodes} tables
        </span>
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearFilters}
            className="h-7 px-2 text-xs text-slate-400 hover:text-slate-100"
          >
            Reset
          </Button>
        )}
      </div>
    </div>
  );
};
