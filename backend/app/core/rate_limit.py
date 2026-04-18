"""Redis fixed-window rate limiter + FastAPI middleware.

We pin to a fixed window for simplicity — per (ip_or_tenant_bucket, minute).
If Redis is unreachable the limiter fails open so an outage of the cache tier
doesn't take down the API. That trade-off is logged.
"""
from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from fastapi import Request
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    reset_seconds: int


_redis: Redis | None = None


def _get_redis() -> Redis:
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def check(key: str, limit: int, window_seconds: int) -> RateLimitResult:
    redis = _get_redis()
    bucket_sec = int(time.time() // window_seconds) * window_seconds
    full_key = f"rl:{key}:{bucket_sec}"
    try:
        pipe = redis.pipeline()
        pipe.incr(full_key)
        pipe.expire(full_key, window_seconds)
        count, _ = await pipe.execute()
        remaining = max(0, limit - int(count))
        reset = bucket_sec + window_seconds - int(time.time())
        return RateLimitResult(allowed=int(count) <= limit, remaining=remaining, reset_seconds=reset)
    except Exception:
        logger.warning("rate_limit.redis_unavailable", extra={"key": key})
        return RateLimitResult(allowed=True, remaining=limit, reset_seconds=window_seconds)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP rate limit applied to every /api/v1 request.

    Auth-related routes keep a tighter, separate bucket so brute-forcers can't
    burn the whole IP budget before being throttled.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if not request.url.path.startswith("/api/v1/"):
            return await call_next(request)

        settings = get_settings()
        client_ip = _client_ip(request)
        scope = "auth" if request.url.path.startswith("/api/v1/auth/") else "api"
        limit = 20 if scope == "auth" else settings.rate_limit_per_ip_per_minute
        result = await check(f"{scope}:ip:{client_ip}", limit=limit, window_seconds=60)
        if not result.allowed:
            return JSONResponse(
                {"detail": "rate limit exceeded"},
                status_code=429,
                headers={"Retry-After": str(result.reset_seconds)},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        return response


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"
