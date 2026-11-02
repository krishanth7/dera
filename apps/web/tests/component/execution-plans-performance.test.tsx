import React from "react";
import { writeFileSync } from "node:fs";
import { render, cleanup } from "@testing-library/react";
import { expect, it } from "vitest";
import { ExecutionPlanTree } from "@/components/execution-plans/ExecutionPlanTree";
import type { PlanReport } from "@/components/execution-plans/types";
import fixture from "../fixtures/execution-plan.json";

it("qualifies synthetic 10/100/1000-node DOM rendering without timing assertions", () => {
  const base=fixture as PlanReport;
  const results=[];
  for (const count of [10,100,1000]) {
    const report: PlanReport={...base,diagnostics:[],nodes:Array.from({length:count},(_,i)=>({...base.nodes[0],node_id:`n${i}`,parent_id:i?"n0":null,depth:i?2:1,child_ids:i?[]:Array.from({length:count-1},(_,j)=>`n${j+1}`)}))};
    const samples=[];
    for(let i=0;i<5;i++) {
      const start=performance.now();
      const {container}=render(<ExecutionPlanTree report={report} selected={null} onSelect={()=>{}} />);
      samples.push(performance.now()-start);
      expect(container.querySelectorAll('button[aria-pressed]').length).toBe(count);
      cleanup();
    }
    results.push({nodes:count,median_ms:Number(samples.sort((a,b)=>a-b)[2].toFixed(3))});
  }
  const evidence = JSON.stringify({environment:"Vitest jsdom; not browser paint, FPS or production latency",iterations:5,results});
  if (process.env.DERA_PLAN_BENCHMARK_OUTPUT) writeFileSync(process.env.DERA_PLAN_BENCHMARK_OUTPUT, evidence + "\n");
},30000);
