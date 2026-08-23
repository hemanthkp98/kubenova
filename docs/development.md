# Development

Set up local development environments, run test suites, add LangGraph agent tools, and contribute to KubeNova.

---

## Local Development Setup

### Prerequisites

- **Python**: Version 3.11+
- **Node.js**: Version 20+
- **Docker & Docker Compose**
- **kubectl** in PATH
- **Local Cluster**: Minikube, Kind, or a remote kubeconfig context

### Running with Docker Compose (Hot-Reload Mode)

```bash
# 1. Clone the repository
git clone https://github.com/kubenova/kubenova.git
cd kubenova

# 2. Configure environment
cp .env.example .env
# Edit .env to set your LLM credentials

# 3. Start development stack with live file mounting
make dev
```

- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Frontend UI**: [http://localhost:5173](http://localhost:5173)

---

## Running Without Docker

### Backend (FastAPI)

```bash
cd backend
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (Next.js / Vite)

```bash
cd frontend
npm install
npm run dev
```

---

## Common Commands

| Command | Action |
|---|---|
| `./start.sh` | Recommended first-run entry point |
| `make start` | Start stack via Docker Compose |
| `make dev` | Hot-reload development mode with mounted source files |
| `make build` | Rebuild Docker images |
| `make test` | Run all unit test suites (backend + frontend) |
| `make test-backend` | Run backend pytest suite |
| `make test-frontend` | Run frontend vitest suite |
| `make test-e2e` | Run Playwright end-to-end browser tests |
| `make lint` | Run code quality linters (Ruff, MyPy, ESLint, TypeScript) |
| `make clean` | Stop containers and remove volumes |

---

## Extending KubeNova

### How to Add a New LLM Provider

1. Create `backend/app/core/llm/my_provider.py`:
   ```python
   class MyProvider:
       def __init__(self, config: LLMConfig) -> None: ...
       @property
       def config(self) -> LLMConfig: ...
       def get_chat_model(self) -> BaseChatModel: ...
       def is_available(self) -> bool: ...
   ```
2. Add a matching case in `factory.py`'s `_create_provider()`:
   ```python
   if name == "myprovider":
       from app.core.llm.my_provider import MyProvider
       return MyProvider(config)
   ```
3. Add `"myprovider"` to `LLM_PROVIDER` Literal in `config.py`.
4. Add unit tests in `tests/unit/test_llm_factory.py`.
5. Document settings in [Configuration](configuration.md).

### How to Add a New Kubernetes Resource Type

1. Add Pydantic model to `backend/app/models/resource.py`.
2. Add `list_*` method to `backend/app/core/k8s/resources.py`.
3. Add GET endpoint in `backend/app/api/routes/resources.py`.
4. Add TypeScript interface in `frontend/src/types/resource.ts`.
5. Add React component under `frontend/src/components/resources/`.
6. Register the component in `ResourcePanel.tsx`'s tab list.
7. Add unit tests for both backend and frontend.

### How to Add a New LangGraph Agent Tool or Node

**New Tool:**
1. Add `@tool` function in `backend/app/core/agents/tools.py`.
2. Append tool to `ALL_TOOLS` list.
3. Add test in `tests/unit/test_agent_tools.py`.

**New Node:**
1. Add node function in `backend/app/core/agents/nodes.py`.
2. Register node in `graph.py` with `graph.add_node()`.
3. Add edges with `graph.add_edge()` or `graph.add_conditional_edges()`.
4. Update state diagram in [Architecture](architecture.md).

---

## Contribution & Code Standards

- **Python**: PEP 8 compliance, explicit type hints on all functions and attributes, module docstrings.
- **TypeScript**: Strict mode, avoid `any` types.
- **Minimum Test Coverage**: 80% for backend; component and interaction tests for frontend.
- For complete PR guidelines, see [CONTRIBUTING.md](../CONTRIBUTING.md).
