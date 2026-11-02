import React from "react";
import { cleanup, fireEvent, render, screen, within, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ExecutionPlanTree, metric, visibleNodes } from "@/components/execution-plans/ExecutionPlanTree";
import { ExecutionPlanExplorer } from "@/components/execution-plans/ExecutionPlanExplorer";
import type { PlanReport } from "@/components/execution-plans/types";
import fixture from "../fixtures/execution-plan.json";
import { apiClient } from "@/lib/api-client";

const report = fixture as PlanReport;
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe("Imported execution plan explorer", () => {
  it("formats missing and zero metrics distinctly", () => { expect(metric(null)).toBe("Unavailable"); expect(metric(0)).toBe("0"); });
  it("renders actual graph relationships and accessible table", () => {
    render(<ExecutionPlanTree report={report} selected={null} onSelect={vi.fn()} />);
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /n0000 · HASH_JOIN/ })).toBeInTheDocument();
    expect(screen.getAllByText("Unavailable").length).toBeGreaterThan(0);
    expect(screen.getByText("customers_pkey")).toBeInTheDocument();
  });
  it("selects nodes by keyboard-capable native buttons", () => {
    const select=vi.fn(); render(<ExecutionPlanTree report={report} selected={null} onSelect={select} />);
    fireEvent.click(screen.getByRole("button", { name: /n0001 · SCAN/ })); expect(select).toHaveBeenCalledWith("n0001");
  });
  it("collapses descendants without losing accessible table rows", () => {
    render(<ExecutionPlanTree report={report} selected="n0000" onSelect={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "Toggle n0000 subtree" }));
    expect(screen.queryByRole("button", { name: /n0001 · SCAN/ })).not.toBeInTheDocument();
    expect(within(screen.getByRole("table")).getByText("n0001")).toBeInTheDocument();
    expect(visibleNodes(report, new Set(["n0000"]))).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "Expand all" }));
    expect(screen.getByRole("button", { name: /n0001 · SCAN/ })).toBeInTheDocument();
  });
  it("zooms, fits, and pans using accessible controls", () => {
    Element.prototype.scrollBy=vi.fn(); Element.prototype.scrollTo=vi.fn();
    render(<ExecutionPlanTree report={report} selected={null} onSelect={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "Zoom in" })); expect(screen.getByLabelText("Zoom level")).toHaveTextContent("120%");
    fireEvent.click(screen.getByRole("button", { name: "Zoom out" })); expect(screen.getByLabelText("Zoom level")).toHaveTextContent("100%");
    fireEvent.click(screen.getByRole("button", { name: "Pan right" })); expect(Element.prototype.scrollBy).toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Fit to screen" })); expect(Element.prototype.scrollTo).toHaveBeenCalled();
  });
  it("shows empty and missing workspace states without demo data", () => {
    render(<ExecutionPlanExplorer workspaceId={null} />);
    expect(screen.getByRole("button", { name: "Analyze imported plan" })).toBeDisabled();
    expect(screen.getByText(/Select an authorized workspace/)).toBeInTheDocument();
    expect(screen.getByText(/Import a plan to explore/)).toBeInTheDocument();
  });
  it("shows loading then diagnostics and recommendation evidence", async () => {
    let resolve!: (r: PlanReport)=>void;
    vi.spyOn(apiClient,"analyzeExecutionPlan").mockReturnValue(new Promise(r=>{resolve=r;}));
    render(<ExecutionPlanExplorer workspaceId="workspace" />);
    fireEvent.change(screen.getByLabelText("Execution plan JSON"), { target: { value: "{}" } });
    fireEvent.click(screen.getByRole("button", { name: "Analyze imported plan" }));
    expect(screen.getByRole("status")).toHaveTextContent("Analyzing imported plan");
    resolve(report);
    await waitFor(()=>expect(screen.getByLabelText("Plan summary")).toBeInTheDocument());
    expect(screen.getByLabelText("Plan diagnostics")).toHaveTextContent("PLAN001");
    fireEvent.click(screen.getByRole("button",{name:/PLAN001 · n0001/}));
    expect(screen.getByLabelText("Node details")).toHaveTextContent("orders");
    expect(screen.getByLabelText("Plan recommendations")).toHaveTextContent("Large sequential scan");
  });
  it("handles unsupported results and sanitized errors", async () => {
    vi.spyOn(apiClient,"analyzeExecutionPlan").mockRejectedValue(new Error("sensitive SQL"));
    render(<ExecutionPlanExplorer workspaceId="workspace" />);
    fireEvent.change(screen.getByLabelText("Execution plan JSON"),{target:{value:"{}"}});
    fireEvent.click(screen.getByRole("button",{name:"Analyze imported plan"}));
    expect(await screen.findByRole("alert")).not.toHaveTextContent("sensitive SQL");
    vi.mocked(apiClient.analyzeExecutionPlan).mockResolvedValue({...report,status:"PARTIAL"});
    fireEvent.click(screen.getByRole("button",{name:"Analyze imported plan"}));
    expect(await screen.findByText("Partially supported plan")).toBeInTheDocument();
  });
});
