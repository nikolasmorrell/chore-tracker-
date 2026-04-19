"""Tenant-scoping helpers.

Every authenticated request must set `app.current_tenant` on the active DB
connection so that Postgres RLS policies filter every row. The `set_current_tenant`
helper is called from a FastAPI dependency in `app.api.deps`.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def set_current_tenant(session: AsyncSession, tenant_id: UUID) -> None:
    """Bind the current tenant for the remainder of this connection/transaction."""
    await session.execute(
        text("SELECT set_config('app.current_tenant', :tid, true)"),
        {"tid": str(tenant_id)},
    )


async def clear_current_tenant(session: AsyncSession) -> None:
    await session.execute(text("SELECT set_config('app.current_tenant', '', true)"))
