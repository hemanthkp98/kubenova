# Multi-Cluster Support

KubeNova reads all contexts from the kubeconfig file and lets users switch between them from the UI. Each context points to a different cluster (EKS, GKE, on-prem, Minikube, etc.).

---

## How it works

1. On startup, `ClusterManager.list_contexts()` reads `~/.kube/config` (or `KUBECONFIG_PATH`) and enumerates all contexts.
2. The active context defaults to the `current-context` field in kubeconfig, or `DEFAULT_CLUSTER_CONTEXT` if set.
3. When the user selects a context in the UI (GET `/api/clusters/switch`), `ClusterManager.switch_context()` sets the new active context and clears the client cache.
4. All subsequent API calls use the new context.

---

## Kubeconfig setup

Mount your kubeconfig into the Docker container read-only:

```yaml
# docker-compose.yml
volumes:
  - ~/.kube:/root/.kube:ro
```

For the Helm chart, KubeNova uses the pod's service account credentials when running inside the cluster. To add remote clusters, create a kubeconfig Secret and mount it.

---

## RBAC requirements

For each cluster KubeNova connects to, the service account (or kubeconfig user) needs these permissions:

**Read-only (always required)**:
```yaml
rules:
  - apiGroups: [""]
    resources: [pods, services, nodes, namespaces, events]
    verbs: [get, list, watch]
  - apiGroups: [""]
    resources: [pods/log]
    verbs: [get]
  - apiGroups: ["apps"]
    resources: [deployments, statefulsets, daemonsets]
    verbs: [get, list, watch]
```

**Write (for apply/delete operations — HIGH risk, requires user approval)**:
```yaml
  - apiGroups: ["*"]
    resources: ["*"]
    verbs: [create, update, patch, delete]
```

You can restrict write permissions to specific namespaces by creating RoleBindings instead of ClusterRoleBindings.

---

## Context switching behaviour

- Switching context resets the active **namespace** to "default".
- The Kubernetes client cache is cleared on switch to prevent cross-cluster credential leakage.
- In-progress WebSocket chat sessions continue with the context that was active when the session started — they are not retroactively affected by a context switch.
