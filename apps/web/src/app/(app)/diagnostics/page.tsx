"use client";

import React, { useEffect, useState, useCallback } from "react";
import { DiagnosticFinding, DiagnosticReport } from "@/lib/diagnostics/types";
import { evaluateSchemaDiagnostics } from "@/lib/diagnostics/api";
import { SAMPLE_DIAGNOSTIC_REPORT } from "@/lib/diagnostics/fixtures";
import { DiagnosticsOverview } from "@/components/diagnostics/DiagnosticsOverview";
import { useWorkspace } from "@/providers/workspace-provider";
import { apiClient, SchemaSummary } from "@/lib/api-client";
import { Sparkles, AlertCircle, Database, RefreshCw } from "lucide-react";
import DiagnosticsLoading from "./loading";

export default function DiagnosticsPage() {
  const { currentWorkspace } = useWorkspace();
  const [report, setReport] = useState<DiagnosticReport | null>(null);
  const [schemas, setSchemas] = useState<SchemaSummary[]>([]);
  const [selectedSchemaId, setSelectedSchemaId] = useState<string | null>(null);
  const [isDemoMode, setIsDemoMode] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadDiagnostics = useCallback(
    async (targetSchemaId?: string) => {
      if (!currentWorkspace?.id) {
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        // 1. Fetch available registered schemas in the workspace
        const schemaList = await apiClient.listSchemas(currentWorkspace.id);
        setSchemas(schemaList);

        if (schemaList.length === 0) {
          // No real schemas in workspace: prompt user to inspect or choose demo mode
          setIsLoading(false);
          return;
        }

        const schemaToEvaluate =
          targetSchemaId ||
          selectedSchemaId ||
          schemaList[0].schema_id ||
          (schemaList[0] as any).id;

        setSelectedSchemaId(schemaToEvaluate);

        // 2. Evaluate real registered schema with workspace authorization headers
        const data = await evaluateSchemaDiagnostics(schemaToEvaluate, {
          workspaceId: currentWorkspace.id,
        });

        setReport(data);
        setIsDemoMode(false);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Failed to evaluate schema diagnostics.";
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    },
    [currentWorkspace, selectedSchemaId]
  );

  useEffect(() => {
    loadDiagnostics();
  }, [loadDiagnostics]);

  const handleEnterDemoMode = () => {
    setReport(SAMPLE_DIAGNOSTIC_REPORT);
    setIsDemoMode(true);
    setError(null);
  };

  const handleApplySuppression = useCallback(
    (fingerprint: string, _reason: string, _durationDays: number) => {
      setReport((prev) => {
        if (!prev) return prev;
        const updatedFindings = prev.findings.map((f: DiagnosticFinding) => {
          if (f.fingerprint === fingerprint) {
            return {
              ...f,
              is_suppressed: true,
              suppression_id: `supp-${Date.now().toString(36)}`,
            };
          }
          return f;
        });

        const suppressedCount = updatedFindings.filter((f) => f.is_suppressed).length;
        return {
          ...prev,
          findings: updatedFindings,
          summary: {
            ...prev.summary,
            suppressed_findings: suppressedCount,
          },
        };
      });
    },
    []
  );

  const handleRevokeSuppression = useCallback((fingerprint: string) => {
    setReport((prev) => {
      if (!prev) return prev;
      const updatedFindings = prev.findings.map((f: DiagnosticFinding) => {
        if (f.fingerprint === fingerprint) {
          return {
            ...f,
            is_suppressed: false,
            suppression_id: undefined,
          };
        }
        return f;
      });

      const suppressedCount = updatedFindings.filter((f) => f.is_suppressed).length;
      return {
        ...prev,
        findings: updatedFindings,
        summary: {
          ...prev.summary,
          suppressed_findings: suppressedCount,
        },
      };
    });
  }, []);

  if (isLoading && !report) {
    return <DiagnosticsLoading />;
  }

  // Error state: Surface evaluation failure clearly
  if (error && !report) {
    return (
      <div className="mx-auto max-w-4xl p-8" role="alert">
        <div className="rounded-xl border border-red-200 bg-red-50/70 p-6 text-center dark:border-red-950/60 dark:bg-red-950/20">
          <AlertCircle className="mx-auto h-8 w-8 text-red-600 dark:text-red-400" />
          <h2 className="mt-3 text-base font-bold text-red-900 dark:text-red-200">
            Diagnostics Evaluation Failed
          </h2>
          <p className="mx-auto mt-2 max-w-lg text-xs text-red-700 dark:text-red-300">
            {error}
          </p>
          <div className="mt-5 flex items-center justify-center gap-3">
            <button
              type="button"
              onClick={() => loadDiagnostics()}
              className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3.5 py-1.5 text-xs font-medium text-white shadow-xs hover:bg-blue-700"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Retry Evaluation
            </button>
            <button
              type="button"
              onClick={handleEnterDemoMode}
              className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3.5 py-1.5 text-xs font-medium text-slate-700 shadow-xs hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              <Sparkles className="h-3.5 w-3.5 text-amber-500" />
              Explore Demo Report
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Empty state: Workspace has no inspected schemas yet
  if (!report && schemas.length === 0) {
    return (
      <div className="mx-auto max-w-4xl p-8">
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <Database className="mx-auto h-10 w-10 text-slate-400" />
          <h2 className="mt-3 text-base font-bold text-slate-900 dark:text-slate-100">
            No Inspected Schemas in Workspace
          </h2>
          <p className="mx-auto mt-2 max-w-md text-xs text-slate-500 dark:text-slate-400">
            To run deterministic diagnostic rules against your database, inspect a connection first.
            You can also explore the diagnostic dashboard using verified sample data.
          </p>
          <div className="mt-6 flex items-center justify-center gap-3">
            <button
              type="button"
              onClick={handleEnterDemoMode}
              className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-4 py-2 text-xs font-medium text-white shadow-xs hover:bg-blue-700"
            >
              <Sparkles className="h-3.5 w-3.5 text-amber-300" />
              View Verified Demo Report
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Prominent Demo Mode Banner if in sample fixture mode */}
      {isDemoMode && (
        <div
          role="status"
          className="flex items-center justify-between rounded-lg border border-amber-300 bg-amber-50 px-4 py-2.5 text-xs text-amber-900 shadow-xs dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-200"
        >
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-amber-600 dark:text-amber-400" />
            <span className="font-semibold">Demo Mode:</span>
            <span>
              Viewing verified deterministic sample diagnostic report. Real database evaluation
              requires an inspected schema.
            </span>
          </div>
          {schemas.length > 0 && (
            <button
              type="button"
              onClick={() => loadDiagnostics(schemas[0].schema_id)}
              className="rounded-md bg-amber-200/80 px-2.5 py-1 text-[11px] font-medium text-amber-950 hover:bg-amber-200 dark:bg-amber-900/60 dark:text-amber-100 dark:hover:bg-amber-800"
            >
              Evaluate Real Schema ({schemas[0].database_name || schemas[0].schema_id})
            </button>
          )}
        </div>
      )}

      <DiagnosticsOverview
        report={report || SAMPLE_DIAGNOSTIC_REPORT}
        workspaceName={
          isDemoMode
            ? "Demo Workspace (Sample Fixture)"
            : currentWorkspace?.name || "Production Workspace"
        }
        connectionName={isDemoMode ? "SQLite Reference Schema" : "Primary Database"}
        engineName={isDemoMode ? "SQLite 3.39" : "PostgreSQL 16"}
        onReevaluate={() => loadDiagnostics()}
        onApplySuppression={handleApplySuppression}
        onRevokeSuppression={handleRevokeSuppression}
        isLoading={isLoading}
      />
    </div>
  );
}
