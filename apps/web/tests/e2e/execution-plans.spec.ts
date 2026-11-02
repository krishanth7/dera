import { test, expect } from "@playwright/test";
import fixture from "../fixtures/execution-plan.json";
import type { PlanReport } from "../../src/components/execution-plans/types";
const report = fixture as PlanReport;

// UI contract fixtures only. Backend auth is verified separately with real sessions.
test.beforeEach(async ({ page }) => {
  await page.route("**/api/v1/**", async route => {
    const url=route.request().url();
    const body=url.includes("execution-plans/analyze") ? report : url.includes("workspaces") ? [] : {id:"test-user",email:"test@example.com",status:"active"};
    await route.fulfill({json:body,headers:{"Access-Control-Allow-Origin":"http://localhost:3000","Access-Control-Allow-Credentials":"true","Access-Control-Allow-Methods":"GET, POST, OPTIONS","Access-Control-Allow-Headers":"content-type, x-csrf-token"}});
  });
});

test("imports a plan, selects nodes, collapses and zooms with keyboard controls", async ({ page }) => {
  await page.goto("/app/execution-plans");
  await page.getByLabel("Execution plan JSON",{exact:true}).fill('{"Plan":{"Node Type":"Result"}}');
  await page.getByRole("button",{name:"Analyze imported plan"}).click();
  await expect(page.getByLabel("Plan summary",{exact:true})).toBeVisible();
  await page.getByRole("button",{name:/n0001 · SCAN/}).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByLabel("Node details",{exact:true})).toContainText("orders");
  await page.getByRole("button",{name:"Zoom in",exact:true}).click();
  await expect(page.getByLabel("Zoom level")).toContainText("120%");
  await page.getByRole("button",{name:"Toggle n0000 subtree"}).click();
  await expect(page.getByRole("button",{name:/n0001 · SCAN/})).toHaveCount(0);
  await expect(page.getByRole("table")).toContainText("n0001");
});

test("contains graph/table overflow at a mobile viewport", async ({ page }) => {
  await page.setViewportSize({width:390,height:844});
  await page.goto("/app/execution-plans");
  await expect(page.getByRole("heading",{name:"Execution plan explorer"})).toBeVisible();
  await page.getByLabel("Execution plan JSON",{exact:true}).fill("{}");
  await page.getByRole("button",{name:"Analyze imported plan"}).click();
  await expect(page.getByRole("table")).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
});

test("records synthetic response-to-painted-plan latency for bounded graph sizes", async ({ page }) => {
  let current: PlanReport = report;
  await page.route("**/sql-engineering/execution-plans/analyze**", async route=>{
    await route.fulfill({json:current,headers:{"Access-Control-Allow-Origin":"http://localhost:3000","Access-Control-Allow-Credentials":"true","Access-Control-Allow-Methods":"GET, POST, OPTIONS","Access-Control-Allow-Headers":"content-type, x-csrf-token"}});
  });
  await page.goto("/app/execution-plans");
  await page.getByLabel("Execution plan JSON",{exact:true}).fill("{}");
  const results=[];
  for(const [label,count,deep] of [["10_nodes",10,false],["100_nodes",100,false],["1000_nodes",1000,false],["deep_25",25,true]] as const) {
    const samples=[];
    for(let sample=0;sample<5;sample++) {
      const nodes=Array.from({length:count},(_,i)=>({...report.nodes[i?1:0],node_id:`n${i}`,parent_id:i?(deep?`n${i-1}`:"n0"):null,depth:deep?i+1:i?2:1,child_ids:deep?(i<count-1?[`n${i+1}`]:[]):i?[]:Array.from({length:count-1},(_,j)=>`n${j+1}`)}));
      current={...report,nodes,root_ids:["n0"],diagnostics:[],recommendations:[],summary:{...report.summary,node_count:count,max_depth:deep?count:2},plan_fingerprint:`perf-${label}-${sample}`};
      const start=await page.evaluate(()=>performance.now());
      await page.getByRole("button",{name:"Analyze imported plan"}).click();
      await expect(page.getByLabel("Plan summary",{exact:true})).toContainText(current.plan_fingerprint);
      await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));
      const end=await page.evaluate(()=>performance.now());
      samples.push(end-start);
      await expect(page.locator('button[aria-pressed]')).toHaveCount(count);
    }
    results.push({fixture:label,nodes:count,median_ms:Number(samples.sort((a,b)=>a-b)[2].toFixed(3))});
  }
  console.log("DERA_PLAN_BROWSER_BENCHMARK",JSON.stringify({iterations:5,method:"Synthetic API fixture, click-to-report plus two animation frames; includes test driver and mocked transport overhead, not isolated React CPU time or FPS",results}));
});
