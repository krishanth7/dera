"use client";

import React, { useEffect, useState } from "react";
import { MigrationDashboard } from "@/components/migrations/MigrationDashboard";
import {
  SAMPLE_SNAPSHOTS,
  SAMPLE_COMPARISON,
  SAMPLE_RISK_REPORT,
  SAMPLE_MIGRATION_PLAN,
  SAMPLE_SQL_ARTIFACT,
  SAMPLE_GOVERNANCE_REVIEW,
  SAMPLE_AUDIT_EVENTS,
} from "@/lib/migrations/fixtures";
import { SchemaSnapshotSummary } from "@/lib/migrations/types";
import { apiClient } from "@/lib/api-client";
import { useWorkspace } from "@/providers/workspace-provider";
import { Loader2, AlertCircle } from "lucide-react";

export default function MigrationsPage() {
  const { currentWorkspace } = useWorkspace();
  const [snapshots, setSnapshots] = useState<SchemaSnapshotSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isDemoMode, setIsDemoMode] = useState<boolean>(false);

  useEffect(() => {
    let mounted = true;

    async function loadWorkspaceSnapshots() {
      if (!currentWorkspace?.id) {
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        const res = await apiClient.listMigrationSnapshots(currentWorkspace.id);
        if (mounted) {
          if (res.snapshots && res.snapshots.length > 0) {
            setSnapshots(res.snapshots);
            setIsDemoMode(false);
          } else {
            // No snapshots in live workspace yet: offer live selection or fallback to demo
            setSnapshots([]);
          }
        }
      } catch (err: any) {
        if (mounted) {
          console.warn("Failed to load workspace snapshots:", err);
          setError("Could not load workspace snapshots. Live API may be unavailable or workspace has no captured schemas.");
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    }

    loadWorkspaceSnapshots();
    return () => {
      mounted = false;
    };
  }, [currentWorkspace?.id]);

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-16 max-w-7xl flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
        <p className="text-sm text-slate-400">Loading authenticated workspace snapshots...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6 max-w-7xl space-y-4">
      {/* Persistent Demo Mode or Live Mode Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 bg-slate-900 border border-slate-800 rounded-lg text-xs">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-300">Mode:</span>
          {isDemoMode ? (
            <span className="px-2 py-0.5 rounded font-bold bg-amber-950 text-amber-300 border border-amber-800">
              DEMO MODE — SAMPLE DATA — NOT LIVE RESULTS
            </span>
          ) : (
            <span className="px-2 py-0.5 rounded font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
              LIVE WORKSPACE ENGINE — AUTHENTICATED
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setIsDemoMode((prev) => !prev)}
            className="text-indigo-400 hover:text-indigo-300 underline font-medium"
          >
            {isDemoMode ? "Switch to Live Workspace Mode" : "Switch to Demo Mode (Sample Fixtures)"}
          </button>
        </div>
      </div>

      {error && !isDemoMode && (
        <div className="p-4 bg-amber-950/60 border border-amber-800 text-amber-200 rounded-lg text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={() => setIsDemoMode(true)}
            className="px-2.5 py-1 bg-amber-900 hover:bg-amber-800 text-white rounded font-medium ml-4"
          >
            View Demo Fixtures
          </button>
        </div>
      )}

      {isDemoMode ? (
        <MigrationDashboard
          snapshots={SAMPLE_SNAPSHOTS}
          initialComparison={SAMPLE_COMPARISON}
          initialRiskReport={SAMPLE_RISK_REPORT}
          initialPlan={SAMPLE_MIGRATION_PLAN}
          initialArtifact={SAMPLE_SQL_ARTIFACT}
          initialReview={SAMPLE_GOVERNANCE_REVIEW}
          initialAuditEvents={SAMPLE_AUDIT_EVENTS}
          isDemoMode={true}
        />
      ) : (
        <MigrationDashboard
          workspaceId={currentWorkspace?.id}
          snapshots={snapshots}
          isDemoMode={false}
        />
      )}
    </div>
  );
}
