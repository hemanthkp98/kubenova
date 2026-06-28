# LLM Provider Configuration

KubeNova supports three LLM backends. All are configured via environment variables in `.env`.

The default is **Ollama running inside Docker** — free, no API key, no host installation.

---

## Ollama in Docker (default — free, no API key)

```env
COMPOSE_PROFILES=ollama
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
LLM_API_KEY=
LLM_BASE_URL=http://ollama:11434
```

The Ollama container starts automatically when `COMPOSE_PROFILES=ollama` is set. The model is downloaded on first run (~2 GB) and cached in a Docker volume for subsequent starts.

**Memory requirement**: the Docker VM must have ≥ 4 GiB RAM (6 GiB recommended). See the [README](./README.md#memory-requirement-ollama-only) for per-platform instructions.

**Available models** (set via `LLM_MODEL`):
| Model | Size | Quality |
|---|---|---|
| `llama3.2` | ~2 GB | Good — default |
| `llama3.1:8b` | ~5 GB | Better (needs ≥ 8 GiB Docker memory) |
| `mistral` | ~4 GB | Alternative |

---

## Ollama on the host (Apple Silicon — GPU via Metal)

For better performance on Apple Silicon, run Ollama natively so it can use the Metal GPU.

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

## Anthropic (Claude)

```env
COMPOSE_PROFILES=
LLM_PROVIDER=anthropic
LLM_MODEL=claude-haiku-4-5-20251001
LLM_API_KEY=sk-ant-your-key-here
LLM_BASE_URL=
```

Supported models: `claude-haiku-4-5-20251001`, `claude-sonnet-4-6`, `claude-opus-4-8`.

Get an API key at [console.anthropic.com](https://console.anthropic.com).

---

## Google Gemini

```env
COMPOSE_PROFILES=
LLM_PROVIDER=openai
LLM_MODEL=gemini-2.0-flash
LLM_API_KEY=<google-ai-studio-key>
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```

Gemini uses the OpenAI-compatible endpoint. Get a key at [aistudio.google.com](https://aistudio.google.com).

---

## OpenAI (GPT)

```env
COMPOSE_PROFILES=
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
LLM_API_KEY=sk-your-openai-key
LLM_BASE_URL=
```

Supported models: `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`.

For Azure OpenAI, also set:
```env
LLM_BASE_URL=https://your-resource.openai.azure.com/
```

---

## Per-session keys (UI)

The LLM Config modal (top-right gear icon) lets operators supply an API key per browser session. Keys entered in the UI are stored in `sessionStorage` and are **cleared when the tab closes**. They are never sent to the audit log or stored on the server.

---

## Security notes

- API keys are **never** written to the SQLite audit log.
- Keys set via environment variable are only accessible to the backend process.
- The backend does not log the key value at any log level.
- For production deployments, use Kubernetes Secrets (see the Helm chart `values.yaml` `llm.apiKeySecret`).

---

## Adding a new provider

1. Create `backend/app/core/llm/my_provider.py` implementing `LLMProvider` from `base.py`.
2. Add a case in `factory.py`'s `_create_provider()` function.
3. Add the provider name to `LLM_PROVIDER` in `config.py`'s Literal type.
4. Write tests in `tests/unit/test_llm_factory.py`.
