import { EmptyState } from "@/components/ui/empty-state";
import { GitFork } from "lucide-react";

export default function DependenciesPage() {
  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 dark:border-slate-800 pb-5">
        <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Dependency Analysis
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Topological table ordering, circular dependency detection, and drop sequences.
        </p>
      </div>

      <EmptyState
        title="Dependency Graph Unavailable"
        description="Dependency analysis based on Phase 6.4 core contracts will be visually displayed in future releases."
        icon={<GitFork className="w-6 h-6 text-slate-400" />}
      />
    </div>
  );
}
