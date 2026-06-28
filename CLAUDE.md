# KubeNova — Claude Context

## What This Is

KubeNova is a Kubernetes AI assistant: talk to a cluster in plain English, see resources live, diagnose failures, and approve/reject generated kubectl commands before they run. Built for developers who want LLM-powered cluster ops without losing control.

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, Python 3.11, LangChain 0.2, LangGraph 0.1, kubernetes-python 30.1 |
| LLM | Ollama (default, runs in Docker) / Anthropic / Gemini — swapped via `LLM_PROVIDER` env var |
| Database | SQLite via SQLModel + aiosqlite (async) |
| Frontend | React 18, TypeScript, Vite 5, TanStack Query, Zustand, Tailwind, Radix UI, Monaco editor |
| Runtime | Docker Compose — single `docker compose up` starts everything |

## Directory Layout

```
kubenova/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app factory, CORS, router registration
│   │   ├── config.py            # Pydantic Settings — all env vars documented here
│   │   ├── api/
│   │   │   ├── deps.py          # FastAPI dependency injectors (db, audit, cluster manager)
│   │   │   └── routes/
│   │   │       ├── chat.py      # POST /api/chat, WS /api/ws/chat, POST /api/chat/approve
│   │   │       ├── clusters.py  # GET /api/clusters, GET /api/clusters/{name}/status, POST /api/clusters/switch
│   │   │       ├── resources.py # GET /api/resources/{pods,deployments,services,nodes,namespaces,events}
│   │   │       ├── logs.py      # WebSocket log streaming
│   │   │       └── audit.py     # GET /api/audit, GET /api/audit/export
│   │   ├── core/
│   │   │   ├── agents/
│   │   │   │   ├── graph.py     # LangGraph StateGraph wiring + conditional routing
│   │   │   │   ├── nodes.py     # Node functions: intent_classifier, safety_gate, executor, responder…
│   │   │   │   ├── state.py     # KubeNovaState TypedDict (shared graph state)
│   │   │   │   └── tools.py     # @tool definitions the LLM can call (list_pods, describe_pod, etc.)
│   │   │   ├── k8s/
│   │   │   │   ├── client.py    # k8s client factory — cached per context, loads kubeconfig
│   │   │   │   ├── multi_cluster.py  # ClusterManager — lists contexts, switches context, probes status
│   │   │   │   ├── resources.py # ResourceFetcher — thin wrappers around k8s API
│   │   │   │   └── executor.py  # kubectl command generation, dry-run, RiskLevel enum
│   │   │   ├── llm/
│   │   │   │   ├── factory.py   # get_llm() — returns the configured provider's LLM instance
│   │   │   │   ├── anthropic_provider.py
│   │   │   │   ├── openai_provider.py
│   │   │   │   └── ollama_provider.py
│   │   │   └── audit/
│   │   │       ├── logger.py    # AuditLogger — write/update audit events
│   │   │       └── models.py    # AuditEventCreate pydantic model
│   │   ├── db/database.py       # Async SQLAlchemy engine + create_tables()
│   │   └── models/              # SQLModel / Pydantic response models
│   ├── requirements.txt         # Pinned runtime deps
│   ├── requirements-dev.txt     # Extends requirements.txt + pytest, ruff, mypy
│   ├── Dockerfile               # Multi-stage: builder → dev → runtime
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── chat/            # ChatPanel, ChatInput, ChatMessage, CommandPreview, IncidentModePanel
│   │   │   ├── resources/       # Resource list views
│   │   │   ├── logs/            # Log streaming UI
│   │   │   ├── audit/           # Audit log table
│   │   │   ├── yaml/            # Monaco YAML editor
│   │   │   └── layout/          # Shell, sidebar, navbar
│   │   ├── hooks/               # useCluster, useResources, useChatWebSocket, useLogWebSocket, useAudit
│   │   ├── store/               # Zustand: clusterStore, chatStore, llmStore
│   │   └── types/               # TypeScript interfaces mirroring backend Pydantic models
│   ├── Dockerfile               # Multi-stage: builder (npm ci + vite build) → nginx
│   ├── Dockerfile.dev           # Dev: npm ci, then mounts src via volume, vite on port 80
│   ├── nginx.conf               # SPA routing + /api proxy to backend:8000
│   ├── package.json
│   └── package-lock.json        # Required for npm ci in Docker
├── docker-compose.yml           # Production: backend:8000, frontend:5173→80
├── docker-compose.dev.yml       # Dev override: hot-reload, mounts src, vite --port 80
├── Makefile                     # See commands below
└── helm/kubenova/               # Helm chart for k8s deployment
```

