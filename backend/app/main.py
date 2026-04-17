"""FastAPI application factory.

Phase 1: mounts all v1 routers as stubs and exposes /healthz + /docs so the
deploy pipeline can be verified before business logic lands.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    configure_logging()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Chore Tracker API",
        version="0.1.0",
        description="Multi-tenant AI operations platform for service businesses.",
        lifespan=lifespan,
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz", tags=["health"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok", "env": settings.app_env}

    @app.get("/readyz", tags=["health"])
    async def readyz() -> dict[str, str]:
        return {"status": "ready"}

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
