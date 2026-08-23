# Configuration

Configure LLM backends, environment variables, model parameters, and memory settings for KubeNova.

---

## Environment Variables Reference

KubeNova is configured via environment variables in `.env` or injected Kubernetes Secrets:

| Variable | Type | Default | Description |
|---|---|---|---|
| `COMPOSE_PROFILES` | `string` | `ollama` | Docker Compose profile (`ollama` to run local Ollama container, empty for external LLMs). |
| `LLM_PROVIDER` | `string` | `ollama` | Backend LLM provider: `ollama`, `anthropic`, or `openai` (used for OpenAI & Gemini). |
| `LLM_MODEL` | `string` | `llama3.2` | Model identifier to query. |
| `LLM_API_KEY` | `string` | — | API key for Anthropic, OpenAI, or Google Gemini. |
| `LLM_BASE_URL` | `string` | `http://ollama:11434` | Base endpoint URL for Ollama, Azure OpenAI, or custom OpenAI-compatible proxies. |
| `KUBECONFIG` | `string` | `~/.kube/config` | Path to kubeconfig file containing cluster contexts. |
| `DATABASE_URL` | `string` | `sqlite:///./data/kubenova.db` | Storage path for session history and audit log database. |
| `LOG_LEVEL` | `string` | `INFO` | Application log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

---

## LLM Providers

### 1. Ollama in Docker (Default — Free, No API Key)

```env
COMPOSE_PROFILES=ollama
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
LLM_API_KEY=
LLM_BASE_URL=http://ollama:11434
```

The Ollama container starts automatically when `COMPOSE_PROFILES=ollama` is set. The model is downloaded on first run (~2 GB) and cached in a Docker volume for subsequent starts.

**Memory Requirement**: The Docker VM must have ≥ 4 GiB RAM (6 GiB recommended). See [Getting Started](getting-started.md#memory-requirements-ollama-local-model) for per-platform instructions.

**Available Models**:
| Model | Size | Quality |
|---|---|---|
| `llama3.2` | ~2 GB | Good — default |
| `llama3.1:8b` | ~5 GB | Better (needs ≥ 8 GiB Docker memory) |
| `mistral` | ~4 GB | Alternative |

---

### 2. Ollama on the Host (Apple Silicon — GPU via Metal)

For accelerated performance on Apple Silicon, run Ollama natively so it can utilize the Metal GPU:

```env
COMPOSE_PROFILES=
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
LLM_API_KEY=
LLM_BASE_URL=http://host.docker.internal:11434
```

```bash
brew install ollama
brew services start ollama
ollama pull llama3.2
```

---

### 3. Anthropic Claude

```env
COMPOSE_PROFILES=
LLM_PROVIDER=anthropic
LLM_MODEL=claude-haiku-4-5-20251001
LLM_API_KEY=sk-ant-your-key-here
LLM_BASE_URL=
```

- Supported models: `claude-haiku-4-5-20251001`, `claude-sonnet-4-6`, `claude-opus-4-8`.
- Obtain an API key at [Anthropic Console](https://console.anthropic.com/).

---

### 4. Google Gemini

```env
COMPOSE_PROFILES=
LLM_PROVIDER=openai
LLM_MODEL=gemini-2.0-flash
LLM_API_KEY=<YOUR_GOOGLE_AI_STUDIO_KEY>
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```

Gemini uses the OpenAI-compatible endpoint. Obtain an API key at [Google AI Studio](https://aistudio.google.com).

---

### 5. OpenAI (GPT)

```env
COMPOSE_PROFILES=
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
LLM_API_KEY=sk-your-openai-key
LLM_BASE_URL=
```

- Supported models: `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`.
- For Azure OpenAI, set:
  ```env
  LLM_BASE_URL=https://your-resource.openai.azure.com/
  ```

---

## Per-Session Keys (UI)

The LLM Config modal in the UI (top-right gear icon) allows operators to supply an API key per browser session. Keys entered in the UI are stored in `sessionStorage` and are **cleared when the browser tab closes**. They are never recorded in the audit log or persisted on the server.

---

## Security Notes

- API keys are **never** written to the SQLite audit log.
- Keys configured via environment variables are only accessible to the backend process.
- The backend does not log key values at any verbosity level.
- For production Kubernetes deployments, inject keys via Kubernetes Secrets (see [Deployment](deployment.md)).
