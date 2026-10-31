"use client";

/**
 * DERA — Advanced Schema Search Filters Panel
 * Multi-criteria filtering by object type, namespace, schema, and constraint category.
 */

import React from "react";
import { Filter, RotateCcw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { SearchFiltersState, SearchObjectType } from "./types";
import type { SchemaSummary, NamespaceItem } from "@/lib/api-client";

interface SearchFiltersPanelProps {
  filters: SearchFiltersState;
  onChange: (newFilters: SearchFiltersState) => void;
  schemas: SchemaSummary[];
  namespaces: NamespaceItem[];
}

export function SearchFiltersPanel({
  filters,
  onChange,
  schemas,
  namespaces,
}: SearchFiltersPanelProps) {
  const objectTypes: Array<{ type: SearchObjectType; label: string }> = [
    { type: "all", label: "All Objects" },
    { type: "table", label: "Tables" },
    { type: "view", label: "Views" },
    { type: "column", label: "Columns" },
    { type: "constraint", label: "Constraints" },
    { type: "index", label: "Indexes" },
    { type: "namespace", label: "Namespaces" },
  ];

  const constraintTypes = [
    { value: "", label: "All Constraint Types" },
    { value: "PRIMARY_KEY", label: "Primary Key (PK)" },
    { value: "FOREIGN_KEY", label: "Foreign Key (FK)" },
    { value: "UNIQUE", label: "Unique" },
    { value: "CHECK", label: "Check" },
  ];

  const handleTypeSelect = (type: SearchObjectType) => {
    onChange({ ...filters, objectType: type });
  };

  const handleReset = () => {
    onChange({
      query: filters.query,
      objectType: "all",
      namespace: "",
      constraintType: "",
      completeness: "",
      schemaId: "",
    });
  };

  const hasActiveFilters =
    filters.objectType !== "all" ||
    Boolean(filters.namespace) ||
    Boolean(filters.constraintType) ||
    Boolean(filters.schemaId) ||
    Boolean(filters.completeness);

  return (
    <div className="space-y-4 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm text-xs">
      {/* Object Type Pills */}
      <div>
        <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-2">
          Object Type
        </span>
        <div className="flex flex-wrap gap-1.5">
          {objectTypes.map(({ type, label }) => {
            const isSelected = filters.objectType === type;
            return (
              <button
                key={type}
                type="button"
                onClick={() => handleTypeSelect(type)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                  isSelected
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
                }`}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Selectors Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-slate-100 dark:border-slate-800">
        {/* Schema Selector */}
        <div>
          <label htmlFor="search-schema-select" className="text-[11px] font-medium text-slate-500 block mb-1">
            Schema Scope
          </label>
          <select
            id="search-schema-select"
            value={filters.schemaId}
            onChange={(e) => onChange({ ...filters, schemaId: e.target.value })}
            className="w-full h-8 px-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-xs"
          >
            <option value="">All Authorized Schemas</option>
            {schemas.map((s) => (
              <option key={s.schema_id} value={s.schema_id}>
                {s.database_name} ({s.engine})
              </option>
            ))}
          </select>
        </div>

        {/* Namespace Selector */}
        <div>
          <label htmlFor="search-namespace-select" className="text-[11px] font-medium text-slate-500 block mb-1">
            Namespace
          </label>
          <select
            id="search-namespace-select"
            value={filters.namespace}
            onChange={(e) => onChange({ ...filters, namespace: e.target.value })}
            className="w-full h-8 px-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-xs"
          >
            <option value="">All Namespaces</option>
            {namespaces.map((ns) => (
              <option key={ns.namespace_id || ns.name} value={ns.name}>
                {ns.name} ({ns.table_count} tables)
              </option>
            ))}
          </select>
        </div>

        {/* Constraint Type Selector (Active if constraint or all selected) */}
        {(filters.objectType === "all" || filters.objectType === "constraint") && (
          <div>
            <label htmlFor="search-constraint-select" className="text-[11px] font-medium text-slate-500 block mb-1">
              Constraint Category
            </label>
            <select
              id="search-constraint-select"
              value={filters.constraintType}
              onChange={(e) => onChange({ ...filters, constraintType: e.target.value })}
              className="w-full h-8 px-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-xs"
            >
              {constraintTypes.map((ct) => (
                <option key={ct.value} value={ct.value}>
                  {ct.label}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Active Filter Indicators & Reset */}
      {hasActiveFilters && (
        <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800 text-xs">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-slate-500">Active filters:</span>
            {filters.objectType !== "all" && (
              <Badge variant="outline" className="text-[10px]">
                type: {filters.objectType}
              </Badge>
            )}
            {filters.namespace && (
              <Badge variant="outline" className="text-[10px]">
                ns: {filters.namespace}
              </Badge>
            )}
            {filters.constraintType && (
              <Badge variant="outline" className="text-[10px]">
                constraint: {filters.constraintType}
              </Badge>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleReset}
            className="h-7 text-xs text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 gap-1"
          >
            <RotateCcw className="w-3 h-3" />
            Reset Filters
          </Button>
        </div>
      )}
    </div>
  );
}
