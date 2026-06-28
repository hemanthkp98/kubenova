/**
 * @file Unit tests for the ResourceBadge component.
 */

import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ResourceBadge } from "@/components/resources/ResourceBadge";

describe("ResourceBadge", () => {
  it("renders the status text", () => {
    render(<ResourceBadge status="Running" />);
    expect(screen.getByText("Running")).toBeInTheDocument();
  });

  it("applies green color for Running status", () => {
    const { container } = render(<ResourceBadge status="Running" />);
    const badge = container.querySelector("[data-testid='resource-badge']");
    expect(badge?.className).toContain("kn-success");
  });

  it("applies red color for Failed status", () => {
    const { container } = render(<ResourceBadge status="Failed" />);
    const badge = container.querySelector("[data-testid='resource-badge']");
    expect(badge?.className).toContain("kn-danger");
  });

  it("applies yellow color for Pending status", () => {
    const { container } = render(<ResourceBadge status="Pending" />);
    const badge = container.querySelector("[data-testid='resource-badge']");
    expect(badge?.className).toContain("kn-warning");
  });

  it("applies red color for CrashLoopBackOff", () => {
    const { container } = render(<ResourceBadge status="CrashLoopBackOff" />);
    const badge = container.querySelector("[data-testid='resource-badge']");
    expect(badge?.className).toContain("kn-danger");
  });

  it("applies muted style for unknown statuses", () => {
    const { container } = render(<ResourceBadge status="WeirdUnknownState" />);
    const badge = container.querySelector("[data-testid='resource-badge']");
    expect(badge?.className).toContain("kn-text-muted");
  });
});
