/**
 * @file Unit tests for the useCluster hook and clusterStore.
 */

import { describe, it, expect, beforeEach } from "vitest";
import { useClusterStore } from "@/store/clusterStore";

describe("clusterStore", () => {
  beforeEach(() => {
    useClusterStore.setState({
      activeCluster: "",
      activeNamespace: "default",
      availableContexts: [],
    });
  });

  it("defaults to empty cluster and default namespace", () => {
    const state = useClusterStore.getState();
    expect(state.activeCluster).toBe("");
    expect(state.activeNamespace).toBe("default");
  });

  it("sets active cluster", () => {
    useClusterStore.getState().setActiveCluster("production");
    expect(useClusterStore.getState().activeCluster).toBe("production");
  });

  it("resets namespace to default when cluster changes", () => {
    useClusterStore.setState({ activeNamespace: "kube-system" });
    useClusterStore.getState().setActiveCluster("new-cluster");
    expect(useClusterStore.getState().activeNamespace).toBe("default");
  });

  it("sets active namespace independently", () => {
    useClusterStore.getState().setActiveNamespace("staging");
    expect(useClusterStore.getState().activeNamespace).toBe("staging");
  });

  it("sets available contexts and auto-selects active", () => {
    useClusterStore.getState().setAvailableContexts([
      { name: "minikube", cluster: "minikube", user: "minikube", namespace: "default", is_active: true },
      { name: "prod", cluster: "prod", user: "admin", namespace: "production", is_active: false },
    ]);
    const state = useClusterStore.getState();
    expect(state.availableContexts).toHaveLength(2);
    // Auto-selects active context when none was set.
    expect(state.activeCluster).toBe("minikube");
  });

  it("does not override existing cluster when setting contexts", () => {
    useClusterStore.setState({ activeCluster: "my-cluster" });
    useClusterStore.getState().setAvailableContexts([
      { name: "minikube", cluster: "minikube", user: "minikube", namespace: "default", is_active: true },
    ]);
    expect(useClusterStore.getState().activeCluster).toBe("my-cluster");
  });
});
