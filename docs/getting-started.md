# Getting Started

Get up and running with KubeNova locally using Docker Compose in under two minutes.

---

## Quickstart

Run KubeNova with two commands. No local Python or Node.js toolchains required:

```bash
# 1. Clone the repository
git clone https://github.com/kubenova/kubenova.git
cd kubenova

# 2. Start the local stack
./start.sh
```

Open [http://localhost:5173](http://localhost:5173) in your browser once the stack is healthy.

### What Happens on Startup

- **First run**: Ollama downloads the `llama3.2` model (~2 GB). This takes 2–5 minutes depending on your internet connection.
- **Subsequent runs**: The model is cached inside a Docker volume, and startup takes ~10 seconds.
- **No cluster connected?** KubeNova starts cleanly even without a kubeconfig file. The cluster panel shows an empty state; simply mount or configure a cluster context when ready.
- The `start.sh` script automatically provisions `.env` from `.env.example`, verifies Docker daemon status, and checks available memory.

---

## Prerequisites

### Required: Docker

Docker is the only required host dependency:

| Platform | Recommended Option |
|---|---|
| macOS | [Docker Desktop](https://docs.docker.com/desktop/install/mac/) or [Colima](https://github.com/abiosoft/colima) |
| Linux | [Docker Engine](https://docs.docker.com/engine/install/) |
| Windows | [Docker Desktop with WSL2](https://docs.docker.com/desktop/install/windows/) |

### Memory Requirements (Ollama Local Model)

The default local LLM (`llama3.2`, 3B parameters) requires approximately 2.5 GB of RAM inside Docker. The full stack requires at least **4 GiB** allocated to Docker (**6 GiB is recommended**).

#### Allocating Docker Memory

- **Docker Desktop (macOS / Windows)**:
  1. Open Docker Desktop Settings.
  2. Navigate to **Resources → Advanced**.
  3. Set **Memory** to at least 6 GiB.
  4. Click **Apply & Restart**.
- **Colima (macOS)**:
  ```bash
  colima stop
  colima start --cpu 4 --memory 6
  ```
- **Linux (Docker Engine)**:
  Docker uses host RAM directly. Run `free -h` to verify available memory.

> [!TIP]
> If you prefer using cloud LLMs (Claude, Gemini, OpenAI) without local RAM constraints, see [Configuration](configuration.md#llm-providers).

---

## Next Steps

- ⚙️ **Configure Providers**: See [Configuration](configuration.md) to use Anthropic Claude, Google Gemini, or OpenAI.
- 🏢 **Team Deployment**: See [Deployment](deployment.md) to deploy KubeNova as an in-cluster shared service.
- 🌐 **Multi-Cluster**: See [Multi-Cluster](multi-cluster.md) to connect multiple Kubernetes environments.
- 🛠️ **Development**: See [Development](development.md) for hot-reloading dev mode.
