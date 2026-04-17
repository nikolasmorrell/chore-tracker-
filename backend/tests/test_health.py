"""Smoke tests for the Phase 1 scaffolding."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_healthz(client: AsyncClient) -> None:
    r = await client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_openapi_includes_v1_routes(client: AsyncClient) -> None:
    r = await client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    assert "/api/v1/auth/signup" in paths
    assert "/api/v1/documents" in paths
    assert "/api/v1/webhooks/twilio/voice" in paths
