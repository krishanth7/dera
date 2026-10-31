"use client";

/**
 * DERA — Table Inspector Indexes Tab
 * Displays secondary, unique, and primary indexes with column terms and uniqueness semantics.
 */

import React from "react";
import { Binary, KeyRound, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { TableDetailItem } from "@/lib/api-client";

interface IndexesTabProps {
  table: TableDetailItem;
}

export function IndexesTab({ table }: IndexesTabProps) {
  const indexes = table.indexes || [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Binary className="w-4 h-4 text-violet-500" />
          <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            Database Indexes ({indexes.length})
          </h2>
        </div>
      </div>

      {indexes.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {indexes.map((idx) => (
            <div
              key={idx.index_id}
              className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm text-xs space-y-3"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-mono font-semibold text-slate-900 dark:text-slate-100">
                  {idx.name}
                </span>
                <div className="flex items-center gap-1.5">
                  {idx.is_primary && (
                    <Badge variant="outline" className="text-[10px] bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30">
                      <KeyRound className="w-2.5 h-2.5 mr-1" />
                      PRIMARY
                    </Badge>
                  )}
                  {idx.is_unique && !idx.is_primary && (
                    <Badge variant="outline" className="text-[10px] bg-teal-500/10 text-teal-700 dark:text-teal-300 border-teal-500/30">
                      UNIQUE
                    </Badge>
                  )}
                  {!idx.is_unique && (
                    <Badge variant="secondary" className="text-[10px]">
                      INDEX
                    </Badge>
                  )}
                </div>
              </div>

              <div className="text-slate-600 dark:text-slate-400 space-y-1">
                <span className="text-[11px] text-slate-500 block">Indexed Columns:</span>
                <div className="flex flex-wrap gap-1">
                  {idx.columns.map((col, cIdx) => (
                    <span
                      key={col}
                      className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-mono text-[11px] text-slate-800 dark:text-slate-200"
                    >
                      <span className="text-violet-500 mr-1">#{cIdx + 1}</span>
                      {col}
                    </span>
                  ))}
                </div>
              </div>

              <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex justify-between items-center text-[11px] text-slate-400 font-mono">
                <span>ID: {idx.index_id}</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-8 rounded-xl border border-dashed border-slate-200 dark:border-slate-800 text-center space-y-2">
          <Binary className="w-8 h-8 mx-auto text-slate-400" />
          <p className="text-xs text-slate-500">
            No indexes discovered or declared on table &ldquo;{table.name}&rdquo;.
          </p>
        </div>
      )}
    </div>
  );
}
