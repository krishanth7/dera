"use client";

/**
 * DERA — Advanced Schema Search Results List
 * Displays paginated search matches with object type badges, parent context,
 * matched snippets, and navigation actions.
 */

import React from "react";
import Link from "next/link";
import {
  Table2,
  Columns3,
  KeyRound,
  Binary,
  Layers,
  ArrowRight,
  Database,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  SearchX,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { SearchResultItem, SearchPaginationState } from "./types";

interface SearchResultsListProps {
  results: SearchResultItem[];
  pagination: SearchPaginationState;
  onPageChange: (newPage: number) => void;
  onPageSizeChange: (newPageSize: number) => void;
  query: string;
}

export function SearchResultsList({
  results,
  pagination,
  onPageChange,
  onPageSizeChange,
  query,
}: SearchResultsListProps) {
  const { page, pageSize, totalCount } = pagination;
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));

  const getObjectIcon = (type: string) => {
    switch (type) {
      case "table":
      case "view":
        return <Table2 className="w-4 h-4 text-indigo-500" />;
      case "column":
        return <Columns3 className="w-4 h-4 text-emerald-500" />;
      case "constraint":
        return <KeyRound className="w-4 h-4 text-amber-500" />;
      case "index":
        return <Binary className="w-4 h-4 text-violet-500" />;
      case "namespace":
        return <Layers className="w-4 h-4 text-teal-500" />;
      default:
        return <Database className="w-4 h-4 text-slate-500" />;
    }
  };

  const getBadgeVariant = (type: string) => {
    switch (type) {
      case "table":
        return "secondary";
      case "view":
        return "outline";
      case "column":
        return "success";
      case "constraint":
        return "warning";
      case "index":
        return "outline";
      default:
        return "secondary";
    }
  };

  const resolveTargetUrl = (item: SearchResultItem) => {
    if (item.objectType === "namespace") {
      return `/schemas/${encodeURIComponent(item.schemaId)}?namespace=${encodeURIComponent(item.name)}`;
    }
    const tableId = item.parentTableId || item.id;
    return `/tables/${encodeURIComponent(tableId)}?schemaId=${encodeURIComponent(item.schemaId)}`;
  };

  if (results.length === 0) {
    return (
      <div className="p-12 text-center rounded-xl border border-dashed border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-3">
        <SearchX className="w-10 h-10 mx-auto text-slate-400" />
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
          No Database Objects Matched
        </h3>
        <p className="text-xs text-slate-500 max-w-sm mx-auto">
          {query
            ? `No tables, columns, constraints, or indexes matching "${query}" were found in authorized schemas.`
            : "Enter a search query or adjust filters to discover schema objects."}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Results List */}
      <div className="space-y-2">
        {results.map((item) => {
          const targetUrl = resolveTargetUrl(item);

          return (
            <Link
              key={`${item.objectType}-${item.schemaId}-${item.id}`}
              href={targetUrl}
              className="group block p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-indigo-500/50 hover:shadow-sm transition-all text-xs"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/80 border border-slate-100 dark:border-slate-800 group-hover:border-indigo-200 dark:group-hover:border-indigo-900 transition-colors">
                    {getObjectIcon(item.objectType)}
                  </div>
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono font-semibold text-sm text-slate-900 dark:text-slate-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                        {item.name}
                      </span>
                      <Badge variant={getBadgeVariant(item.objectType)} className="text-[10px] uppercase font-mono">
                        {item.objectType}
                      </Badge>
                      <Badge variant="outline" className="text-[10px] font-mono text-slate-500">
                        {item.namespace}
                      </Badge>
                    </div>

                    {/* Hierarchy context */}
                    <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
                      <span>Database: <strong className="text-slate-700 dark:text-slate-300 font-mono">{item.databaseName}</strong></span>
                      {item.parentTableName && (
                        <>
                          <span>&bull;</span>
                          <span>Table: <strong className="text-slate-700 dark:text-slate-300 font-mono">{item.parentTableName}</strong></span>
                        </>
                      )}
                      <span>&bull;</span>
                      <span className="text-slate-400">Match in: <em className="text-slate-600 dark:text-slate-300 not-italic font-medium">{item.matchedField}</em></span>
                    </div>

                    {/* Snippet */}
                    {item.snippet && (
                      <div className="text-[11px] font-mono text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/50 px-2 py-1 rounded inline-block">
                        {item.snippet}
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-1.5 text-xs text-slate-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 font-medium whitespace-nowrap self-end sm:self-center">
                  <span>Inspect</span>
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </div>
              </div>
            </Link>
          );
        })}
      </div>

      {/* Pagination Controls */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-slate-200 dark:border-slate-800 text-xs text-slate-500">
        <div className="flex items-center gap-2">
          <span>Rows per page:</span>
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            className="h-7 px-2 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-xs"
          >
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
          </select>
          <span className="ml-2">
            Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, totalCount)} of {totalCount} results
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="h-8 text-xs gap-1"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            Previous
          </Button>
          <span className="font-mono text-xs px-2">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="h-8 text-xs gap-1"
          >
            Next
            <ChevronRight className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>
    </div>
  );
}
