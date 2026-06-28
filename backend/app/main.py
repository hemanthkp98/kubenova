"""
KubeNova FastAPI application factory.

Creates the FastAPI app, configures CORS, registers all API routers,
and sets up the lifespan context manager for startup/shutdown tasks
(DB table creation, logging configuration).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import get_settings
from app.db.database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application startup and shutdown.

    On startup: configure logging, ensure DB tables exist.
    On shutdown: log a goodbye message (connection pools close automatically).
    """
    settings = get_settings()

    # Configure loguru log level.
    logger.remove()
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=settings.KUBENOVA_LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        ),
        colorize=True,
    )

    logger.info("KubeNova starting up (env={}).", settings.KUBENOVA_ENV)
    await create_tables()
    logger.info("Database tables ready.")

    yield

    logger.info("KubeNova shutting down.")


def create_app() -> FastAPI:
    """
    Construct and configure the FastAPI application instance.

    Returns:
        Configured FastAPI app ready to be served by uvicorn.
    """
    settings = get_settings()

    app = FastAPI(
        title="KubeNova",
        description="Talk to your cluster. See it live. Fix it fast.",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # CORS — allows the Vite dev server (and any configured origins) to call the API.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.KUBENOVA_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers under /api prefix.
    from app.api.routes.audit import router as audit_router
    from app.api.routes.chat import router as chat_router
    from app.api.routes.clusters import router as clusters_router
    from app.api.routes.logs import router as logs_router
    from app.api.routes.resources import router as resources_router

    app.include_router(chat_router, prefix="/api")
    app.include_router(clusters_router, prefix="/api")
    app.include_router(resources_router, prefix="/api")
    app.include_router(logs_router, prefix="/api")
    app.include_router(audit_router, prefix="/api")

    @app.get("/healthz", tags=["health"])
    async def healthz() -> dict[str, str]:
        """Simple liveness probe used by Docker / Kubernetes."""
        return {"status": "ok"}

    return app


app = create_app()
