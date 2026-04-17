"""Shared pytest fixtures.

Phase 1 keeps fixtures minimal — an httpx AsyncClient against the FastAPI app.
Phase 2 adds a testcontainers-backed Postgres + RLS-aware session fixture.
"""
from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
