"use client";

import React, { useState } from "react";
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
import { useWorkspace } from "@/providers/workspace-provider";

export default function MigrationsPage() {
  const { currentWorkspace } = useWorkspace();

  return (
    <div className="container mx-auto px-4 py-6 max-w-7xl">
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
    </div>
  );
}
