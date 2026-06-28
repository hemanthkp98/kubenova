#!/bin/sh
# KubeNova quick-start script — works on macOS, Linux, and Windows (Git Bash / WSL2).
#
# Usage:
#   ./start.sh             start with defaults (Ollama, free, no API key)
#   ./start.sh --build     rebuild Docker images before starting
#   ./start.sh -d          start in background (detached)
#   ./start.sh --help      show this message

set -e

case "$1" in --help|-h)
    echo "Usage: ./start.sh [docker compose up flags]"
    echo ""
    echo "  First run: copies .env.example → .env (if .env is absent)"
    echo "  Default LLM: Ollama running inside Docker (free, no API key)"
    echo "  Edit .env to switch to Anthropic or Gemini."
    echo ""
    echo "  Open http://localhost:5173 after the stack is healthy."
    exit 0
    ;;
esac

# Step 1 — bootstrap config
if [ ! -f .env ]; then
    cp .env.example .env
    echo "→ Created .env from .env.example"
    echo "  (Default: Ollama, free. Edit .env to change the LLM provider.)"
    echo ""
fi

# Step 2 — verify Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "✗ Docker is not running." >&2
    echo "  Start Docker Desktop (macOS/Windows) or 'sudo systemctl start docker' (Linux)." >&2
    exit 1
fi

# Step 3 — memory preflight check (Ollama needs ≥ 4 GiB in the Docker VM)
if grep -q 'COMPOSE_PROFILES=ollama' .env 2>/dev/null; then
    MEM_BYTES=$(docker info --format '{{.MemTotal}}' 2>/dev/null || echo 0)
    # 4 GiB = 4294967296 bytes
    if [ "$MEM_BYTES" -gt 0 ] && [ "$MEM_BYTES" -lt 4294967296 ]; then
        MEM_GIB=$(( MEM_BYTES / 1073741824 ))
        echo "⚠  Docker has only ${MEM_GIB} GiB of RAM available." >&2
        echo "   Ollama (llama3.2) needs at least 4 GiB — the model will likely be killed." >&2
        echo "" >&2
        echo "   Fix for Docker Desktop (macOS / Windows):" >&2
        echo "     Settings → Resources → Memory → set to 6 GiB → Apply & Restart" >&2
        echo "" >&2
        echo "   Fix for Colima (macOS):" >&2
        echo "     colima stop && colima start --cpu 4 --memory 6" >&2
        echo "" >&2
        echo "   Fix for Linux:" >&2
        echo "     Docker Engine uses host RAM directly — check 'free -h' and close other apps." >&2
        echo "" >&2
        echo "   Alternatively, switch to a cloud LLM (no memory constraint):" >&2
        echo "     Edit .env and uncomment the Anthropic or Gemini block." >&2
        echo "" >&2
        printf "   Continue anyway? [y/N] " >&2
        read -r REPLY
        case "$REPLY" in y|Y) ;; *) exit 1 ;; esac
        echo ""
    fi
fi

echo "→ Starting KubeNova…"
echo "  First run: Ollama will pull the model (~2 GB). This may take a few minutes."
echo "  Once healthy, open: http://localhost:5173"
echo ""

exec docker compose up "$@"
