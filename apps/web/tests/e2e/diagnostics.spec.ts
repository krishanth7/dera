import { test, expect } from "@playwright/test";

test.describe("Phase 8.6 Diagnostics Dashboard E2E", () => {
  test("navigates to diagnostics and displays overview metrics", async ({ page }) => {
    await page.goto("/app/diagnostics");
    await expect(page.locator("h1")).toContainText("Schema Diagnostics & Intelligence");
    await expect(page.getByText("Phase 8.6")).toBeVisible();
    await expect(page.getByText("Total Findings")).toBeVisible();
    await expect(page.getByText("Severity Distribution")).toBeVisible();
    await expect(page.getByText("Diagnostic Rule Coverage")).toBeVisible();
  });

  test("filters findings by search query and opens detail panel", async ({ page }) => {
    await page.goto("/app/diagnostics");
    const searchInput = page.getByPlaceholder(/Search findings/i);
    await searchInput.fill("Primary Key");
    await expect(page.getByText("Primary Key Contains Nullable Column")).toBeVisible();

    // Click row to open detail panel
    await page.getByText("Primary Key Contains Nullable Column").click();
    await expect(page.getByText("Severity Rationale")).toBeVisible();
    await expect(page.getByText("Primary Key Integrity Remediation")).toBeVisible();
  });
});
