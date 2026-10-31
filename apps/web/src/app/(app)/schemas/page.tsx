import { EmptyState } from "@/components/ui/empty-state";
import { TableProperties } from "lucide-react";

export default function SchemasPage() {
  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 dark:border-slate-800 pb-5">
        <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Schema Explorer
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Inspect extracted tables, views, columns, indexes, and primary key constraints.
        </p>
      </div>

      <EmptyState
        title="No Schemas Extracted"
        description="Connect a database in Phase 7.2 to trigger structural reverse engineering and inspect table metadata."
        icon={<TableProperties className="w-6 h-6 text-slate-400" />}
      />
    </div>
  );
}
