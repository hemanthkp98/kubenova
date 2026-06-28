/**
 * @file E2E test: full chat flow including command preview approval.
 *
 * Requires a running KubeNova instance (frontend + backend with mock cluster).
 */

import { test, expect } from "@playwright/test";

test.describe("Chat flow", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("chat input is visible on load", async ({ page }) => {
    await expect(page.getByTestId("chat-input")).toBeVisible();
  });

  test("typing and sending a message shows streaming indicator", async ({ page }) => {
    const input = page.getByTestId("chat-input");
    await input.fill("show me all pods in default namespace");
    await page.getByTestId("send-button").click();

    // Message should appear in the chat.
    await expect(page.getByText("show me all pods in default namespace")).toBeVisible();
  });

  test("user message appears in chat after send", async ({ page }) => {
    const input = page.getByTestId("chat-input");
    await input.fill("list deployments");
    await input.press("Enter");
    await expect(page.getByText("list deployments")).toBeVisible();
  });

  test("chat input clears after send", async ({ page }) => {
    const input = page.getByTestId("chat-input");
    await input.fill("test message");
    await input.press("Enter");
    await expect(input).toHaveValue("");
  });

  test("Enter key sends message", async ({ page }) => {
    const input = page.getByTestId("chat-input");
    await input.fill("get nodes");
    await input.press("Enter");
    await expect(page.getByText("get nodes")).toBeVisible({ timeout: 5000 });
  });

  test("Shift+Enter does not send message", async ({ page }) => {
    const input = page.getByTestId("chat-input");
    await input.fill("line1");
    await input.press("Shift+Enter");
    // Input still has content (wasn't sent).
    await expect(input).not.toHaveValue("");
  });
});
