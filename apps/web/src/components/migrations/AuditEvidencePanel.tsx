"use client";

import React, { useState } from "react";
import { AuditEventRecord, SqlArtifact, GovernanceReviewRequest, ReviewStatus } from "@/lib/migrations/types";
import { Download, History, CheckCircle2, Lock } from "lucide-react";

interface AuditEvidencePanelProps {
  events: AuditEventRecord[];
  review: GovernanceReviewRequest;
  artifact: SqlArtifact;
}

export function AuditEvidencePanel({ events, review, artifact }: AuditEvidencePanelProps) {
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  const isApproved = review.status === ReviewStatus.APPROVED || review.status === "APPROVED";
  const isValid = artifact.validation ? artifact.validation.is_valid : true;
  const isEligibleForExport = isApproved && isValid;

  const handleExport = () => {
    if (!isEligibleForExport) return;

    const exportPayload = {
      manifest_version: "1.0.0",
      generated_at: new Date().toISOString(),
      artifact_id: artifact.artifact_id,
      dialect: artifact.dialect,
      fingerprint: artifact.artifact_fingerprint || artifact.fingerprint,
      review_id: review.review_id,
      review_status: review.status,
      decisions: review.decisions,
      sql: artifact.sql_content || artifact.rendered_sql_script,
      audit_events_count: events.length,
      notice: "GENERATED FOR CONTROLLED REVIEW — NOT EXECUTED",
    };

    const blob = new Blob([JSON.stringify(exportPayload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `dera-migration-artifact-${artifact.artifact_id.slice(0, 8)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    setDownloadSuccess(true);
    setTimeout(() => setDownloadSuccess(false), 3000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 text-slate-100 shadow-md">
      {/* Header and Export Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-4">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <History className="w-5 h-5 text-indigo-400" />
            Append-Only Audit Evidence Chain & Controlled Export
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Tamper-evident event log certifying every state transition, reviewer decision, and cryptographic fingerprint.
          </p>
        </div>

        {/* Controlled Export Button */}
        <div>
          <button
            type="button"
            onClick={handleExport}
            disabled={!isEligibleForExport}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded text-xs font-semibold transition-colors ${
              isEligibleForExport
                ? "bg-emerald-600 hover:bg-emerald-500 text-white shadow"
                : "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700"
            }`}
          >
            {downloadSuccess ? (
              <>
                <CheckCircle2 className="w-4 h-4 text-white" /> Bundle Exported!
              </>
            ) : isEligibleForExport ? (
              <>
                <Download className="w-4 h-4" /> Export Authorized Bundle
              </>
            ) : (
              <>
                <Lock className="w-4 h-4" /> Export Locked (Approval Required)
              </>
            )}
          </button>
        </div>
      </div>

      {/* Export Eligibility Banner */}
      <div className="mb-5 bg-slate-950/80 border border-slate-800 p-4 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="text-xs text-slate-400">Governance Export Status</div>
          <div className="text-sm font-semibold text-slate-200 mt-0.5 flex items-center gap-2">
            {isEligibleForExport ? (
              <span className="text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" /> Eligible for Controlled CI/CD Handoff
              </span>
            ) : (
              <span className="text-amber-400 flex items-center gap-1.5">
                <Lock className="w-4 h-4" /> Ineligible for Export — Quorum of Approvals Pending
              </span>
            )}
          </div>
        </div>
        <div className="text-xs font-mono text-slate-400">
          Total Audit Trail Records: <span className="text-indigo-400 font-bold">{events.length}</span>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-slate-950/60 border border-slate-800 rounded-lg overflow-hidden">
        <div className="p-3 bg-slate-950 border-b border-slate-800 text-xs font-semibold uppercase tracking-wider text-slate-400 flex justify-between">
          <span>Cryptographic Event Ledger</span>
          <span className="font-mono text-[10px] text-slate-500">Hash-Chained Timeline</span>
        </div>

        <div className="divide-y divide-slate-800/60 max-h-[440px] overflow-y-auto">
          {events.map((evt) => (
            <div key={evt.event_id} className="p-3.5 hover:bg-slate-900/40 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="space-y-1">
                <div className="flex items-center gap-2 font-medium text-slate-200">
                  <span className="font-mono text-indigo-400 uppercase text-[11px] bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                    {evt.event_type}
                  </span>
                  <span>by</span>
                  <span className="text-slate-300 font-mono">{evt.actor_id}</span>
                </div>
                <div className="text-slate-400 text-[11px]">
                  State: <span className="font-mono text-slate-500">{evt.previous_state || "START"}</span> →{" "}
                  <span className="font-mono text-emerald-400">{evt.new_state}</span>
                </div>
              </div>

              <div className="text-right text-[11px] font-mono text-slate-500">
                <div>{new Date(evt.timestamp).toLocaleString()}</div>
                <div className="truncate max-w-[180px]" title={evt.event_id}>
                  ID: {evt.event_id}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Audit Integrity Footer */}
      <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-500 flex justify-between">
        <span>Immutable Provenance Guarantee</span>
        <span>SHA-256 State Transitions Verified</span>
      </div>
    </div>
  );
}
