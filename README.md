# KubeNova

AI-native Kubernetes operations platform with natural language chat, real-time resource visualization, and an automated dry-run safety approval gate.

---

## Why It Exists

Managing and diagnosing Kubernetes clusters requires deep kubectl fluency and constant context-switching between terminal windows, dashboards, and log aggregators. KubeNova provides a unified browser interface that translates natural language queries into safe cluster operations, streams live pod logs and cluster events via WebSockets, and enforces a mandatory dry-run preview and human approval workflow before executing modifying commands.

---

## Quickstart

```bash
# 1. Clone the repository
git clone https://github.com/kubenova/kubenova.git
cd kubenova

# 2. Start the local stack (auto-provisions .env and starts Ollama)
./start.sh
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Documentation

- [Getting Started](docs/getting-started.md) — Prerequisites, Docker installation, Ollama memory allocation, and first run.
- [Configuration](docs/configuration.md) — Environment variables, LLM backends (Ollama, Claude, Gemini, OpenAI), and per-session keys.
- [Architecture](docs/architecture.md) — System design, LangGraph state machine, safety gates, and data flows.
- [Deployment](docs/deployment.md) — In-cluster production deployment with Helm, ingress, and team access.
- [API Reference](docs/api.md) — Complete REST and WebSocket endpoint specifications and payload schemas.
- [Multi-Cluster](docs/multi-cluster.md) — Multi-cluster discovery, kubeconfig switching, and RBAC requirements.
- [Development](docs/development.md) — Local development workflow, hot-reload mode, and running test suites.
- [Contributing](CONTRIBUTING.md) — Contribution guidelines, code standards, and PR checklist.
- [Security Policy](SECURITY.md) — Threat model, API key isolation, and dry-run safety gate guarantees.

---

## Architecture

KubeNova connects a React frontend to a FastAPI backend powered by a stateful LangGraph agent:

```
Browser UI (React + Vite) ◄──► WebSocket / REST ◄──► FastAPI Backend ──► LangGraph Agent ──► Kubernetes API
```

For detailed architectural concerns, state graphs, and Mermaid diagrams, see [Architecture](docs/architecture.md).

---

## Contributing & License

- Contributing guidelines and code standards are in [CONTRIBUTING.md](CONTRIBUTING.md).
- Security policies and vulnerability disclosures are in [SECURITY.md](SECURITY.md).
- Licensed under the Apache License 2.0.
