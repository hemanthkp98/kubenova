# KubeNova Makefile
# Run `make help` to see all available targets.

.PHONY: help start dev build test lint helm-lint helm-template clean

# Default target.
.DEFAULT_GOAL := help

BACKEND_DIR  := backend
FRONTEND_DIR := frontend
HELM_DIR     := helm/kubenova
COMPOSE      := docker compose -f docker-compose.yml
COMPOSE_DEV  := $(COMPOSE) -f docker-compose.dev.yml

## help: Print this help message.
help:
	@echo "KubeNova make targets:"
	@grep -E '^## ' Makefile | sed 's/## /  /'

## start: First-time setup — copies .env if missing, then starts KubeNova.
##        Default provider is Ollama (free). Edit .env to switch providers.
start:
	@[ -f .env ] || (cp .env.example .env && echo "→ Created .env from .env.example")
	@docker info >/dev/null 2>&1 || (echo "✗ Docker is not running. Start Docker Desktop and try again." && exit 1)
	@echo "→ Starting KubeNova (first run downloads Ollama model ~2 GB)…"
	$(COMPOSE) up

## dev: Start in development mode with hot-reload.
dev:
	@[ -f .env ] || (cp .env.example .env && echo "→ Created .env from .env.example")
	$(COMPOSE_DEV) down --remove-orphans 2>/dev/null || true
	$(COMPOSE_DEV) up

## build: Build (or rebuild) Docker images.
build:
	@echo "→ Building Docker images…"
	$(COMPOSE) build

## test: Run all backend and frontend tests.
test: test-backend test-frontend

## test-backend: Run backend pytest suite inside Docker.
test-backend:
	@echo "→ Running backend tests…"
	docker exec kubenova-backend python -m pytest --tb=short -v

## test-frontend: Run frontend Vitest suite.
test-frontend:
	@echo "→ Running frontend tests…"
	cd $(FRONTEND_DIR) && npm run test

## test-e2e: Run Playwright end-to-end tests (requires running instance).
test-e2e:
	@echo "→ Running E2E tests…"
	cd $(FRONTEND_DIR) && npx playwright test tests/e2e/

## lint: Run all linters (Python + TypeScript).
lint: lint-backend lint-frontend

## lint-backend: Run ruff + mypy on the backend.
lint-backend:
	@echo "→ Linting backend…"
	cd $(BACKEND_DIR) && ruff check app/ tests/
	cd $(BACKEND_DIR) && mypy app/ --ignore-missing-imports

## lint-frontend: Run eslint + tsc --noEmit on the frontend.
lint-frontend:
	@echo "→ Linting frontend…"
	cd $(FRONTEND_DIR) && npm run lint
	cd $(FRONTEND_DIR) && npx tsc --noEmit

## helm-lint: Lint the Helm chart.
helm-lint:
	@echo "→ Linting Helm chart…"
	helm lint $(HELM_DIR)

## helm-template: Render Helm templates for inspection.
helm-template:
	helm template kubenova $(HELM_DIR)

## clean: Stop containers, remove volumes and frontend build artefacts.
clean:
	@echo "→ Stopping containers…"
	$(COMPOSE) down --volumes --remove-orphans || true
	@echo "→ Removing frontend build artefacts…"
	rm -rf $(FRONTEND_DIR)/dist
	@echo "✓ Clean."
