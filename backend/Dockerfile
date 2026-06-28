# syntax=docker/dockerfile:1
# KubeNova Backend — Multi-stage Dockerfile
# Stage 1: builder — compile Python wheels
# Stage 2: runtime — slim image with non-root user

# ---- builder ----
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# ---- dev ----
FROM builder AS dev

WORKDIR /app

RUN pip install --no-cache-dir --find-links=/build/wheels -r /build/requirements.txt

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

# ---- runtime ----
FROM python:3.11-slim AS runtime

# Install kubectl (pinned version, auto-detected architecture).
ARG KUBECTL_VERSION=v1.30.2
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && \
    ARCH=$(dpkg --print-architecture) && \
    curl -fsSL "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${ARCH}/kubectl" \
        -o /usr/local/bin/kubectl && \
    chmod +x /usr/local/bin/kubectl && \
    kubectl version --client && \
    apt-get remove -y curl && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user.
RUN groupadd --gid 1001 kubenova && \
    useradd --uid 1001 --gid 1001 --no-create-home --shell /sbin/nologin kubenova

WORKDIR /app

# Install pre-built wheels from the builder stage.
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && \
    rm -rf /wheels

# Copy application code.
COPY app/ ./app/

# Create data directory and set full ownership before dropping to non-root user.
# Docker initialises a new named volume by copying the image directory — doing
# this ensures the volume root is writable by kubenova on first creation.
RUN mkdir -p /app/data && chown -R kubenova:kubenova /app

USER kubenova

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
