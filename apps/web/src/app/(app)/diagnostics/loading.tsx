import { Skeleton } from "@/components/ui/skeleton";

export default function DiagnosticsLoading() {
  return (
    <div className="space-y-6 animate-pulse" aria-label="Loading diagnostic dashboard">
      {/* Header Skeleton */}
      <div className="flex flex-col justify-between gap-4 rounded-lg border border-slate-200 bg-white p-5 shadow-xs sm:flex-row sm:items-center dark:border-slate-800 dark:bg-slate-900">
        <div className="space-y-2">
          <Skeleton className="h-6 w-64" />
          <Skeleton className="h-3.5 w-96" />
        </div>
        <Skeleton className="h-9 w-48 rounded-md" />
      </div>

      {/* KPI Cards Skeleton */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-8">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-20 rounded-lg" />
        ))}
      </div>

      {/* Charts Skeleton */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Skeleton className="h-64 rounded-lg" />
        <Skeleton className="h-64 rounded-lg" />
      </div>

      {/* Category Summary Skeleton */}
      <Skeleton className="h-32 rounded-lg" />

      {/* Table Skeleton */}
      <Skeleton className="h-96 rounded-lg" />
    </div>
  );
}
