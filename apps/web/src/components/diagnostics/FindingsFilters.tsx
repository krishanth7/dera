"use client";

import React from "react";
import {
  DiagnosticSeverity,
  FindingFilterState,
} from "@/lib/diagnostics/types";
import { Search, Filter, ArrowUpDown } from "lucide-react";

interface FindingsFiltersProps {
  filterState: FindingFilterState;
  onFilterChange: (newState: FindingFilterState) => void;
  onResetFilters: () => void;
  totalFilteredCount: number;
  totalFindingsCount: number;
  className?: string;
}

export function FindingsFilters({
  filterState,
  onFilterChange,
  onResetFilters,
  totalFilteredCount,
  totalFindingsCount,
  className = "",
}: FindingsFiltersProps) {
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({ ...filterState, searchQuery: e.target.value });
  };

  const handleSeverityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFilterChange({ ...filterState, severityFilter: e.target.value });
  };

  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFilterChange({ ...filterState, categoryFilter: e.target.value });
  };

  const handleSuppressionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFilterChange({
      ...filterState,
      suppressionFilter: e.target.value as FindingFilterState["suppressionFilter"],
    });
  };

  const handleSortByChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFilterChange({
      ...filterState,
      sortBy: e.target.value as FindingFilterState["sortBy"],
    });
  };

  const toggleSortDirection = () => {
    onFilterChange({
      ...filterState,
      sortDirection: filterState.sortDirection === "asc" ? "desc" : "asc",
    });
  };

  return (
    <div
      className={`rounded-lg border border-slate-200 bg-white p-4 shadow-xs dark:border-slate-800 dark:bg-slate-900 ${className}`}
      aria-label="Findings Filters and Search"
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            value={filterState.searchQuery}
            onChange={handleSearchChange}
            placeholder="Search findings by title, rule ID, object (e.g. public.users)..."
            className="w-full rounded-md border border-slate-300 bg-white py-1.5 pl-9 pr-3 text-xs text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:outline-hidden focus:ring-1 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:placeholder-slate-500"
            aria-label="Search diagnostic findings"
          />
        </div>

        {/* Filter Controls Row */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Severity Dropdown */}
          <div className="flex items-center gap-1.5">
            <label
              htmlFor="severity-select"
              className="text-[11px] font-medium text-slate-500 dark:text-slate-400"
            >
              Severity:
            </label>
            <select
              id="severity-select"
              value={filterState.severityFilter}
              onChange={handleSeverityChange}
              className="rounded-md border border-slate-300 bg-white py-1 pl-2 pr-6 text-xs text-slate-900 focus:border-blue-500 focus:outline-hidden dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
              <option value="INFORMATIONAL">Informational</option>
            </select>
          </div>

          {/* Category Dropdown */}
          <div className="flex items-center gap-1.5">
            <label
              htmlFor="category-select"
              className="text-[11px] font-medium text-slate-500 dark:text-slate-400"
            >
              Category:
            </label>
            <select
              id="category-select"
              value={filterState.categoryFilter}
              onChange={handleCategoryChange}
              className="rounded-md border border-slate-300 bg-white py-1 pl-2 pr-6 text-xs text-slate-900 focus:border-blue-500 focus:outline-hidden dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            >
              <option value="ALL">All Categories</option>
              <option value="INDEXES">Indexes</option>
              <option value="CONSTRAINTS">Constraints</option>
              <option value="RELATIONSHIPS">Relationships</option>
              <option value="DEPENDENCIES">Dependencies</option>
              <option value="MAINTAINABILITY">Maintainability</option>
            </select>
          </div>

          {/* Suppression Status */}
          <div className="flex items-center gap-1.5">
            <label
              htmlFor="suppression-select"
              className="text-[11px] font-medium text-slate-500 dark:text-slate-400"
            >
              Status:
            </label>
            <select
              id="suppression-select"
              value={filterState.suppressionFilter}
              onChange={handleSuppressionChange}
              className="rounded-md border border-slate-300 bg-white py-1 pl-2 pr-6 text-xs text-slate-900 focus:border-blue-500 focus:outline-hidden dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            >
              <option value="ALL">All Findings</option>
              <option value="ACTIVE_ONLY">Active Only</option>
              <option value="SUPPRESSED_ONLY">Suppressed Only</option>
            </select>
          </div>

          {/* Sort By Dropdown */}
          <div className="flex items-center gap-1.5">
            <label
              htmlFor="sort-select"
              className="text-[11px] font-medium text-slate-500 dark:text-slate-400"
            >
              Sort:
            </label>
            <select
              id="sort-select"
              value={filterState.sortBy}
              onChange={handleSortByChange}
              className="rounded-md border border-slate-300 bg-white py-1 pl-2 pr-6 text-xs text-slate-900 focus:border-blue-500 focus:outline-hidden dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            >
              <option value="priority">Priority</option>
              <option value="severity">Severity</option>
              <option value="rule">Rule ID</option>
              <option value="object">Object ID</option>
            </select>
            <button
              type="button"
              onClick={toggleSortDirection}
              className="rounded-md border border-slate-300 p-1 text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
              aria-label={`Toggle sort direction, current direction: ${filterState.sortDirection}`}
              title={`Sort ${filterState.sortDirection === "asc" ? "Ascending" : "Descending"}`}
            >
              <ArrowUpDown className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Reset button */}
          <button
            type="button"
            onClick={onResetFilters}
            className="rounded-md px-2.5 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
          >
            Reset
          </button>
        </div>
      </div>

      {/* Filter result count */}
      <div className="mt-2.5 text-[11px] text-slate-500 dark:text-slate-400">
        Showing {totalFilteredCount} of {totalFindingsCount} findings
      </div>
    </div>
  );
}
