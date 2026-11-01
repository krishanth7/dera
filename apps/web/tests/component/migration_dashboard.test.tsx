import { describe, it, expect } from "vitest";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { MigrationDashboard } from "../../src/components/migrations/MigrationDashboard";
import { SnapshotSelector } from "../../src/components/migrations/SnapshotSelector";
import { SchemaDiffExplorer } from "../../src/components/migrations/SchemaDiffExplorer";
import { RiskDetailPanel } from "../../src/components/migrations/RiskDetailPanel";
import { MigrationPlanViewer } from "../../src/components/migrations/MigrationPlanViewer";
import { SqlArtifactViewer } from "../../src/components/migrations/SqlArtifactViewer";
import { GovernanceReviewPanel } from "../../src/components/migrations/GovernanceReviewPanel";
import { AuditEvidencePanel } from "../../src/components/migrations/AuditEvidencePanel";
import {
  SAMPLE_SNAPSHOTS,
  SAMPLE_COMPARISON,
  SAMPLE_RISK_REPORT,
  SAMPLE_MIGRATION_PLAN,
  SAMPLE_SQL_ARTIFACT,
  SAMPLE_GOVERNANCE_REVIEW,
  SAMPLE_AUDIT_EVENTS,
} from "../../src/lib/migrations/fixtures";

describe("Phase 9.6 Migration Engineering Workspace Suite", () => {
  it("renders MigrationDashboard with overview metrics and tabs", () => {
    render(
      <MigrationDashboard
        snapshots={SAMPLE_SNAPSHOTS}
        initialComparison={SAMPLE_COMPARISON}
        initialRiskReport={SAMPLE_RISK_REPORT}
        initialPlan={SAMPLE_MIGRATION_PLAN}
        initialArtifact={SAMPLE_SQL_ARTIFACT}
        initialReview={SAMPLE_GOVERNANCE_REVIEW}
        initialAuditEvents={SAMPLE_AUDIT_EVENTS}
      />
    );

    expect(screen.getByText(/Migration Engineering & Governance Workspace/i)).toBeInTheDocument();
    expect(screen.getByText(/Customer Mutation: PROHIBITED/i)).toBeInTheDocument();
    expect(screen.getByText(/Total Structural Diffs/i)).toBeInTheDocument();
  });

  it("renders SnapshotSelector and prevents comparison of identical snapshots", () => {
    const handleCompare = vi.fn();
    render(
      <SnapshotSelector
        snapshots={SAMPLE_SNAPSHOTS}
        baselineId={SAMPLE_SNAPSHOTS[0].id}
        targetId={SAMPLE_SNAPSHOTS[0].id}
        onSelectBaseline={() => {}}
        onSelectTarget={() => {}}
        onRunComparison={handleCompare}
      />
    );

    const button = screen.getByRole("button", { name: /Compare Snapshots/i });
    expect(button).toBeDisabled();
    expect(screen.getByText(/Source and target snapshots are identical/i)).toBeInTheDocument();
  });

  it("renders SchemaDiffExplorer and displays detected structural changes", () => {
    render(<SchemaDiffExplorer comparison={SAMPLE_COMPARISON} />);
    expect(screen.getByText(/Phase 9.1 — Schema Snapshot Differences/i)).toBeInTheDocument();
    expect(screen.getAllByText(/payment_methods/i).length).toBeGreaterThan(0);
  });

  it("renders RiskDetailPanel and flags breaking changes", () => {
    render(<RiskDetailPanel report={SAMPLE_RISK_REPORT} />);
    expect(screen.getByText(/Phase 9.2 — Migration Risk Analysis & Classification/i)).toBeInTheDocument();
    expect(screen.getByText(/Potentially Breaking Changes/i)).toBeInTheDocument();
  });

  it("renders MigrationPlanViewer with ordered stages and manual gates", () => {
    render(<MigrationPlanViewer plan={SAMPLE_MIGRATION_PLAN} />);
    expect(screen.getByText(/Phase 9.3 — Deterministic Migration Plan/i)).toBeInTheDocument();
    expect(screen.getByText(/Topological DAG Order/i)).toBeInTheDocument();
  });

  it("renders SqlArtifactViewer with non-negotiable review-only safety banner", () => {
    render(<SqlArtifactViewer artifact={SAMPLE_SQL_ARTIFACT} />);
    expect(screen.getAllByText(/GENERATED FOR REVIEW — NOT EXECUTED/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Dialect: POSTGRESQL/i).length).toBeGreaterThan(0);
  });

  it("enforces separation of duties in GovernanceReviewPanel against requester self-approval", () => {
    render(
      <GovernanceReviewPanel
        review={SAMPLE_GOVERNANCE_REVIEW}
        currentUserId={SAMPLE_GOVERNANCE_REVIEW.requester_id}
      />
    );

    const approveButton = screen.getByRole("button", { name: /Approve Migration/i });
    expect(approveButton).toBeDisabled();
    expect(screen.getByText(/self-approval is blocked by Separation of Duties/i)).toBeInTheDocument();
  });

  it("renders AuditEvidencePanel with hash-chained timeline and export gate", () => {
    render(
      <AuditEvidencePanel
        events={SAMPLE_AUDIT_EVENTS}
        review={SAMPLE_GOVERNANCE_REVIEW}
        artifact={SAMPLE_SQL_ARTIFACT}
      />
    );

    expect(screen.getByText(/Append-Only Audit Evidence Chain/i)).toBeInTheDocument();
    expect(screen.getByText(/Cryptographic Event Ledger/i)).toBeInTheDocument();
  });
});
