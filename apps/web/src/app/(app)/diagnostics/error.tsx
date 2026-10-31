"use client";

import React, { useEffect } from "react";
import { AlertCircle, RefreshCw, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function DiagnosticsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Audit / log diagnostic load error without sensitive data leakage
    console.error("Diagnostics dashboard load error:", error.message);
  }, [error]);

  return (
    <div
      className="flex min-h-[50vh] flex-col items-center justify-center rounded-lg border border-red-200 bg-white p-8 text-center shadow-xs dark:border-red-950 dark:bg-slate-900"
      role="alert"
      aria-live="assertive"
    >
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-950/60">
        <AlertCircle className="h-6 w-6 text-red-600 dark:text-red-400" />
      </div>

      <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
        Unable to Load Diagnostics Report
      </h2>

      <p className="mt-2 max-w-md text-xs text-slate-600 dark:text-slate-400">
        An error occurred while evaluating or fetching the schema diagnostic report.
        Verify your database connection permissions and workspace access.
      </p>

      {error.message && (
        <div className="mt-3 rounded-md bg-slate-100 p-2 font-mono text-[11px] text-slate-700 dark:bg-slate-800 dark:text-slate-300">
          {error.message}
        </div>
      )}

      <div className="mt-6 flex items-center gap-3">
        <button
          type="button"
          onClick={() => reset()}
          className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-700 focus:outline-hidden focus:ring-2 focus:ring-blue-500"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Retry Diagnostics</span>
        </button>

        <Link
          href="/app/overview"
          className="inline-flex items-center gap-2 rounded-md border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Return to Overview</span>
        </Link>
      </div>
    </div>
  );
}
