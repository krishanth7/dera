"use client";

import React, { useState } from "react";
import {
  GovernanceReviewRequest,
  ReviewDecisionType,
  ReviewDecision,
  ReviewStatus,
} from "@/lib/migrations/types";
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Users,
  FileCheck,
  Clock,
  RotateCcw,
} from "lucide-react";

interface GovernanceReviewPanelProps {
  review: GovernanceReviewRequest;
  currentUserId?: string;
  onRecordDecision?: (decision: ReviewDecisionType, rationale: string) => void;
}

export function GovernanceReviewPanel({
  review: initialReview,
  currentUserId = "usr-reviewer-lead",
  onRecordDecision,
}: GovernanceReviewPanelProps) {
  const [review, setReview] = useState<GovernanceReviewRequest>(initialReview);
  const [rationale, setRationale] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localFeedback, setLocalFeedback] = useState<string | null>(null);

  const isRequester = currentUserId === review.requester_id;
  const isApproved = review.status === ReviewStatus.APPROVED;
  const isRejected = review.status === ReviewStatus.REJECTED;

  const handleDecision = (decisionType: ReviewDecisionType) => {
    if (!rationale.trim()) {
      setLocalFeedback("Please provide a technical rationale for your governance decision.");
      return;
    }

    if (decisionType === ReviewDecisionType.APPROVE && isRequester) {
      setLocalFeedback("Separation of Duties Violation: Requester cannot self-approve migration artifacts.");
      return;
    }

    setIsSubmitting(true);
    setLocalFeedback(null);

    const newDecision: ReviewDecision = {
      decision_id: `dec-${Date.now().toString(36)}`,
      reviewer_id: currentUserId,
      reviewer_role: "Database Engineering Lead",
      decision: decisionType,
      rationale: rationale.trim(),
      decided_at: new Date().toISOString(),
    };

    setTimeout(() => {
      setReview((prev) => {
        const updatedDecisions = [...prev.decisions, newDecision];
        let nextStatus = prev.status;
        const requiredApprovals = prev.required_approvals ?? 1;

        if (decisionType === ReviewDecisionType.APPROVE) {
          const approveCount = updatedDecisions.filter(
            (d) => d.decision === ReviewDecisionType.APPROVE || d.decision_type === "APPROVE"
          ).length;
          if (approveCount >= requiredApprovals) {
            nextStatus = ReviewStatus.APPROVED;
          }
        } else if (decisionType === ReviewDecisionType.REJECT) {
          nextStatus = ReviewStatus.REJECTED;
        } else if (decisionType === ReviewDecisionType.REQUEST_CHANGES) {
          nextStatus = ReviewStatus.CHANGES_REQUESTED;
        }

        return {
          ...prev,
          status: nextStatus,
          decisions: updatedDecisions,
        };
      });

      if (onRecordDecision) {
        onRecordDecision(decisionType, rationale.trim());
      }

      setRationale("");
      setIsSubmitting(false);
    }, 400);
  };

  const getStatusBadge = (status: ReviewStatus | string) => {
    switch (status) {
      case ReviewStatus.APPROVED:
      case "APPROVED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded text-xs font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" /> APPROVED
          </span>
        );
      case ReviewStatus.REJECTED:
      case "REJECTED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded text-xs font-bold bg-rose-950 text-rose-300 border border-rose-800">
            <XCircle className="w-4 h-4 text-rose-400" /> REJECTED
          </span>
        );
      case ReviewStatus.CHANGES_REQUESTED:
      case "CHANGES_REQUESTED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded text-xs font-semibold bg-amber-950 text-amber-300 border border-amber-800">
            <RotateCcw className="w-4 h-4 text-amber-400" /> CHANGES REQUESTED
          </span>
        );
      case ReviewStatus.PENDING:
      case ReviewStatus.UNDER_REVIEW:
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded text-xs font-semibold bg-indigo-950 text-indigo-300 border border-indigo-800">
            <Clock className="w-4 h-4 text-indigo-400" /> UNDER REVIEW
          </span>
        );
    }
  };

  const requiredApprovals = review.required_approvals ?? 1;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 text-slate-100 shadow-md">
      {/* Header and Review Metadata */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-4">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            Phase 9.5 — Governance Review, Approval & Safety Controls
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Mandatory human engineering sign-off, four-eyes principle (SoD), and cryptographic artifact hashing.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-xs bg-slate-950 px-3 py-1.5 rounded border border-slate-800">
            <span className="text-slate-400">Policy: </span>
            <span className="font-mono text-slate-200">v{review.policy_version || "1.0.0"}</span>
          </div>
          <div>{getStatusBadge(review.status)}</div>
        </div>
      </div>

      {/* Quorum Progress Banner */}
      <div className="mb-5 bg-slate-950/80 border border-slate-800 p-4 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="text-xs text-slate-400">Approval Quorum Requirement</div>
          <div className="text-sm font-semibold text-slate-200 mt-0.5">
            {review.decisions.filter((d) => d.decision === ReviewDecisionType.APPROVE || d.decision_type === "APPROVE").length} of{" "}
            {requiredApprovals} Required Sign-Offs Satisfied
          </div>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono">
          <div>
            <span className="text-slate-500">Separation of Duties: </span>
            <span className="text-emerald-400 font-semibold">ENFORCED</span>
          </div>
          <div>
            <span className="text-slate-500">Current Actor: </span>
            <span className="text-indigo-400">{currentUserId}</span>
          </div>
        </div>
      </div>

      {/* Review Decisions and Form */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Past Decisions History */}
        <div className="lg:col-span-6 bg-slate-950/60 border border-slate-800 rounded-lg p-4 flex flex-col justify-between max-h-[480px]">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
              <Users className="w-4 h-4 text-slate-400" />
              Recorded Review Decisions ({review.decisions.length})
            </h3>
            <div className="space-y-3 overflow-y-auto max-h-[380px] pr-1">
              {review.decisions.length === 0 ? (
                <div className="text-xs text-slate-500 p-4 text-center">
                  No decisions have been submitted yet. Awaiting authorized peer reviews.
                </div>
              ) : (
                review.decisions.map((d) => {
                  const decType = d.decision || d.decision_type || "APPROVE";
                  const dateStr = d.decided_at || d.timestamp || new Date().toISOString();
                  return (
                    <div key={d.decision_id} className="bg-slate-900 border border-slate-800 p-3 rounded text-xs space-y-1.5">
                      <div className="flex items-center justify-between">
                        <div className="font-semibold text-slate-200">{d.reviewer_role}</div>
                        <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${
                          decType === ReviewDecisionType.APPROVE || decType === "APPROVE"
                            ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                            : decType === ReviewDecisionType.REJECT || decType === "REJECT"
                            ? "bg-rose-950 text-rose-300 border border-rose-800"
                            : "bg-amber-950 text-amber-300 border border-amber-800"
                        }`}>
                          {decType}
                        </span>
                      </div>
                      <div className="text-slate-400 leading-normal">{d.rationale || d.reason}</div>
                      <div className="flex justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-800/60">
                        <span>Reviewer: {d.reviewer_id}</span>
                        <span>{new Date(dateStr).toLocaleString()}</span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Submit Decision Interface */}
        <div className="lg:col-span-6 bg-slate-950/60 border border-slate-800 rounded-lg p-4 flex flex-col justify-between">
          <div className="space-y-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <FileCheck className="w-4 h-4 text-indigo-400" />
              Submit Authorized Review Decision
            </h3>

            {localFeedback && (
              <div className="p-3 bg-rose-950/50 border border-rose-800 rounded text-xs text-rose-300 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                {localFeedback}
              </div>
            )}

            <div>
              <label htmlFor="rationale-input" className="block text-xs text-slate-300 mb-1.5 font-medium">
                Technical Review Rationale & Findings Assessment
              </label>
              <textarea
                id="rationale-input"
                rows={4}
                value={rationale}
                onChange={(e) => setRationale(e.target.value)}
                placeholder="Document your verification of dialect suitability, blast radius, rollback precautions, and test validation..."
                className="w-full bg-slate-900 border border-slate-700 rounded-md p-3 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div className="bg-slate-900/80 p-3 rounded border border-slate-800 text-[11px] text-slate-400 space-y-1">
              <div>• Requester ID: <span className="font-mono text-slate-300">{review.requester_id}</span></div>
              <div>• Artifact SHA-256: <span className="font-mono text-slate-300">{review.artifact_fingerprint.slice(0, 24)}...</span></div>
              {isRequester && (
                <div className="text-amber-400 pt-1 font-medium">
                  Notice: You are the author of this request. You may request changes or reject, but self-approval is blocked by Separation of Duties policy.
                </div>
              )}
            </div>

            {/* Decision Action Buttons */}
            <div className="flex flex-wrap gap-2.5 pt-2">
              <button
                type="button"
                onClick={() => handleDecision(ReviewDecisionType.APPROVE)}
                disabled={isSubmitting || isRequester || isApproved}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 text-white rounded text-xs font-semibold transition-colors"
              >
                <CheckCircle2 className="w-4 h-4" /> Approve Migration
              </button>
              <button
                type="button"
                onClick={() => handleDecision(ReviewDecisionType.REQUEST_CHANGES)}
                disabled={isSubmitting}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-amber-600 hover:bg-amber-500 disabled:bg-slate-800 disabled:text-slate-500 text-white rounded text-xs font-semibold transition-colors"
              >
                <RotateCcw className="w-4 h-4" /> Request Changes
              </button>
              <button
                type="button"
                onClick={() => handleDecision(ReviewDecisionType.REJECT)}
                disabled={isSubmitting || isRejected}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-rose-600 hover:bg-rose-500 disabled:bg-slate-800 disabled:text-slate-500 text-white rounded text-xs font-semibold transition-colors"
              >
                <XCircle className="w-4 h-4" /> Reject Artifact
              </button>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-500 flex justify-between">
            <span>Review ID: {review.review_id}</span>
            <span>Cryptographic State Integrity</span>
          </div>
        </div>
      </div>
    </div>
  );
}
