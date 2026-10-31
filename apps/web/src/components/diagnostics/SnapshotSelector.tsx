"use client";

import React from "react";
import { Camera, Check, RefreshCw } from "lucide-react";

interface SnapshotSelectorProps {
  currentSnapshotId?: string;
  availableSnapshots?: Array<{ id: string; name: string; timestamp: string }>;
  onSelectSnapshot?: (snapshotId: string) => void;
  onEvaluateLive?: () => void;
  isLoading?: boolean;
  className?: string;
}

export function SnapshotSelector({
  currentSnapshotId,
  availableSnapshots = [],
  onSelectSnapshot,
  onEvaluateLive,
  isLoading = false,
  className = "",
}: SnapshotSelectorProps) {
  return (
    <div
      className={`flex flex-wrap items-center gap-2 rounded-lg border border-slate-200 bg-white p-3 shadow-xs dark:border-slate-800 dark:bg-slate-900 ${className}`}
      aria-label="Schema Snapshot Selector"
    >
      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300">
        <Camera className="h-4 w-4 text-blue-500" />
        <span>Evaluation Target:</span>
      </div>

      <div className="flex items-center gap-2">
        <select
          value={currentSnapshotId || "live"}
          onChange={(e) => {
            const val = e.target.value;
            if (val === "live") {
              onEvaluateLive?.();
            } else {
              onSelectSnapshot?.(val);
            }
          }}
          disabled={isLoading}
          className="rounded-md border border-slate-300 bg-white py-1 pl-2 pr-6 text-xs text-slate-900 focus:border-blue-500 focus:outline-hidden dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
          aria-label="Select schema or snapshot for evaluation"
        >
          <option value="live">Live Schema (Current)</option>
          {availableSnapshots.map((snap) => (
            <option key={snap.id} value={snap.id}>
              {snap.name} ({new Date(snap.timestamp).toLocaleDateString()})
            </option>
          ))}
        </select>

        {onEvaluateLive && (
          <button
            type="button"
            onClick={onEvaluateLive}
            disabled={isLoading}
            className="inline-flex items-center gap-1.5 rounded-md bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 hover:bg-blue-100 disabled:opacity-50 dark:bg-blue-950/40 dark:text-blue-300 dark:hover:bg-blue-900/50"
            title="Re-run diagnostic evaluation against live schema"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
            <span>Re-evaluate</span>
          </button>
        )}
      </div>

      {currentSnapshotId && currentSnapshotId !== "live" && (
        <span className="text-[11px] text-slate-500 dark:text-slate-400">
          Showing historical evaluation for snapshot <code>{currentSnapshotId}</code>
        </span>
      )}
    </div>
  );
}
