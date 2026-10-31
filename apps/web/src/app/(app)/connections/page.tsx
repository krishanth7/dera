import { EmptyState } from "@/components/ui/empty-state";
import { Database } from "lucide-react";

export default function ConnectionsPage() {
  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 dark:border-slate-800 pb-5">
        <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Database Connections
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Target database connection configurations and connection pooling.
        </p>
      </div>

      <EmptyState
        title="No Database Connections Configured"
        description="Database connection pools, dialect probers, and reverse engineering drivers are scheduled for Phase 7.2."
        icon={<Database className="w-6 h-6 text-slate-400" />}
      />
    </div>
  );
}
