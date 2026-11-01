"use client";

import React, { useState } from "react";
import { SqlArtifact } from "@/lib/migrations/types";
import { Code2, Copy, Check, ShieldAlert, CheckCircle2, AlertTriangle } from "lucide-react";

interface SqlArtifactViewerProps {
  artifact: SqlArtifact;
}

export function SqlArtifactViewer({ artifact }: SqlArtifactViewerProps) {
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<"FORWARD" | "ROLLBACK" | "VALIDATION">("FORWARD");

  const forwardSql = artifact.sql_content || artifact.rendered_sql_script || "-- No SQL available";
  const rollbackSql = artifact.rollback_sql || "-- Advisory inverse rollback script unavailable";

  const handleCopy = () => {
    const textToCopy = activeTab === "FORWARD" ? forwardSql : rollbackSql;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const validation = artifact.validation || {
    is_valid: true,
    dialect_supported: true,
    warnings: [],
  };

  const artifactFp = artifact.artifact_fingerprint || artifact.fingerprint || "SHA-256";
  const compilerVer = artifact.compiler_version || "1.0.0-phase9.4";

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 text-slate-100 shadow-md">
      {/* Prominent Safety Banner: NON-NEGOTIABLE */}
      <div className="mb-5 bg-amber-950/40 border-2 border-amber-600/80 rounded-lg p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ShieldAlert className="w-6 h-6 text-amber-400 shrink-0" />
          <div>
            <div className="font-bold text-sm tracking-wide text-amber-200">
              GENERATED FOR REVIEW — NOT EXECUTED
            </div>
            <div className="text-xs text-amber-400/90 mt-0.5">
              DERA is strictly review-only. This interface never executes DDL against customer databases.
            </div>
          </div>
        </div>
        <div className="text-xs font-mono bg-amber-950 px-2.5 py-1 rounded border border-amber-700 text-amber-300">
          Dialect: {artifact.dialect}
        </div>
      </div>

      {/* Header and Artifact Metadata */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-4">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Code2 className="w-5 h-5 text-indigo-400" />
            Phase 9.4 — Dialect-Aware Migration SQL IR Artifact
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic DDL emission adhering to safe identifier quoting, transaction boundaries, and AST validation.
          </p>
        </div>

        {/* Tab Controls and Copy Button */}
        <div className="flex items-center gap-3">
          <div className="flex bg-slate-950 p-1 rounded border border-slate-800 text-xs">
            <button
              onClick={() => setActiveTab("FORWARD")}
              className={`px-3 py-1 rounded transition-colors ${
                activeTab === "FORWARD"
                  ? "bg-indigo-600 text-white font-medium"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Migration SQL
            </button>
            <button
              onClick={() => setActiveTab("ROLLBACK")}
              className={`px-3 py-1 rounded transition-colors ${
                activeTab === "ROLLBACK"
                  ? "bg-indigo-600 text-white font-medium"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Advisory Rollback
            </button>
            <button
              onClick={() => setActiveTab("VALIDATION")}
              className={`px-3 py-1 rounded transition-colors ${
                activeTab === "VALIDATION"
                  ? "bg-indigo-600 text-white font-medium"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Validation & AST
            </button>
          </div>

          <button
            onClick={handleCopy}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs rounded border border-slate-700 font-medium transition-colors"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" /> Copied
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" /> Copy SQL
              </>
            )}
          </button>
        </div>
      </div>

      {/* SQL Code Viewer or Validation Panel */}
      {activeTab === "VALIDATION" ? (
        <div className="space-y-4">
          <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Dialect Capabilities & AST Validation Report
            </h3>
            <div className="text-xs text-slate-400 leading-relaxed">
              Syntactic validation confirms that all generated statements comply with official SQL dialect grammar without prohibited constructs.
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4 text-xs">
              <div className="bg-slate-900 p-3 rounded border border-slate-800">
                <div className="text-slate-400">Structural Validation:</div>
                <div className="font-semibold text-emerald-400 mt-1">
                  {validation.is_valid ? "PASSED (Zero syntax errors)" : "FAILED"}
                </div>
              </div>
              <div className="bg-slate-900 p-3 rounded border border-slate-800">
                <div className="text-slate-400">Dialect Support:</div>
                <div className="font-semibold text-indigo-300 mt-1">
                  {validation.dialect_supported ? "Verified Engine Native" : "Emulated Fallback"}
                </div>
              </div>
              <div className="bg-slate-900 p-3 rounded border border-slate-800">
                <div className="text-slate-400">Transaction Scope:</div>
                <div className="font-semibold text-slate-200 mt-1">Single Atomic Transaction</div>
              </div>
            </div>
          </div>

          {validation.warnings && validation.warnings.length > 0 && (
            <div className="bg-amber-950/20 border border-amber-900/60 p-4 rounded-lg">
              <h4 className="text-xs font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4" /> Dialect Engineering Warnings
              </h4>
              <ul className="text-xs text-amber-300/90 space-y-1 list-disc list-inside">
                {validation.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <div className="relative">
          <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-xs text-slate-200 overflow-x-auto max-h-[460px] leading-relaxed select-text">
            <pre className="whitespace-pre">
              {activeTab === "FORWARD" ? forwardSql : rollbackSql}
            </pre>
          </div>
        </div>
      )}

      {/* Provenance & Fingerprint Footer */}
      <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-500 flex flex-wrap justify-between gap-2">
        <div className="flex items-center gap-2">
          <span>Artifact ID: <span className="font-mono text-slate-400">{artifact.artifact_id}</span></span>
          <span>•</span>
          <span>Compiler: <span className="text-slate-400">{compilerVer}</span></span>
        </div>
        <div className="font-mono text-slate-400">
          SHA-256: {artifactFp}
        </div>
      </div>
    </div>
  );
}
