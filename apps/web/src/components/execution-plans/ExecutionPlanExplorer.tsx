"use client";

import React, { useEffect, useRef, useState } from "react";
import { apiClient } from "@/lib/api-client";
import { ExecutionPlanTree, metric } from "./ExecutionPlanTree";
import type { PlanReport, PlanRequest } from "./types";

const formats: Record<PlanRequest["dialect"], PlanRequest["format"]> = { postgresql: "postgresql-json", mysql: "mysql-json-v1", mariadb: "mariadb-json", sqlite: "sqlite-eqp" };

export function ExecutionPlanExplorer({ workspaceId }: { workspaceId: string | null }) {
  const [dialect, setDialect] = useState<PlanRequest["dialect"]>("postgresql");
  const [input, setInput] = useState("");
  const [sql, setSql] = useState("");
  const [report, setReport] = useState<PlanReport | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pending = useRef<AbortController | null>(null);
  useEffect(() => () => pending.current?.abort(), []);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!workspaceId || !input.trim()) return;
    pending.current?.abort();
    const controller = new AbortController(); pending.current = controller;
    setError(null); setReport(null); setLoading(true); setSelected(null);
    try {
      if (new TextEncoder().encode(input).length > 1048576) throw new Error("size");
      const data = await apiClient.analyzeExecutionPlan(workspaceId, { dialect, format: formats[dialect], plan_json: input, ...(sql ? { sql } : {}) }, controller.signal);
      if (!controller.signal.aborted) { setReport(data); setSelected(data.root_ids[0] || null); }
    } catch {
      if (!controller.signal.aborted) setError("Unable to analyze this import. Check the format, size, workspace access and session.");
    } finally { if (!controller.signal.aborted) setLoading(false); }
  }
  const node = report?.nodes.find(n => n.node_id === selected);
  return <div className="mx-auto max-w-[1600px] space-y-6 p-4 md:p-8">
    <header><p className="text-xs font-semibold uppercase tracking-widest text-blue-600">SQL engineering · imported evidence</p><h1 className="text-3xl font-bold">Execution plan explorer</h1>
      <p className="mt-2 text-slate-500">Analyze externally supplied plans. DERA does not execute SQL or acquire live plans. Static indicators are not measured speed improvements.</p></header>
    <form onSubmit={submit} className="space-y-3 rounded-xl border p-4">
      <label className="block">Database dialect <select value={dialect} onChange={e => setDialect(e.target.value as PlanRequest["dialect"])} className="ml-3 rounded border p-2">{Object.keys(formats).map(d => <option key={d}>{d}</option>)}</select></label>
      <p className="text-sm">Required format: {formats[dialect]}. SQLite: JSON array of id, parent, notused, detail rows. Maximum 1 MiB, 1,000 nodes.</p>
      <label className="block" htmlFor="plan-import">Execution plan JSON</label>
      <textarea id="plan-import" value={input} onChange={e => setInput(e.target.value)} maxLength={1048576} rows={8} required spellCheck={false} className="w-full rounded border bg-transparent p-3 font-mono text-xs" />
      <label className="block" htmlFor="associated-sql">Associated SQL (optional, static diagnostics only)</label>
      <textarea id="associated-sql" value={sql} onChange={e => setSql(e.target.value)} maxLength={16384} rows={2} className="w-full rounded border bg-transparent p-2 font-mono text-xs" />
      <button type="submit" disabled={!workspaceId || loading || !input.trim()} className="rounded bg-blue-600 px-4 py-2 font-medium text-white disabled:opacity-50">{loading ? "Analyzing…" : "Analyze imported plan"}</button>
      {!workspaceId && <p role="status">Select an authorized workspace to analyze a plan.</p>}
    </form>
    {loading && <p role="status" aria-live="polite">Analyzing imported plan…</p>}
    {error && <p role="alert" className="rounded border border-red-400 p-4">{error}</p>}
    {!report && !loading && !error && <p>Import a plan to explore operations, evidence and metrics.</p>}
    {report && <>
      <section aria-label="Plan summary" className="rounded-xl border p-4"><h2 className="text-lg font-semibold">{report.status === "PARTIAL" ? "Partially supported plan" : "Plan summary"}</h2>
        <p>{report.summary.node_count} nodes · Depth {report.summary.max_depth} · {report.diagnostics.length} findings</p>
        <p>Estimated inclusive cost: {metric(report.summary.estimated_total_cost)} · Imported execution time: {metric(report.summary.execution_time_ms)} ms</p>
        <p className="text-sm text-slate-500">{report.summary.cost_limitation}</p>
        <p className="break-all font-mono text-xs">Fingerprint: {report.plan_fingerprint}</p>
      </section>
      <ExecutionPlanTree key={report.plan_fingerprint} report={report} selected={selected} onSelect={setSelected} />
      <div className="grid gap-4 lg:grid-cols-2">
        <section aria-label="Node details" className="min-w-0 rounded-xl border p-4"><h2 className="text-lg font-semibold">Node details · {node?.node_id}</h2>
          {node && <><p>{node.native_operation} · {node.relation.name || "No relation reported"}</p>
            <dl className="grid grid-cols-2 gap-2 text-sm">{Object.entries({ "Estimated rows": metric(node.estimate.rows), "Actual rows": metric(node.actual.rows), "Actual loops": metric(node.actual.loops), "Node time (ms)": metric(node.actual.total_time_ms), "Index": node.relation.index_name || "Not reported", "Cost units": node.estimate.unit, "Row ratio": metric(node.actual.row_estimation_ratio) }).map(([key, value]) => <React.Fragment key={key}><dt>{key}</dt><dd>{value}</dd></React.Fragment>)}</dl>
            <p className="mt-3 text-xs">{node.actual.row_semantics}. {node.actual.time_semantics}.</p>
            <details className="mt-3"><summary>Native node metadata (may contain sensitive literals)</summary><pre className="max-h-64 overflow-auto whitespace-pre-wrap break-all text-xs">{node.metadata_json}</pre></details></>}
        </section>
        <section aria-label="Plan diagnostics" className="rounded-xl border p-4"><h2 className="text-lg font-semibold">Diagnostics and investigations</h2>
          {!report.diagnostics.length && <p>No configured rule matched. This does not prove the plan is optimal.</p>}
          <ul className="max-h-[500px] space-y-3 overflow-auto">{report.diagnostics.map(f => <li key={f.finding_id} className="rounded border p-3 text-sm">
            <button type="button" onClick={() => setSelected(f.node_id)} className="font-semibold text-blue-600">{f.rule_id} · {f.node_id} · {f.severity}</button>
            <p>{f.explanation}</p><p>{f.evidence.join(" ")}</p><p className="mt-1">{f.suggested_investigation}</p>
            <p className="text-xs text-slate-500">{f.limitations.join(" ")} Runtime verification required.</p>
          </li>)}</ul>
        </section>
      </div>
      <section aria-label="Plan recommendations" className="rounded-xl border p-4"><h2 className="text-lg font-semibold">Recommendations · manual review required</h2>
        <ul>{report.recommendations.filter(r => r.node_id === selected).map(r => <li key={r.recommendation_id}><strong>{r.title}</strong><p>{r.suggested_action}</p><p>{r.expected_benefit}</p><p className="text-xs text-slate-500">{r.limitations.join(" ")}</p></li>)}</ul>
        {report.sql_diagnostics && <p>Associated SQL diagnostics: {report.sql_diagnostics.analysis_status}, {report.sql_diagnostics.total_findings} findings. Plan correspondence is unverified.</p>}
      </section>
    </>}
  </div>;
}
