"use client";

/**
 * DERA — Table Inspector Constraints Tab
 * Displays Primary Keys, Foreign Keys (including composite mappings and referential actions),
 * Unique Constraints, and Check Constraints (inert SQL text).
 */

import React from "react";
import Link from "next/link";
import { KeyRound, Link2, Fingerprint, ShieldAlert, ExternalLink, ArrowRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { TableDetailItem } from "@/lib/api-client";

interface ConstraintsTabProps {
  table: TableDetailItem;
  schemaId: string;
}

export function ConstraintsTab({ table, schemaId }: ConstraintsTabProps) {
  const pk = table.primary_key;
  const fks = table.foreign_keys || [];
  const uqs = table.unique_constraints || [];
  const checks = table.check_constraints || [];

  return (
    <div className="space-y-6">
      {/* 1. Primary Key Section */}
      <section aria-labelledby="pk-heading" className="space-y-3">
        <div className="flex items-center gap-2">
          <KeyRound className="w-4 h-4 text-amber-500" />
          <h2 id="pk-heading" className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            Primary Key Constraint
          </h2>
        </div>

        {pk ? (
          <div className="p-4 rounded-xl border border-amber-500/20 bg-amber-500/5 dark:bg-amber-950/20 space-y-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-xs text-slate-900 dark:text-slate-100">
                  {pk.name}
                </span>
                {pk.columns.length > 1 ? (
                  <Badge variant="outline" className="text-[10px] bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30">
                    Composite Key ({pk.columns.length} columns)
                  </Badge>
                ) : (
                  <Badge variant="outline" className="text-[10px] text-slate-600 dark:text-slate-400">
                    Single Column
                  </Badge>
                )}
              </div>
              <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
                ID: {pk.constraint_id}
              </span>
            </div>

            <div className="text-xs text-slate-700 dark:text-slate-300">
              <span className="text-slate-500 mr-2">Key Columns:</span>
              <div className="inline-flex flex-wrap gap-1 mt-1">
                {pk.columns.map((col, idx) => (
                  <span
                    key={col}
                    className="inline-flex items-center px-2 py-0.5 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 font-mono text-xs font-medium"
                  >
                    <span className="text-amber-500 mr-1">#{idx + 1}</span> {col}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="p-4 rounded-xl border border-dashed border-slate-200 dark:border-slate-800 text-xs text-slate-500 text-center">
            No Primary Key constraint defined on table &ldquo;{table.name}&rdquo;.
          </div>
        )}
      </section>

      {/* 2. Foreign Keys Section */}
      <section aria-labelledby="fk-heading" className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Link2 className="w-4 h-4 text-blue-500" />
            <h2 id="fk-heading" className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              Foreign Key Relationships ({fks.length})
            </h2>
          </div>
        </div>

        {fks.length > 0 ? (
          <div className="grid grid-cols-1 gap-3">
            {fks.map((fk) => {
              const isComposite = fk.source_columns.length > 1;

              return (
                <div
                  key={fk.constraint_id}
                  className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm space-y-3"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-100 dark:border-slate-800">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-semibold text-xs text-slate-900 dark:text-slate-100">
                        {fk.name}
                      </span>
                      {isComposite && (
                        <Badge variant="outline" className="text-[10px] bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-500/30">
                          Composite ({fk.source_columns.length} columns)
                        </Badge>
                      )}
                    </div>
                    <span className="text-[11px] font-mono text-slate-400">
                      ID: {fk.constraint_id}
                    </span>
                  </div>

                  {/* Mapping Display */}
                  <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-lg space-y-2 text-xs">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="space-y-1">
                        <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block">
                          Source (Referencing)
                        </span>
                        <div className="font-mono font-medium text-slate-900 dark:text-slate-100">
                          {table.name}
                        </div>
                      </div>

                      <div className="hidden sm:flex items-center justify-center text-slate-400 px-3">
                        <ArrowRight className="w-4 h-4" />
                      </div>

                      <div className="space-y-1">
                        <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block">
                          Target (Referenced Parent)
                        </span>
                        {fk.referenced_table_id ? (
                          <Link
                            href={`/tables/${encodeURIComponent(fk.referenced_table_id)}?schemaId=${encodeURIComponent(schemaId)}`}
                            className="font-mono font-medium text-indigo-600 dark:text-indigo-400 hover:underline inline-flex items-center gap-1"
                          >
                            {fk.referenced_table_name}
                            <ExternalLink className="w-3 h-3" />
                          </Link>
                        ) : (
                          <div className="font-mono font-medium text-slate-900 dark:text-slate-100">
                            {fk.referenced_table_name}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Ordered Column Pair Mapping */}
                    <div className="pt-2 border-t border-slate-200/60 dark:border-slate-700/60 space-y-1">
                      <span className="text-[11px] text-slate-500 block">Column Mappings:</span>
                      <div className="space-y-1">
                        {fk.source_columns.map((srcCol, idx) => (
                          <div key={srcCol} className="flex items-center gap-2 font-mono text-xs">
                            <span className="px-2 py-0.5 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200">
                              {srcCol}
                            </span>
                            <span className="text-slate-400">&rarr;</span>
                            <span className="px-2 py-0.5 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200">
                              {fk.referenced_columns[idx] || "N/A"}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Referential Actions */}
                  <div className="flex flex-wrap items-center gap-3 text-xs pt-1">
                    <div className="flex items-center gap-1.5">
                      <span className="text-slate-500">ON DELETE:</span>
                      <Badge variant="outline" className="font-mono text-[10px] uppercase">
                        {fk.on_delete || "NO ACTION"}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-slate-500">ON UPDATE:</span>
                      <Badge variant="outline" className="font-mono text-[10px] uppercase">
                        {fk.on_update || "NO ACTION"}
                      </Badge>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-4 rounded-xl border border-dashed border-slate-200 dark:border-slate-800 text-xs text-slate-500 text-center">
            No Foreign Keys originating from table &ldquo;{table.name}&rdquo;.
          </div>
        )}
      </section>

      {/* 3. Unique Constraints Section */}
      <section aria-labelledby="uq-heading" className="space-y-3">
        <div className="flex items-center gap-2">
          <Fingerprint className="w-4 h-4 text-teal-500" />
          <h2 id="uq-heading" className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            Unique Constraints ({uqs.length})
          </h2>
        </div>

        {uqs.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {uqs.map((uq) => (
              <div
                key={uq.constraint_id}
                className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono font-semibold text-slate-900 dark:text-slate-100">
                    {uq.name}
                  </span>
                  <Badge variant="secondary" className="text-[10px]">
                    UNIQUE
                  </Badge>
                </div>
                <div className="text-slate-600 dark:text-slate-400">
                  <span className="text-slate-500 mr-1.5">Columns:</span>
                  <span className="font-mono text-slate-800 dark:text-slate-200">
                    ({uq.columns.join(", ")})
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4 rounded-xl border border-dashed border-slate-200 dark:border-slate-800 text-xs text-slate-500 text-center">
            No unique constraints declared on &ldquo;{table.name}&rdquo;.
          </div>
        )}
      </section>

      {/* 4. Check Constraints Section */}
      <section aria-labelledby="ck-heading" className="space-y-3">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-rose-500" />
          <h2 id="ck-heading" className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            Check Constraints ({checks.length})
          </h2>
        </div>

        {checks.length > 0 ? (
          <div className="grid grid-cols-1 gap-3">
            {checks.map((ck) => (
              <div
                key={ck.constraint_id}
                className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono font-semibold text-slate-900 dark:text-slate-100">
                    {ck.name}
                  </span>
                  <Badge variant="outline" className="text-[10px] text-rose-600 dark:text-rose-400 border-rose-500/30">
                    CHECK
                  </Badge>
                </div>
                {ck.raw_expression && (
                  <div className="p-2.5 rounded bg-slate-950 text-emerald-400 font-mono text-[11px] overflow-x-auto whitespace-pre-wrap">
                    {ck.raw_expression}
                  </div>
                )}
                {ck.columns.length > 0 && (
                  <div className="text-slate-500 text-[11px]">
                    Evaluates columns: <code className="font-mono text-slate-700 dark:text-slate-300">{ck.columns.join(", ")}</code>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4 rounded-xl border border-dashed border-slate-200 dark:border-slate-800 text-xs text-slate-500 text-center">
            No check constraints defined on &ldquo;{table.name}&rdquo;.
          </div>
        )}
      </section>
    </div>
  );
}
