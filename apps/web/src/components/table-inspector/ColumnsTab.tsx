"use client";

/**
 * DERA — Table Inspector Columns Tab
 * Comprehensive ordinal column table with sorting, search filtering,
 * PK/FK indicators, and expandable details panel.
 */

import React, { useState, useMemo } from "react";
import {
  KeyRound,
  Link2,
  ArrowUpDown,
  Search,
  ChevronDown,
  ChevronRight,
  Info,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import type { ColumnDetailItem, TableDetailItem } from "@/lib/api-client";
import type { ColumnSortField, ColumnSortDirection } from "./types";

interface ColumnsTabProps {
  table: TableDetailItem;
}

export function ColumnsTab({ table }: ColumnsTabProps) {
  const [filterQuery, setFilterQuery] = useState("");
  const [sortField, setSortField] = useState<ColumnSortField>("ordinal");
  const [sortDirection, setSortDirection] = useState<ColumnSortDirection>("asc");
  const [expandedColumnId, setExpandedColumnId] = useState<string | null>(null);

  // Map of column names participating in foreign keys
  const fkColumnMap = useMemo(() => {
    const map = new Map<string, { constraintName: string; targetTable: string; targetColumn: string }>();
    table.foreign_keys.forEach((fk) => {
      fk.source_columns.forEach((srcCol, idx) => {
        map.set(srcCol, {
          constraintName: fk.name,
          targetTable: fk.referenced_table_name,
          targetColumn: fk.referenced_columns[idx] || "",
        });
      });
    });
    return map;
  }, [table.foreign_keys]);

  const handleSort = (field: ColumnSortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const processedColumns = useMemo(() => {
    let result = [...table.columns];

    // Filter
    if (filterQuery.trim()) {
      const q = filterQuery.toLowerCase().trim();
      result = result.filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          c.native_type.toLowerCase().includes(q) ||
          c.canonical_type.toLowerCase().includes(q)
      );
    }

    // Sort
    result.sort((a, b) => {
      let cmp = 0;
      switch (sortField) {
        case "ordinal":
          cmp = a.ordinal_position - b.ordinal_position;
          break;
        case "name":
          cmp = a.name.localeCompare(b.name);
          break;
        case "type":
          cmp = a.native_type.localeCompare(b.native_type);
          break;
        case "nullable":
          cmp = Number(a.is_nullable) - Number(b.is_nullable);
          break;
      }
      return sortDirection === "asc" ? cmp : -cmp;
    });

    return result;
  }, [table.columns, filterQuery, sortField, sortDirection]);

  return (
    <div className="space-y-4">
      {/* Search & Statistics Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <Input
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            placeholder="Filter columns by name or type..."
            className="pl-9 h-9 text-xs"
          />
        </div>
        <div className="text-xs text-slate-500 dark:text-slate-400">
          Showing <strong>{processedColumns.length}</strong> of <strong>{table.columns.length}</strong> columns
          {filterQuery && (
            <button
              type="button"
              onClick={() => setFilterQuery("")}
              className="ml-2 text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              Clear filter
            </button>
          )}
        </div>
      </div>

      {/* Accessible Columns Table */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden bg-white dark:bg-slate-900 shadow-sm">
        <table className="w-full text-left border-collapse text-xs">
          <caption className="sr-only">Table columns metadata for {table.name}</caption>
          <thead>
            <tr className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-[11px] font-semibold text-slate-600 dark:text-slate-300">
              <th scope="col" className="w-10 px-3 py-3 text-center">
                <span className="sr-only">Expand</span>
              </th>
              <th scope="col" className="w-14 px-3 py-3">
                <button
                  type="button"
                  onClick={() => handleSort("ordinal")}
                  className="flex items-center gap-1 hover:text-slate-900 dark:hover:text-slate-100"
                >
                  # <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </button>
              </th>
              <th scope="col" className="px-4 py-3">
                <button
                  type="button"
                  onClick={() => handleSort("name")}
                  className="flex items-center gap-1 hover:text-slate-900 dark:hover:text-slate-100"
                >
                  Column Name <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </button>
              </th>
              <th scope="col" className="px-4 py-3">
                <button
                  type="button"
                  onClick={() => handleSort("type")}
                  className="flex items-center gap-1 hover:text-slate-900 dark:hover:text-slate-100"
                >
                  Data Type <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </button>
              </th>
              <th scope="col" className="px-4 py-3">
                <button
                  type="button"
                  onClick={() => handleSort("nullable")}
                  className="flex items-center gap-1 hover:text-slate-900 dark:hover:text-slate-100"
                >
                  Nullability <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </button>
              </th>
              <th scope="col" className="px-4 py-3">
                Key / Constraint
              </th>
              <th scope="col" className="px-4 py-3">
                Default Value
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {processedColumns.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-slate-500 dark:text-slate-400">
                  No columns match filter &ldquo;{filterQuery}&rdquo;.
                </td>
              </tr>
            ) : (
              processedColumns.map((col) => {
                const isExpanded = expandedColumnId === col.column_id;
                const fkInfo = fkColumnMap.get(col.name);

                return (
                  <React.Fragment key={col.column_id}>
                    <tr
                      className={`hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors ${
                        isExpanded ? "bg-slate-50 dark:bg-slate-800/50" : ""
                      }`}
                    >
                      <td className="px-3 py-2.5 text-center">
                        <button
                          type="button"
                          onClick={() => setExpandedColumnId(isExpanded ? null : col.column_id)}
                          aria-label={`${isExpanded ? "Collapse" : "Expand"} column details for ${col.name}`}
                          className="p-1 rounded text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                        >
                          {isExpanded ? (
                            <ChevronDown className="w-3.5 h-3.5" />
                          ) : (
                            <ChevronRight className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </td>
                      <td className="px-3 py-2.5 font-mono text-slate-500 dark:text-slate-400">
                        {col.ordinal_position}
                      </td>
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono font-medium text-slate-900 dark:text-slate-100">
                            {col.name}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono text-slate-800 dark:text-slate-200">
                            {col.native_type}
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono">
                            ({col.canonical_type})
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-2.5">
                        {col.is_nullable ? (
                          <span className="inline-flex items-center text-slate-500 text-[11px]">
                            <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-slate-400" />
                            NULL
                          </span>
                        ) : (
                          <span className="inline-flex items-center text-amber-600 dark:text-amber-400 font-medium text-[11px]">
                            <XCircle className="w-3.5 h-3.5 mr-1 text-amber-500" />
                            NOT NULL
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-2.5">
                        <div className="flex flex-wrap items-center gap-1.5">
                          {col.is_primary_key && (
                            <Badge
                              variant="outline"
                              className="bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30 text-[10px] font-mono gap-1"
                            >
                              <KeyRound className="w-2.5 h-2.5" />
                              PK
                            </Badge>
                          )}
                          {fkInfo && (
                            <Badge
                              variant="outline"
                              className="bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-500/30 text-[10px] font-mono gap-1"
                              title={`FK to ${fkInfo.targetTable}.${fkInfo.targetColumn} (${fkInfo.constraintName})`}
                            >
                              <Link2 className="w-2.5 h-2.5" />
                              FK &rarr; {fkInfo.targetTable}.{fkInfo.targetColumn}
                            </Badge>
                          )}
                          {!col.is_primary_key && !fkInfo && (
                            <span className="text-slate-400 text-[11px]">—</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-2.5">
                        {col.default_expression ? (
                          <code className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-mono text-[11px] max-w-[200px] truncate inline-block">
                            {col.default_expression}
                          </code>
                        ) : (
                          <span className="text-slate-400 text-[11px]">—</span>
                        )}
                      </td>
                    </tr>

                    {/* Expandable Column Details Row */}
                    {isExpanded && (
                      <tr className="bg-slate-50/70 dark:bg-slate-800/30">
                        <td colSpan={7} className="px-6 py-4 border-t border-slate-100 dark:border-slate-800">
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                            <div className="space-y-1">
                              <span className="text-slate-500 dark:text-slate-400 font-medium text-[11px] block">
                                Column Identity
                              </span>
                              <div className="font-mono text-slate-800 dark:text-slate-200 break-all">
                                ID: {col.column_id}
                              </div>
                              <div className="text-slate-600 dark:text-slate-400 text-[11px]">
                                Ordinal Position: #{col.ordinal_position}
                              </div>
                            </div>
                            <div className="space-y-1">
                              <span className="text-slate-500 dark:text-slate-400 font-medium text-[11px] block">
                                Type Mapping & Attributes
                              </span>
                              <div className="text-slate-700 dark:text-slate-300">
                                Native: <code className="font-mono">{col.native_type}</code>
                              </div>
                              <div className="text-slate-700 dark:text-slate-300">
                                Canonical: <code className="font-mono">{col.canonical_type}</code>
                              </div>
                            </div>
                            <div className="space-y-1">
                              <span className="text-slate-500 dark:text-slate-400 font-medium text-[11px] block">
                                Constraints & Relations
                              </span>
                              {col.is_primary_key && (
                                <div className="text-amber-700 dark:text-amber-300 font-medium">
                                  Primary Key constraint member
                                </div>
                              )}
                              {fkInfo && (
                                <div className="text-blue-700 dark:text-blue-300">
                                  References <code className="font-mono">{fkInfo.targetTable}({fkInfo.targetColumn})</code>
                                  <div className="text-slate-500 text-[11px]">via {fkInfo.constraintName}</div>
                                </div>
                              )}
                              {!col.is_primary_key && !fkInfo && (
                                <div className="text-slate-500">No key constraints mapped</div>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