## Quick Start (2 steps)

```bash
# Step 1 — configure (copy once, edit if you want a different LLM provider)
cp .env.example .env

# Step 2 — start everything (Ollama model pulls automatically on first run ~2 GB)
./start.sh          # or: docker compose up  or: make start
```

Open http://localhost:5173 once the stack is healthy (~60 s on first run, ~10 s on subsequent runs).

## Common Commands

```bash
make start        # Copy .env if absent, then start (recommended for first run)
make dev          # Start with hot-reload (backend + frontend source mounted)
make build        # Build/rebuild Docker images
make test         # Run all tests (backend pytest + frontend vitest)
make test-backend # pytest inside the running backend container
make test-frontend# vitest inside frontend/
make test-e2e     # Playwright E2E (requires running stack)
make lint         # ruff + mypy + eslint + tsc
make clean        # Stop containers, remove volumes and frontend dist
```

## Environment Variables

All settings live in `kubenova/.env` (root level). Docker Compose auto-loads it.
Defined and documented in `backend/app/config.py`.

| Variable | Default | Notes |
|---|---|---|
| `COMPOSE_PROFILES` | `ollama` | Set to `ollama` to start bundled Ollama; leave empty to use API key provider |
| `LLM_PROVIDER` | `ollama` | `anthropic` / `openai` / `ollama` |
| `LLM_MODEL` | `llama3.2` | Model ID for the chosen provider |
| `LLM_API_KEY` | `""` | Required for Anthropic/OpenAI; not needed for Ollama |
| `LLM_BASE_URL` | `http://ollama:11434` | Container URL for Ollama; or set to `http://host.docker.internal:11434` for native Ollama |
| `KUBECONFIG_DIR` | `~/.kube` | Directory mounted read-only into backend; created if absent |
| `KUBENOVA_ENV` | `development` | Controls log verbosity and CORS strictness |
| `KUBENOVA_DATABASE_URL` | SQLite `./data/kubenova.db` | Swap for `postgresql+asyncpg://` in prod |

After changing `.env`, apply with:
```bash
docker compose up -d --force-recreate backend
```

## LangGraph Agent

The chat feature runs a `StateGraph` with these nodes:

```
HumanMessage
    └─► intent_classifier
    └─► safety_gate ──── CRITICAL ──► blocked (terminal)
                    ├─── incident_mode ──► incident_analyzer ──► executor ──► responder
                    ├─── HIGH ──► human_review ──► (approved?) ──► executor ──► responder
                    └─── LOW/MEDIUM ──────────────────────────────► executor ──► responder
```

- `safety_gate` assigns `RiskLevel` (LOW / MEDIUM / HIGH / CRITICAL) and populates `command_preview`
- `human_review` pauses and waits for `POST /api/chat/approve` before continuing
- `executor` calls LLM tools (list_pods, describe_pod, get_events, exec_command, dry_run_manifest, etc.)
- State is `KubeNovaState` TypedDict in `core/agents/state.py`
- WebSocket endpoint streams node output in chunks; REST endpoint waits for full completion

## Kubernetes Connectivity

- The backend reads `~/.kube/config` (mounted read-only into the container)
- `ClusterManager` (singleton in `deps.py`) lists contexts and tracks the active one
- `get_k8s_clients(context)` caches clients per context name; call `clear_client_cache()` after context switch
- The client falls back to in-cluster config if kubeconfig load fails

### Local dev with k3d

