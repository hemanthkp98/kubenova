# KubeNova

**Talk to your cluster. See it live. Fix it fast.**

KubeNova is a production-ready, open-source, web-based Kubernetes chat interface that lets you interact with your clusters using natural language. Ask questions, diagnose incidents, and apply changes — all from a browser, with a real-time resource panel and an AI-powered safety gate before anything destructive runs.

---

## What makes KubeNova different

| Feature | KubeNova | kubectl + terminal |
|---|---|---|
| Browser-based UI | ✓ | ✗ |
| Live resource panel (WebSocket) | ✓ | ✗ |
| Command dry-run preview before apply | ✓ | Manual |
| Pluggable LLM backends | ✓ | N/A |
| Multi-cluster context switching | ✓ | Manual flag |
| Log streaming in UI | ✓ | Separate window |
| Structured audit log + CSV export | ✓ | ✗ |
| Incident response mode | ✓ | ✗ |

---

## Quick start

Two steps. No host dependencies beyond Docker.

### Step 1 — clone

```bash
git clone https://github.com/kubenova/kubenova.git
cd kubenova
```

### Step 2 — start

```bash
./start.sh
```

Open [http://localhost:5173](http://localhost:5173) once the stack is healthy.

- **First run**: Ollama downloads the `llama3.2` model (~2 GB). This takes 2–5 minutes depending on your connection.
- **Subsequent runs**: the model is cached in a Docker volume — startup takes ~10 seconds.
- **No cluster?** KubeNova starts fine with no kubeconfig. The cluster panel shows an empty list; connect a cluster whenever you're ready.

> The `start.sh` script auto-creates `.env` from `.env.example` on first run, verifies Docker is running, and warns you if Docker has insufficient memory for Ollama.

---

## For teams

Want to run KubeNova as a **shared service** that your whole team accesses via a URL — no setup on each person's machine? The [`deploy.sh`](../deploy.sh) script builds the Docker images, creates all Kubernetes resources, and exposes KubeNova externally in one command.

→ **[Team Deployment Guide](./TEAM_DEPLOYMENT.md)**

---

## Prerequisites

### Required

**Docker** — the only host dependency. Install for your platform:

| Platform | Recommended option |
|---|---|
| macOS | [Docker Desktop](https://docs.docker.com/desktop/install/mac/) or [Colima](https://github.com/abiosoft/colima) |
| Linux | [Docker Engine](https://docs.docker.com/engine/install/) |
| Windows | [Docker Desktop with WSL2](https://docs.docker.com/desktop/install/windows/) |

### Memory requirement (Ollama only)

The default LLM (`llama3.2`, 3 B parameters) needs approximately 2.5 GB of RAM inside the Docker VM. The full stack needs at least **4 GiB** allocated to Docker; **6 GiB is recommended**.

<details>
<summary>How to increase Docker memory</summary>

**Docker Desktop (macOS / Windows)**
1. Open Docker Desktop
2. Go to **Settings → Resources → Advanced**
3. Set **Memory** to at least 6 GiB
4. Click **Apply & Restart**

**Colima (macOS)**
```bash
colima stop
colima start --cpu 4 --memory 6
```

**Linux (Docker Engine)**
Docker Engine uses host RAM directly — no separate VM. Run `free -h` to check available memory and close other applications if needed.

</details>

If you prefer a cloud LLM (no memory constraint), skip the memory step and see [LLM Providers](#llm-providers) below.

### Optional

- A kubeconfig (`~/.kube/config`) with at least one cluster context. KubeNova starts without one and picks it up automatically when you add it later.

---

## LLM providers

Edit `.env` to choose your LLM. The default is Ollama running inside Docker — free and requires no API key.

### Ollama in Docker (default — free, no API key)

```env
COMPOSE_PROFILES=ollama
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
LLM_API_KEY=
LLM_BASE_URL=http://ollama:11434
```

Use `llama3.1:8b` for better quality (requires ~5 GB Docker memory).

### Anthropic Claude

```env
COMPOSE_PROFILES=
LLM_PROVIDER=anthropic
LLM_MODEL=claude-haiku-4-5-20251001
LLM_API_KEY=sk-ant-...
LLM_BASE_URL=
```

Get a key at [console.anthropic.com](https://console.anthropic.com).

### Google Gemini

```env
COMPOSE_PROFILES=
LLM_PROVIDER=openai
LLM_MODEL=gemini-2.0-flash
LLM_API_KEY=<google-ai-studio-key>
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```

Get a key at [aistudio.google.com](https://aistudio.google.com).

### Ollama on the host (Apple Silicon — GPU via Metal)

```env
COMPOSE_PROFILES=
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
LLM_API_KEY=
LLM_BASE_URL=http://host.docker.internal:11434
```

```bash
brew install ollama && brew services start ollama && ollama pull llama3.2
```

See [LLM_PROVIDERS.md](./LLM_PROVIDERS.md) for the full reference.

---

## Architecture overview

```
Browser (React + Vite)
     │
     ├── REST /api/*  ──────► FastAPI (Python 3.11)
     └── WS /api/ws/* ──────►     │
                                  ├── LangGraph Agent
                                  │       ├── Anthropic Claude
                                  │       ├── OpenAI / Gemini
                                  │       └── Ollama (runs in Docker)
                                  ├── Kubernetes SDK ──► Clusters
                                  └── SQLite Audit Log
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full design explanation and Mermaid diagrams.

---

## Common commands

```bash
./start.sh            # recommended first-run entry point
make start            # same as ./start.sh
make dev              # hot-reload mode (source files mounted)
make build            # rebuild Docker images
make test             # all tests (backend pytest + frontend vitest)
make lint             # ruff + mypy + eslint + tsc
make clean            # stop containers and remove volumes
```

---

## Documentation

| Document | Description |
|---|---|
| [TEAM_DEPLOYMENT.md](./TEAM_DEPLOYMENT.md) | Deploy KubeNova to a cluster for the whole team to share |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System design, data flow, LangGraph state machine |
| [API.md](./API.md) | Full REST and WebSocket API reference |
| [LLM_PROVIDERS.md](./LLM_PROVIDERS.md) | Configuring Anthropic, OpenAI, Gemini, and Ollama |
| [MULTI_CLUSTER.md](./MULTI_CLUSTER.md) | Multi-cluster setup and RBAC requirements |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Dev setup, code standards, PR checklist |
| [SECURITY.md](./SECURITY.md) | Threat model, API key handling, responsible disclosure |

---

## License

Apache 2.0 — see [LICENSE](../LICENSE).
