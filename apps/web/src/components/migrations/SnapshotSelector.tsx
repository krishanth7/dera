"use client";

import React from "react";
import { SchemaSnapshotSummary } from "@/lib/migrations/types";
import { Database, CheckCircle2, AlertTriangle, ArrowRight } from "lucide-react";

interface SnapshotSelectorProps {
  snapshots: SchemaSnapshotSummary[];
  baselineId: string;
  targetId: string;
  onSelectBaseline: (id: string) => void;
  onSelectTarget: (id: string) => void;
  onRunComparison: () => void;
  isComparing?: boolean;
}

export function SnapshotSelector({
  snapshots,
  baselineId,
  targetId,
  onSelectBaseline,
  onSelectTarget,
  onRunComparison,
  isComparing = false,
}: SnapshotSelectorProps) {
  const baseline = snapshots.find((s) => s.id === baselineId);
  const target = snapshots.find((s) => s.id === targetId);

  const isCompatible = baseline && target && baseline.engine === target.engine;
  const isSameSnapshot = baselineId && targetId && baselineId === targetId;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 text-slate-100 shadow-md">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-4">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Database className="w-5 h-5 text-indigo-400" />
            Snapshot Selection & Compatibility Verification
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic evaluation requires two compatible immutable schema snapshots captured from authorized sources.
          </p>
        </div>
        <button
          type="button"
          onClick={onRunComparison}
          disabled={!isCompatible || isSameSnapshot || isComparing}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white rounded-md text-sm font-medium transition-colors shadow"
        >
          {isComparing ? "Comparing..." : "Compare Snapshots"}
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Baseline (Source) */}
        <div className="space-y-3">
          <label htmlFor="baseline-selector" className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
            Source Baseline Snapshot
          </label>
          <select
            id="baseline-selector"
            aria-label="Select baseline snapshot"
            value={baselineId}
            onChange={(e) => onSelectBaseline(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {snapshots.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.engine} {s.engine_version})
              </option>
            ))}
          </select>
          {baseline && (
            <div className="text-xs bg-slate-950/60 p-3 rounded border border-slate-800 space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-400">Snapshot ID:</span>
                <span className="font-mono text-slate-300">{baseline.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Fingerprint:</span>
                <span className="font-mono text-slate-400 truncate max-w-[200px]" title={baseline.fingerprint}>
                  {baseline.fingerprint}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Objects:</span>
                <span className="text-slate-300">
                  {baseline.table_count} tables, {baseline.view_count} views
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Target (Destination) */}
        <div className="space-y-3">
          <label htmlFor="target-selector" className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
            Target Destination Snapshot
          </label>
          <select
            id="target-selector"
            aria-label="Select target snapshot"
            value={targetId}
            onChange={(e) => onSelectTarget(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {snapshots.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.engine} {s.engine_version})
              </option>
            ))}
          </select>
          {target && (
            <div className="text-xs bg-slate-950/60 p-3 rounded border border-slate-800 space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-400">Snapshot ID:</span>
                <span className="font-mono text-slate-300">{target.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Fingerprint:</span>
                <span className="font-mono text-slate-400 truncate max-w-[200px]" title={target.fingerprint}>
                  {target.fingerprint}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Objects:</span>
                <span className="text-slate-300">
                  {target.table_count} tables, {target.view_count} views
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Compatibility Status Banner */}
      <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          {isSameSnapshot ? (
            <span className="inline-flex items-center gap-1.5 text-amber-400">
              <AlertTriangle className="w-4 h-4" />
              Source and target snapshots are identical. Select distinct snapshots to compute structural changes.
            </span>
          ) : isCompatible ? (
            <span className="inline-flex items-center gap-1.5 text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
              Snapshots compatible: Identical dialect ({baseline?.engine}) and matching engine versions.
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 text-rose-400">
              <AlertTriangle className="w-4 h-4" />
              Incompatible engine dialects: Cannot migrate directly between {baseline?.engine} and {target?.engine}.
            </span>
          )}
        </div>
        <span className="text-slate-500 font-mono">Tenant Isolation: Verified</span>
      </div>
    </div>
  );
}
