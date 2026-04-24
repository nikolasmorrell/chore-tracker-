"""FastAPI application factory.

Boots the HTTP app, configures logging + Sentry, mounts every v1 router, and
exposes `/healthz` (liveness) + `/readyz` (readiness — pings DB + Redis).
"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.rate_limit import RateLimitMiddleware
from app.db.session import engine

logger = logging.getLogger(__name__)


def _init_sentry() -> None:
    settings = get_settings()
    if not settings.sentry_dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.app_env,
            traces_sample_rate=settings.sentry_traces_sample_rate,
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
            send_default_pii=False,
        )
        logger.info("sentry.initialized")
    except Exception as exc:  # pragma: no cover — don't crash boot on Sentry
        logger.warning("sentry.init_failed", extra={"err": str(exc)})


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    _init_sentry()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Serva API",
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
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if settings.app_env != "test":
        app.add_middleware(RateLimitMiddleware)

    @app.get("/healthz", tags=["health"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok", "env": settings.app_env}

    @app.get("/readyz", tags=["health"])
    async def readyz() -> JSONResponse:
        db_ok = True
        redis_ok = True
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception as exc:
            db_ok = False
            logger.warning("readyz.db_fail", extra={"err": str(exc)})
        try:
            client: redis.Redis = redis.from_url(settings.redis_url)  # type: ignore[no-untyped-call]
            await client.ping()
            await client.aclose()
        except Exception as exc:
            redis_ok = False
            logger.warning("readyz.redis_fail", extra={"err": str(exc)})

        ready = db_ok and redis_ok
        return JSONResponse(
            status_code=status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "ready" if ready else "not_ready",
                "db": "ok" if db_ok else "fail",
                "redis": "ok" if redis_ok else "fail",
            },
        )

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
