"use client";

import React, { useMemo, useRef, useState } from "react";
import type { PlanReport } from "./types";

export function metric(value: number | null | undefined): string {
  return value == null ? "Unavailable" : value.toLocaleString("en-US", { maximumFractionDigits: 6 });
}

export function visibleNodes(report: PlanReport, collapsed: Set<string>) {
  const nodes = new Map(report.nodes.map(n => [n.node_id, n]));
  return report.nodes.filter(n => {
    let parent = n.parent_id;
    while (parent) {
      if (collapsed.has(parent)) return false;
      parent = nodes.get(parent)?.parent_id ?? null;
    }
    return true;
  });
}

export function ExecutionPlanTree({ report, selected, onSelect }: {
  report: PlanReport; selected: string | null; onSelect: (id: string) => void;
}) {
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [zoom, setZoom] = useState(1);
  const [page, setPage] = useState(0);
  const viewport = useRef<HTMLDivElement>(null);
  const visible = useMemo(() => visibleNodes(report, collapsed), [report, collapsed]);
  const width = Math.max(800, ...visible.map(n => n.depth * 250 + 10));
  const height = Math.max(220, visible.length * 92 + 20);
  const positions = new Map(visible.map((n, i) => [n.node_id, { x: (n.depth - 1) * 250 + 10, y: i * 92 + 10 }]));
  function toggle(id: string) {
    setCollapsed(prev => { const next = new Set(prev); if (next.has(id)) next.delete(id); else next.add(id); return next; });
  }
  function pan(x: number, y: number) { viewport.current?.scrollBy({ left: x, top: y, behavior: "smooth" }); }
  return <section aria-label="Execution plan tree" className="space-y-3">
    <div className="flex flex-wrap gap-2" aria-label="Plan view controls">
      <button type="button" onClick={() => setZoom(z => Math.min(2, z + .2))}>Zoom in</button>
      <button type="button" onClick={() => setZoom(z => Math.max(.1, z - .2))}>Zoom out</button>
      <button type="button" onClick={() => { setZoom(Math.max(.1, Math.min(1, (viewport.current?.clientWidth || 800) / width, 450 / height))); viewport.current?.scrollTo({ left: 0, top: 0 }); }}>Fit to screen</button>
      <button type="button" onClick={() => pan(-200, 0)}>Pan left</button>
      <button type="button" onClick={() => pan(200, 0)}>Pan right</button>
      <button type="button" onClick={() => pan(0, -200)}>Pan up</button>
      <button type="button" onClick={() => pan(0, 200)}>Pan down</button>
      <button type="button" onClick={() => { setCollapsed(new Set()); setZoom(1); }}>Expand all</button>
      {selected && <button type="button" aria-expanded={!collapsed.has(selected)} onClick={() => toggle(selected)}>Toggle selected subtree</button>}
      <output aria-label="Zoom level">{Math.round(zoom * 100)}%</output>
    </div>
    <p className="text-sm text-slate-500">Scroll to pan. Use Tab to select nodes, or use the structured table below. Costs are inclusive estimates, not milliseconds.</p>
    <div ref={viewport} tabIndex={0} role="region" aria-label="Scrollable plan canvas" className="h-[450px] overflow-auto rounded-xl border bg-slate-50 dark:bg-slate-950">
      <div style={{ width: width * zoom, height: height * zoom, position: "relative" }}>
        <div style={{ width, height, transform: `scale(${zoom})`, transformOrigin: "top left", position: "absolute" }}>
          <svg aria-hidden="true" width={width} height={height} style={{ position: "absolute", pointerEvents: "none" }}>
            {visible.map(n => { const a = n.parent_id ? positions.get(n.parent_id) : null; const b = positions.get(n.node_id)!;
              return a ? <path key={n.node_id} d={`M${a.x + 220},${a.y + 35} H${a.x + 235} V${b.y + 35} H${b.x}`} fill="none" stroke="#64748b" /> : null; })}
          </svg>
          {visible.map(n => { const p = positions.get(n.node_id)!; const count = report.diagnostics.filter(d => d.node_id === n.node_id).length;
            return <button type="button" key={n.node_id} aria-pressed={selected === n.node_id} onClick={() => onSelect(n.node_id)}
              style={{ position: "absolute", left: p.x, top: p.y, width: 220, height: 76 }}
              className={`rounded-lg border p-2 text-left text-xs bg-white dark:bg-slate-900 focus-visible:outline-2 focus-visible:outline-blue-600 ${selected === n.node_id ? "border-blue-600 ring-2 ring-blue-400" : "border-slate-300"}`}>
              <strong className="block truncate">{n.node_id} · {n.operation}</strong>
              <span className="block truncate">{n.relation.name || n.native_operation}</span>
              <span>Rows {metric(n.estimate.rows)} · Cost {metric(n.estimate.total)}</span>
              {count > 0 && <span className="ml-1 text-amber-700">{count} findings</span>}
            </button>; })}
        </div>
      </div>
    </div>
    <div className="overflow-x-auto">
      <table className="w-full text-sm"><caption>Accessible plan table · all nodes, 100 per page</caption>
        <thead><tr>{["Node", "Parent", "Operation", "Estimated rows", "Actual rows", "Estimated cost", "Index", "Subtree"].map(s => <th key={s} scope="col" className="p-2 text-left">{s}</th>)}</tr></thead>
        <tbody>{report.nodes.slice(page * 100, (page + 1) * 100).map(n => <tr key={n.node_id}>
          <td><button type="button" onClick={() => onSelect(n.node_id)}>{n.node_id}</button></td><td>{n.parent_id || "Root"}</td><td>{n.native_operation}</td>
          <td>{metric(n.estimate.rows)}</td><td>{metric(n.actual.rows)}</td><td>{metric(n.estimate.total)}</td><td>{n.relation.index_name || "Not reported"}</td>
          <td>{n.child_ids.length > 0 && <button type="button" aria-expanded={!collapsed.has(n.node_id)} aria-label={`Toggle ${n.node_id} subtree`} onClick={() => toggle(n.node_id)}>{collapsed.has(n.node_id) ? "Expand" : "Collapse"}</button>}</td>
        </tr>)}</tbody>
      </table>
      <button type="button" disabled={page === 0} onClick={() => setPage(p => p - 1)}>Previous nodes</button>
      <button type="button" disabled={(page + 1) * 100 >= report.nodes.length} onClick={() => setPage(p => p + 1)}>Next nodes</button>
    </div>
  </section>;
}
