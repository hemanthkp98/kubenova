/**
 * @file Unit tests for the CommandPreview component.
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { CommandPreview } from "@/components/chat/CommandPreview";
import type { CommandPreview as CommandPreviewType } from "@/types/chat";

const mockPreview: CommandPreviewType = {
  kubectl_command: "kubectl rollout restart deployment/web -n default",
  manifest_yaml: null,
  diff: "+ Deployment/web restarted",
  warnings: ["This will cause a rolling restart."],
  resource_name: "web",
  resource_kind: "Deployment",
  risk_level: "HIGH",
  is_safe: true,
};

describe("CommandPreview", () => {
  it("renders the kubectl command", () => {
    render(
      <CommandPreview
        preview={mockPreview}
        auditEventId="test-audit-id"
        onApprove={vi.fn()}
        onCancel={vi.fn()}
      />
    );
    expect(screen.getByText(/kubectl rollout restart/)).toBeInTheDocument();
  });

  it("shows the risk badge", () => {
    render(
      <CommandPreview
        preview={mockPreview}
        auditEventId="test-audit-id"
        onApprove={vi.fn()}
        onCancel={vi.fn()}
      />
    );
    expect(screen.getByText(/HIGH RISK/i)).toBeInTheDocument();
  });

  it("calls onApprove when Approve button is clicked", async () => {
    const user = userEvent.setup();
    const onApprove = vi.fn();
    render(
      <CommandPreview
        preview={mockPreview}
        auditEventId="test-audit-id"
        onApprove={onApprove}
        onCancel={vi.fn()}
      />
    );
    await user.click(screen.getByTestId("approve-button"));
    expect(onApprove).toHaveBeenCalledWith("test-audit-id");
  });

  it("calls onCancel when Cancel button is clicked", async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    render(
      <CommandPreview
        preview={mockPreview}
        auditEventId="test-audit-id"
        onApprove={vi.fn()}
        onCancel={onCancel}
      />
    );
    await user.click(screen.getByTestId("cancel-button"));
    expect(onCancel).toHaveBeenCalledWith("test-audit-id");
  });

  it("disables approve button for CRITICAL risk", () => {
    render(
      <CommandPreview
        preview={{ ...mockPreview, risk_level: "CRITICAL" }}
        auditEventId="test-audit-id"
        onApprove={vi.fn()}
        onCancel={vi.fn()}
      />
    );
    expect(screen.getByTestId("approve-button")).toBeDisabled();
  });

  it("shows warnings when present", () => {
    render(
      <CommandPreview
        preview={mockPreview}
        auditEventId="test-audit-id"
        onApprove={vi.fn()}
        onCancel={vi.fn()}
      />
    );
    expect(screen.getByText("This will cause a rolling restart.")).toBeInTheDocument();
  });
});
