/**
 * @file Unit tests for the PodList component.
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PodList } from "@/components/resources/PodList";
import type { PodInfo } from "@/types/resource";

// Mock the hooks used by PodList.
vi.mock("@/hooks/useResources", () => ({
  usePods: () => ({
    data: mockPods,
    isLoading: false,
    error: null,
  }),
}));

vi.mock("@/store/clusterStore", () => ({
  useClusterStore: () => ({ activeCluster: "minikube" }),
}));

// Stub out LogViewer to avoid WebSocket complexity in tests.
vi.mock("@/components/logs/LogViewer", () => ({
  LogViewer: ({ pod, onClose }: { pod: string; onClose: () => void }) => (
    <div data-testid="log-viewer" data-pod={pod}>
      <button onClick={onClose}>Close</button>
    </div>
  ),
}));

const mockPods: PodInfo[] = [
  {
    name: "nginx-abc",
    namespace: "default",
    status: "Running",
    ready: "1/1",
    restarts: 0,
    age: "1h",
    node: "node-1",
    labels: {},
    containers: [{ name: "nginx", image: "nginx:latest", ready: true, restart_count: 0, state: "Running", state_reason: null }],
    created_at: null,
  },
  {
    name: "crashing-pod",
    namespace: "default",
    status: "CrashLoopBackOff",
    ready: "0/1",
    restarts: 5,
    age: "10m",
    node: null,
    labels: {},
    containers: [{ name: "app", image: "app:latest", ready: false, restart_count: 5, state: "Waiting", state_reason: "CrashLoopBackOff" }],
    created_at: null,
  },
];

function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>;
}

describe("PodList", () => {
  it("renders pod rows", () => {
    render(<PodList />, { wrapper });
    expect(screen.getByText("nginx-abc")).toBeInTheDocument();
    expect(screen.getByText("crashing-pod")).toBeInTheDocument();
  });

  it("opens log viewer when a pod row is clicked", async () => {
    const user = userEvent.setup();
    render(<PodList />, { wrapper });
    const rows = screen.getAllByTestId("pod-row");
    await user.click(rows[0]);
    expect(screen.getByTestId("log-viewer")).toBeInTheDocument();
  });

  it("closes log viewer when close is clicked", async () => {
    const user = userEvent.setup();
    render(<PodList />, { wrapper });
    await user.click(screen.getAllByTestId("pod-row")[0]);
    await user.click(screen.getByText("Close"));
    expect(screen.queryByTestId("log-viewer")).not.toBeInTheDocument();
  });

  it("shows restart count in the table", () => {
    render(<PodList />, { wrapper });
    expect(screen.getByText("5")).toBeInTheDocument();
  });
});
