# Contributing to KubeNova

Thank you for considering a contribution! This document covers the development setup, code standards, and PR checklist.

---

## Prerequisites

- Python 3.11+
- Node 20+
- Docker and Docker Compose
- `kubectl` in PATH
- A local Kubernetes cluster (minikube or kind recommended)
- An LLM API key (or Ollama running locally)

---

## Local development setup

```bash
# 1. Clone the repo
git clone https://github.com/kubenova/kubenova.git
cd kubenova

# 2. Copy and configure environment
cp .env.example .env
# Edit .env: set LLM_PROVIDER, LLM_MODEL, LLM_API_KEY

# 3. Install dependencies
make install

# 4. Start the development environment (hot-reload)
make dev
# Backend:  http://localhost:8000
# Frontend: http://localhost:5173
```

### Backend only (without Docker)

```bash
cd backend
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend only (without Docker)

```bash
cd frontend
npm install
npm run dev
```

---

## Running tests

```bash
make test         # all tests
make test-backend # pytest only
make test-frontend # vitest only
make test-e2e     # playwright (requires running instance)
```

---

## How to add a new LLM provider

1. Create `backend/app/core/llm/my_provider.py`:
   ```python
   class MyProvider:
       def __init__(self, config: LLMConfig) -> None: ...
       @property
       def config(self) -> LLMConfig: ...
       def get_chat_model(self) -> BaseChatModel: ...
       def is_available(self) -> bool: ...
   ```
2. Add a case to `factory.py`'s `_create_provider()`:
   ```python
   if name == "myprovider":
       from app.core.llm.my_provider import MyProvider
       return MyProvider(config)
   ```
3. Add `"myprovider"` to the `LLM_PROVIDER` Literal in `config.py`.
4. Add tests in `tests/unit/test_llm_factory.py`.
5. Document in [Configuration](docs/configuration.md).

---

## How to add a new Kubernetes resource type

1. Add a Pydantic model to `backend/app/models/resource.py`.
2. Add a `list_*` method to `backend/app/core/k8s/resources.py`.
3. Add a new GET endpoint in `backend/app/api/routes/resources.py`.
4. Add a TypeScript interface in `frontend/src/types/resource.ts`.
5. Add a React component under `frontend/src/components/resources/`.
6. Add the component to `ResourcePanel.tsx`'s tab list.
7. Add unit tests for both backend and frontend.

---

## How to add a new LangGraph node or tool

**New tool:**
1. Add a `@tool` function in `backend/app/core/agents/tools.py`.
2. Append it to `ALL_TOOLS` at the bottom of the file.
3. Write a test in `tests/unit/test_agent_tools.py`.

**New node:**
1. Add a function in `backend/app/core/agents/nodes.py`.
2. Register it in `graph.py` with `graph.add_node()`.
3. Add edges with `graph.add_edge()` or `graph.add_conditional_edges()`.
4. Update the state diagram in [Architecture](docs/architecture.md).

---

## Code standards

- **Python**: PEP 8, type hints on every function and class attribute, module-level docstring in every file.
- **TypeScript**: strict mode, no `any` (document exceptions), file-level JSDoc in every file.
- **Test coverage minimum**: 80% for backend, component smoke tests + interaction tests for frontend.
- **No hardcoded secrets**: use environment variables or the Kubernetes Secret mechanism.
- For complete command references, see [Development Guide](docs/development.md).

---

## PR checklist

Before opening a pull request:

- [ ] All tests pass (`make test`)
- [ ] Lint is clean (`make lint`)
- [ ] TypeScript compiles without errors (`cd frontend && npx tsc --noEmit`)
- [ ] Documentation updated (`docs/api.md`, `docs/architecture.md` if relevant)
- [ ] No secrets or API keys committed
- [ ] New environment variables added to `.env.example`
- [ ] Helm chart updated if Kubernetes resources changed
