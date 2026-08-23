# Deployment

Deploy KubeNova as a shared, always-on service inside your Kubernetes cluster so your entire team gets a single URL to chat with the cluster.

> **Not what you need?** If you just want to run KubeNova on your own machine and point it at a cluster, use the [Docker Compose Quickstart](getting-started.md) instead — it's two commands and takes under a minute.

---

## How it works

```
Your Team
   │
   ├─ Alice  ──────────────────────────────┐
   ├─ Bob    ──────────────────────────────┤
   └─ Carol  ──────────────────────────────┤
                                           ▼
                            KubeNova (running inside the cluster)
                            ┌───────────────────────────────┐
                            │  Frontend (nginx)   :80       │ ← LoadBalancer / NodePort
                            │  Backend  (FastAPI) :8000     │ ← ClusterIP (internal only)
                            │  ServiceAccount               │ ← in-cluster auth, no kubeconfig needed
                            └───────────────────────────────┘
                                           │
                                           ▼
                                    Kubernetes API Server
```

KubeNova uses the pod's **ServiceAccount token** to authenticate with the cluster API — no kubeconfig files to mount or rotate.

---

## Prerequisites

| Tool | Purpose | Install |
|---|---|---|
| `docker` | Build the images | [docs.docker.com](https://docs.docker.com/get-docker/) |
| `kubectl` | Apply manifests | [kubernetes.io/docs/tasks/tools](https://kubernetes.io/docs/tasks/tools/) |
| Cluster access | A kubeconfig pointing at the target cluster | Cloud provider docs |
| LLM API key | Unless using self-hosted Ollama | See [LLM section](#llm-provider) below |

---

## Step 1 — Configure

Open [`kubenova.conf`](../kubenova.conf) (in the repo root) and fill in the sections that apply to you. Every option has an inline comment explaining it.

The three things you **must** set:

```bash
# Where is your cluster?
KUBECONFIG_PATH="$HOME/.kube/config"

# Where should images be pushed? (leave empty for local clusters: kind/k3d/minikube)
REGISTRY="ghcr.io/your-org"

# Which LLM? (see options below)
LLM_PROVIDER="anthropic"
LLM_API_KEY="sk-ant-..."
LLM_MODEL="claude-3-5-haiku-20241022"
```

Everything else — namespace, replicas, expose type, database URL — has a sensible default and can be left unchanged for a first deploy.

---

## Step 2 — Deploy

```bash
./deploy.sh
```

That's it. The script:

1. Validates your config and tests cluster connectivity
2. Builds the backend and frontend Docker images locally
3. Pushes them to your registry (or loads them into a local cluster)
4. Creates the `kubenova` namespace and all Kubernetes resources
5. Waits for pods to become ready
6. Prints the URL where your team can access KubeNova

**Expected output:**

```
╔══════════════════════════════════════════╗
║      KubeNova Kubernetes Deployer        ║
╚══════════════════════════════════════════╝

[1/8] Loading configuration
✓ Config loaded from kubenova.conf
   Namespace   : kubenova
   LLM Provider: anthropic / claude-3-5-haiku-20241022
   Expose Type : LoadBalancer

[2/8] Checking prerequisites
✓ docker and kubectl are available

...

╔══════════════════════════════════════════╗
║     KubeNova deployed successfully! 🚀  ║
╚══════════════════════════════════════════╝

  Access URL:   http://34.12.45.67
  Namespace:    kubenova
  API Docs:     http://34.12.45.67/api/docs
```

Share the URL with your team. No installs on their side.

---

## LLM Provider

Pick one. Edit the corresponding block in `kubenova.conf`.

### Anthropic Claude *(recommended for teams)*

Best reasoning quality. Cost is per-request — very low for typical cluster queries (~$0.001–0.01 per conversation turn with Haiku).

```bash
LLM_PROVIDER="anthropic"
LLM_MODEL="claude-3-5-haiku-20241022"   # fast and cheap
# LLM_MODEL="claude-sonnet-4-6"         # better quality, higher cost
LLM_API_KEY="sk-ant-..."
LLM_BASE_URL=""
```

Get a key at [console.anthropic.com](https://console.anthropic.com).

### Google Gemini

Good balance of quality and cost. Uses the OpenAI-compatible endpoint.

```bash
LLM_PROVIDER="openai"
LLM_MODEL="gemini-2.0-flash"
LLM_API_KEY="<google-ai-studio-key>"
LLM_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
```

Get a key at [aistudio.google.com](https://aistudio.google.com).

### OpenAI

```bash
LLM_PROVIDER="openai"
LLM_MODEL="gpt-4o-mini"
LLM_API_KEY="sk-..."
LLM_BASE_URL=""
```

### Self-hosted Ollama *(free, no API key)*

Run Ollama separately in your cluster and point KubeNova at it. Suitable for air-gapped environments.

```bash
LLM_PROVIDER="ollama"
LLM_MODEL="llama3.2"
LLM_API_KEY=""
LLM_BASE_URL="http://ollama.ollama.svc.cluster.local:11434"
```

See [Configuration](configuration.md) for full Ollama cluster setup instructions.

---

## Kubernetes Resources Created

The deploy script creates exactly these resources. Nothing hidden.

| Resource | Kind | Notes |
|---|---|---|
| `kubenova` | Namespace | All other resources live here |
| `kubenova` | ServiceAccount | The identity the backend pod runs as |
| `kubenova` | ClusterRole | Read + approved-write permissions (see below) |
| `kubenova` | ClusterRoleBinding | Binds the SA to the ClusterRole |
| `kubenova-config` | ConfigMap | App config from `kubenova.conf` |
| `kubenova-secret` | Secret | Holds `LLM_API_KEY` (base64) |
| `kubenova-backend` | Deployment | FastAPI + LangGraph agent |
| `backend` | Service | ClusterIP — internal only, used by nginx proxy |
| `kubenova-frontend` | Deployment | nginx serving the React SPA |
| `kubenova` | Service | LoadBalancer or NodePort — **external access** |

---

## Cluster Permissions

KubeNova's ClusterRole gives it two tiers of access:

### Read (always active)

Used for the live resource panel and answering questions.

```
pods, pods/log, services, nodes, namespaces, events, configmaps,
deployments, statefulsets, daemonsets, replicasets,
jobs, cronjobs, ingresses, storageclasses, roles, rolebindings ...
```
Verbs: `get`, `list`, `watch`

### Write (safety-gated)

Used when KubeNova generates and applies manifests. **Every write operation requires explicit user approval in the UI** before it executes — the agent pauses and waits for an "Approve" click. CRITICAL-risk operations (namespace delete, `--all` deletes, node drain) are blocked entirely, regardless of user input.

```
All apiGroups, all resources
```
Verbs: `create`, `update`, `patch`, `delete`

> If your security policy requires narrower write scope, edit the ClusterRole section in `deploy.sh` to use namespace-scoped RoleBindings instead of a cluster-wide ClusterRoleBinding.

---

## Securing Access

> [!WARNING]
> KubeNova ships with **no authentication layer**. The URL printed by `deploy.sh` is publicly accessible if your LoadBalancer has a public IP. Do not expose it to the public internet without adding authentication.

### Option A — VPN / private network *(simplest)*

Deploy KubeNova with a private LoadBalancer annotation (cloud-specific):

```bash
# AWS (internal NLB)
kubectl annotate svc kubenova -n kubenova \
  service.beta.kubernetes.io/aws-load-balancer-internal="true"

# GCP (internal)
kubectl annotate svc kubenova -n kubenova \
  cloud.google.com/load-balancer-type="Internal"
```

Team members access it over VPN only. No auth code required.

### Option B — nginx basic auth *(quick)*

```bash
# Create htpasswd file
htpasswd -c auth team-user

# Create secret
kubectl create secret generic kubenova-basic-auth \
  --from-file=auth \
  -n kubenova

# Patch the frontend service to ClusterIP and create an Ingress
# with nginx.ingress.kubernetes.io/auth-type: basic annotations
```

### Option C — OAuth2 proxy *(production-grade)*

Deploy [oauth2-proxy](https://oauth2-proxy.github.io/oauth2-proxy/) in front of the frontend service, backed by your organisation's SSO provider (Google, GitHub, Okta, Azure AD). This is the recommended approach for production teams.

---

## External Access Options

Set `EXPOSE_TYPE` in `kubenova.conf`:

| Value | When to use | How to get the URL |
|---|---|---|
| `LoadBalancer` | Cloud clusters (EKS, GKE, AKS) | Script waits and prints the external IP |
| `NodePort` | Local/bare-metal clusters, kind, k3d | `http://<any-node-ip>:<NODEPORT>` |

For **NodePort**, also set `NODEPORT` (default `30080`, must be 30000–32767).

---

## Persistent Audit Log

By default KubeNova uses an ephemeral SQLite database — the audit log is lost when the backend pod restarts.

For a persistent audit log, switch to PostgreSQL:

```bash
# In kubenova.conf:
DATABASE_URL="postgresql+asyncpg://kubenova:password@postgres.db.svc.cluster.local:5432/kubenova"
```

The backend creates the schema on startup automatically.

---

## Updating KubeNova

To deploy a new version:

```bash
# 1. Pull the latest code
git pull

# 2. Re-run deploy — it rebuilds images and rolls out new pods
./deploy.sh
```

The script is idempotent — safe to run multiple times. `kubectl apply` will only update resources that have changed.

---

## Scaling

Edit `kubenova.conf` and re-run `./deploy.sh`:

```bash
BACKEND_REPLICAS=2    # each replica handles independent chat sessions
FRONTEND_REPLICAS=2   # stateless — scales freely behind the LoadBalancer
```

The backend is session-stateless per LangGraph invocation. Multiple replicas work without shared state.

---

## Dry Run

To preview the full manifest without applying anything:

```bash
./deploy.sh --dry-run
```

Useful for auditing what will be deployed before doing it for real.

---

## Teardown

To remove KubeNova from the cluster completely:

```bash
./teardown.sh
```

This deletes the `kubenova` namespace and the cluster-scoped RBAC resources. It prompts for confirmation before deleting anything.

---

## Troubleshooting

### Pods stuck in `Pending`
```bash
kubectl describe pod -n kubenova -l app=kubenova-backend
```
Common causes: insufficient cluster resources, image pull error (check `REGISTRY`/image name), node selector mismatch.

### `ImagePullBackOff`
- Remote cluster: confirm `docker push` succeeded and the registry is accessible from the cluster.
- Local cluster (kind/k3d): re-run `./deploy.sh` — it reloads images on every run.

### `502 Bad Gateway` on `/api/*`
The frontend nginx can't reach the backend. Check:
```bash
kubectl get svc backend -n kubenova
kubectl logs -n kubenova -l app=kubenova-backend --tail=50
```

### Backend starts but LLM calls fail
Check the API key is set correctly:
```bash
kubectl get secret kubenova-secret -n kubenova -o jsonpath='{.data.LLM_API_KEY}' | base64 -d
```
If empty, update `LLM_API_KEY` in `kubenova.conf` and re-run `./deploy.sh`.

### `Cannot connect to cluster`
Verify `KUBECONFIG_PATH` exists and the context in `KUBE_CONTEXT` is valid:
```bash
kubectl --kubeconfig=<your-path> cluster-info
```
