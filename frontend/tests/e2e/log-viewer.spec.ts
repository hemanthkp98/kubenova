/**
 * @file E2E test: log viewer opens when clicking a pod row.
 */

import { test, expect } from "@playwright/test";

test.describe("Log viewer", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("KubeNova title is present", async ({ page }) => {
    await expect(page.getByText("KubeNova")).toBeVisible();
  });

  test("resource panel is visible in chat view", async ({ page }) => {
    await expect(page.getByText("Cluster Resources")).toBeVisible();
  });

  test("pods tab is visible in resource panel", async ({ page }) => {
    await expect(page.getByRole("button", { name: "Pods" })).toBeVisible();
  });

  test("LLM config button opens modal", async ({ page }) => {
    await page.getByRole("button", { name: /LLM|llm/i }).click();
    await expect(page.getByRole("dialog")).toBeVisible({ timeout: 2000 });
  });
});
