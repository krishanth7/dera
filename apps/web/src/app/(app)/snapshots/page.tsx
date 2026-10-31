import { EmptyState } from "@/components/ui/empty-state";
import { Camera } from "lucide-react";

export default function SnapshotsPage() {
  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 dark:border-slate-800 pb-5">
        <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Schema Snapshots
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Deterministic SHA-256 fingerprint snapshots and drift verification records.
        </p>
      </div>

      <EmptyState
        title="No Schema Snapshots Captured"
        description="Capture deterministic snapshots using Phase 6.5 core models to track and audit database drift over time."
        icon={<Camera className="w-6 h-6 text-slate-400" />}
      />
    </div>
  );
}