KubeNova mounts `~/.kube` (or `KUBECONFIG_DIR`) into the backend automatically.
For k3d on macOS with Colima the API server address in the kubeconfig must use
`host.docker.internal` (not `127.0.0.1`) so the backend container can reach it:

```bash
k3d cluster create kubenova-dev
# Export a docker-accessible kubeconfig:
k3d kubeconfig get kubenova-dev | \
  sed 's/0.0.0.0/host.docker.internal/g' > ~/.kube/kubenova-dev-docker.yaml
# Point KubeNova at it:
echo "KUBECONFIG_DIR=$(dirname ~/.kube/kubenova-dev-docker.yaml)" >> .env
# Also set DEFAULT_CLUSTER_CONTEXT if needed
```

## LLM Provider Setup

Edit `kubenova/.env` to switch providers. Uncomment the block you want.
See `.env.example` for the full template with all options.

### Ollama in Docker (default — free, no API key)
```
COMPOSE_PROFILES=ollama
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2          # or llama3.1:8b for better quality
LLM_API_KEY=
LLM_BASE_URL=http://ollama:11434
```
Model `llama3.2` (~2 GB, fast) or `llama3.1:8b` (~5 GB, smarter). Downloaded on first start.

### Ollama native (Apple Silicon — better performance, GPU via Metal)
```
COMPOSE_PROFILES=
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
LLM_API_KEY=
LLM_BASE_URL=http://host.docker.internal:11434
```
Start with: `brew install ollama && brew services start ollama && ollama pull llama3.2`

### Anthropic Claude
```
COMPOSE_PROFILES=
LLM_PROVIDER=anthropic
LLM_MODEL=claude-haiku-4-5-20251001   # or claude-sonnet-4-6
LLM_API_KEY=sk-ant-...
LLM_BASE_URL=
```

### Google Gemini (via OpenAI-compatible endpoint)
```
COMPOSE_PROFILES=
LLM_PROVIDER=openai
LLM_MODEL=gemini-2.0-flash
LLM_API_KEY=<google-ai-studio-key>
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```

## Docker Compose Notes

- **Ollama profile**: set `COMPOSE_PROFILES=ollama` in `.env` to start the bundled Ollama container. Leave empty to use an API key provider (Anthropic/Gemini). Docker Compose reads `COMPOSE_PROFILES` automatically from `.env`.
- **Kubeconfig auto-mount**: `~/.kube` (or `KUBECONFIG_DIR`) is bind-mounted read-only into the backend at `/root/.kube`. The directory is created on the host if absent, so the app starts gracefully with no cluster configured.
- **`--force-recreate` vs restart**: env var changes in `.env` are baked at container creation time. `docker compose restart` does NOT pick them up. Use `docker compose up -d --force-recreate backend`.
- **`make dev` runs `down` before `up`** to prevent stale containers holding ports.
- **nginx WebSocket fix**: all `/api/` traffic (REST + WebSocket) goes through one nginx `location /api/` block with `Upgrade` headers. Actual WS paths are `/api/chat/ws/chat` and `/api/logs/ws/…` — not `/api/ws/`.
- **Multi-arch kubectl**: the backend Dockerfile detects the container's CPU architecture (`dpkg --print-architecture`) and downloads the matching `kubectl` binary — works on amd64 and arm64.
- The `version:` field in compose files is obsolete in Compose V2 — removed.

## API Docs

Available at `http://localhost:8000/api/docs` when the dev stack is running.

All resource endpoints require `?cluster_context=<context-name>`. Namespace defaults to `default`; pass `all` for cross-namespace queries.

## Frontend Patterns

- **State**: Zustand stores for cluster selection (`clusterStore`), chat history (`chatStore`), LLM config (`llmStore`)
- **Data fetching**: TanStack Query for REST endpoints; custom hooks (`useChatWebSocket`, `useLogWebSocket`) for WebSocket streams
- **Chat flow**: `useChatWebSocket` → receives `token` / `command_preview` / `done` / `error` message types
- **Approval flow**: `CommandPreview` component renders the modal; approval calls `POST /api/chat/approve`
