/**
 * @file Unit tests for the AmbientAlerts component.
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AmbientAlerts } from "@/components/resources/AmbientAlerts";
import type { PodInfo } from "@/types/resource";

let mockPodsData: PodInfo[] = [];

vi.mock("@/hooks/useResources", () => ({
  usePods: () => ({ data: mockPodsData }),
  useNodes: () => ({ data: [] }),
}));

function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>;
}

describe("AmbientAlerts", () => {
  it("renders nothing when no issues", () => {
    mockPodsData = [];
    const { container } = render(<AmbientAlerts />, { wrapper });
    expect(container.firstChild).toBeNull();
  });

  it("shows CrashLoopBackOff alert when pod is crashing", () => {
    mockPodsData = [
      {
        name: "bad-pod",
        namespace: "default",
        status: "CrashLoopBackOff",
        ready: "0/1",
        restarts: 10,
        age: "5m",
        node: null,
        labels: {},
        containers: [{ name: "app", image: "x", ready: false, restart_count: 10, state: "Waiting", state_reason: "CrashLoopBackOff" }],
        created_at: null,
      },
    ];
    render(<AmbientAlerts />, { wrapper });
    expect(screen.getByText(/CrashLoopBackOff/)).toBeInTheDocument();
  });

  it("shows pending alert for pending pods", () => {
    mockPodsData = [
      {
        name: "pending-pod",
        namespace: "default",
        status: "Pending",
        ready: "0/1",
        restarts: 0,
        age: "10m",
        node: null,
        labels: {},
        containers: [],
        created_at: null,
      },
    ];
    render(<AmbientAlerts />, { wrapper });
    expect(screen.getByText(/pending/i)).toBeInTheDocument();
  });

  it("calls onAskAI with appropriate message when Ask AI is clicked", async () => {
    const user = userEvent.setup();
    const onAskAI = vi.fn();
    mockPodsData = [
      {
        name: "crash-pod",
        namespace: "default",
        status: "CrashLoopBackOff",
        ready: "0/1",
        restarts: 3,
        age: "2m",
        node: null,
        labels: {},
        containers: [{ name: "app", image: "x", ready: false, restart_count: 3, state: "Waiting", state_reason: "CrashLoopBackOff" }],
        created_at: null,
      },
    ];
    render(<AmbientAlerts onAskAI={onAskAI} />, { wrapper });
    await user.click(screen.getByText("Ask AI"));
    expect(onAskAI).toHaveBeenCalledWith(expect.stringContaining("CrashLoopBackOff"));
  });

  it("dismisses an alert when X is clicked", async () => {
    const user = userEvent.setup();
    mockPodsData = [
      {
        name: "crash-pod",
        namespace: "default",
        status: "CrashLoopBackOff",
        ready: "0/1",
        restarts: 3,
        age: "2m",
        node: null,
        labels: {},
        containers: [{ name: "app", image: "x", ready: false, restart_count: 3, state: "Waiting", state_reason: "CrashLoopBackOff" }],
        created_at: null,
      },
    ];
    render(<AmbientAlerts />, { wrapper });
    expect(screen.getByText(/CrashLoopBackOff/)).toBeInTheDocument();
    await user.click(screen.getByLabelText("Dismiss alert"));
    expect(screen.queryByText(/CrashLoopBackOff/)).not.toBeInTheDocument();
  });
});
