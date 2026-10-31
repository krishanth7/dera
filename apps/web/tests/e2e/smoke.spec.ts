import { test, expect } from "@playwright/test";

test.describe("DERA Studio Smoke Tests", () => {
  test("root route redirects to overview or login", async ({ page }) => {
    await page.goto("/");
    // Should navigate to /app/overview
    await expect(page).toHaveURL(/.*\/app\/overview/);
  });

  test("overview displays deterministic policy and navigation links", async ({ page }) => {
    await page.goto("/app/overview");
    await expect(page.locator("h1")).toContainText("Engineering Studio Overview");
    await expect(page.getByText("Zero-AI Compliant")).toBeVisible();
    await expect(page.getByText("Supported Dialects")).toBeVisible();
  });

  test("navigation to settings page works correctly", async ({ page }) => {
    await page.goto("/app/settings");
    await expect(page.locator("h1")).toContainText("Studio Settings");
    await expect(page.getByText("Appearance & Theme")).toBeVisible();
    await expect(page.getByText("Strictly Prohibited")).toHaveCount(3);
  });

  test("connections route displays accurate planned state", async ({ page }) => {
    await page.goto("/app/connections");
    await expect(page.getByText("No Database Connections Configured")).toBeVisible();
  });
});
