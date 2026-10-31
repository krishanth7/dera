import { EmptyState } from "@/components/ui/empty-state";
import { FileDown } from "lucide-react";

export default function ExportsPage() {
  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 dark:border-slate-800 pb-5">
        <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Schema Exports
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Export definitions to SQL DDL, PlantUML, Mermaid, JSON, and Markdown.
        </p>
      </div>

      <EmptyState
        title="No Schema Exports Generated"
        description="Deterministic schema export facilities powered by core Phase 6.6 will be interactive in Phase 7.3."
        icon={<FileDown className="w-6 h-6 text-slate-400" />}
      />
    </div>
  );
}
