"""Redis token-bucket rate limiter (skeleton).

Phase 2 wires this into a FastAPI middleware + per-route dependency. The
current file defines the interface so the middleware can be added later
without touching call sites.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    reset_seconds: int


async def check(key: str, limit: int, window_seconds: int) -> RateLimitResult:  # pragma: no cover
    raise NotImplementedError("Rate limiter implemented in Phase 2")
