import { test, expect } from "@playwright/test";
import report from "../fixtures/execution-plan.json";

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
