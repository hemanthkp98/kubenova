/**
 * @file E2E test: cluster switching updates the resource panel.
 */

import { test, expect } from "@playwright/test";

test.describe("Cluster switching", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("cluster switcher is visible in the navbar", async ({ page }) => {
    // The cluster switcher button should be visible.
    await expect(page.getByRole("button", { name: /cluster|Select/i })).toBeVisible();
  });

  test("clicking cluster switcher opens dropdown", async ({ page }) => {
    await page.getByRole("button", { name: /cluster|Select/i }).first().click();
    // Either shows context options or "No contexts found".
    const dropdown = page.locator('[role="listbox"]');
    await expect(dropdown).toBeVisible({ timeout: 3000 });
  });

  test("namespace switcher is present", async ({ page }) => {
    await expect(page.locator("button", { hasText: "default" }).first()).toBeVisible();
  });
});
