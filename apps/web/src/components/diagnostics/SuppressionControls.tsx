"use client";

import React, { useState } from "react";
import { DiagnosticFinding } from "@/lib/diagnostics/types";
import { Shield, ShieldAlert, ShieldCheck, Clock, X, AlertTriangle } from "lucide-react";

interface SuppressionControlsProps {
  finding: DiagnosticFinding;
  onApplySuppression?: (fingerprint: string, reason: string, durationDays: number) => void;
  onRevokeSuppression?: (fingerprint: string) => void;
  className?: string;
}

export function SuppressionControls({
  finding,
  onApplySuppression,
  onRevokeSuppression,
  className = "",
}: SuppressionControlsProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [durationDays, setDurationDays] = useState(30);

  const handleSubmitSuppression = (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim()) return;
    onApplySuppression?.(finding.fingerprint, reason.trim(), durationDays);
    setIsModalOpen(false);
    setReason("");
  };

  return (
    <div className={`rounded-md border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {finding.is_suppressed ? (
            <ShieldCheck className="h-4 w-4 text-amber-500" />
          ) : (
            <Shield className="h-4 w-4 text-slate-400" />
          )}
          <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
            Suppression Governance
          </span>
        </div>

        {finding.is_suppressed ? (
          <button
            type="button"
            disabled={!onRevokeSuppression}
            onClick={() => onRevokeSuppression?.(finding.fingerprint)}
            className="rounded-sm bg-red-50 px-2 py-1 text-[11px] font-medium text-red-700 hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-red-950/40 dark:text-red-300 dark:hover:bg-red-900/50"
            title={onRevokeSuppression ? "Revoke this exemption" : "Suppression mutation not available in current mode"}
          >
            Revoke Exemption
          </button>
        ) : (
          <button
            type="button"
            disabled={!onApplySuppression}
            onClick={() => setIsModalOpen(true)}
            className="rounded-sm bg-slate-100 px-2 py-1 text-[11px] font-medium text-slate-700 hover:bg-slate-200 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
            title={onApplySuppression ? "Exempt finding from diagnostics" : "Suppression mutation not available in current mode"}
          >
            Exempt Finding
          </button>
        )}
      </div>

      {finding.is_suppressed && (
        <div className="mt-2 text-[11px] text-slate-500 dark:text-slate-400">
          <p>
            <span className="font-medium text-slate-700 dark:text-slate-300">Status: </span>
            Active suppression recorded ({finding.suppression_id || "Governance Policy"})
          </p>
          <p className="mt-0.5 text-[10px] text-slate-400">
            Suppressed findings remain auditable in compliance reports.
          </p>
        </div>
      )}

      {/* Exemption Modal */}
      {isModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="suppression-dialog-title"
        >
          <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-5 shadow-lg dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-3 flex items-center justify-between">
              <h3
                id="suppression-dialog-title"
                className="text-sm font-semibold text-slate-900 dark:text-slate-100"
              >
                Apply Diagnostic Exemption
              </h3>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="rounded-sm p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                aria-label="Close dialog"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <p className="mb-3 text-xs text-slate-500 dark:text-slate-400">
              Exempting <span className="font-mono text-slate-700 dark:text-slate-200">{finding.rule_id}</span> on{" "}
              <span className="font-mono text-slate-700 dark:text-slate-200">{finding.object_id}</span>.
            </p>

            <form onSubmit={handleSubmitSuppression} className="space-y-3">
              <div>
                <label
                  htmlFor="suppression-reason"
                  className="block text-xs font-medium text-slate-700 dark:text-slate-300"
                >
                  Justification (Mandatory)
                </label>
                <textarea
                  id="suppression-reason"
                  required
                  rows={3}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="e.g. Legacy partitioned table exempt from wide table rule per architecture review ADR-042."
                  className="mt-1 w-full rounded-md border border-slate-300 p-2 text-xs text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:outline-hidden dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
                />
              </div>

              <div>
                <label
                  htmlFor="suppression-duration"
                  className="block text-xs font-medium text-slate-700 dark:text-slate-300"
                >
                  Expiration Window
                </label>
                <select
                  id="suppression-duration"
                  value={durationDays}
                  onChange={(e) => setDurationDays(Number(e.target.value))}
                  className="mt-1 w-full rounded-md border border-slate-300 bg-white p-1.5 text-xs text-slate-900 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
                >
                  <option value={7}>7 Days (Temporary Review)</option>
                  <option value={30}>30 Days (Sprint Cycle)</option>
                  <option value={90}>90 Days (Quarterly Waiver)</option>
                  <option value={365}>1 Year (Permanent Architectural Decision)</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="rounded-md border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 focus:outline-hidden"
                >
                  Confirm Exemption
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
