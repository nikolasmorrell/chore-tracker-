"""Owner-only admin routes."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, text

from app.api.deps import SessionDep, require_role
from app.core.config import get_settings
from app.db.models.audit import AuditLog
from app.db.models.user import User
from app.schemas.audit import AuditLogRead
from app.schemas.common import CursorPage

router = APIRouter()


@router.get("/health", summary="Deep health + dependency check (owner-only)")
async def deep_health(
    session: SessionDep,
    _user: Annotated[User, Depends(require_role("owner"))],
) -> dict[str, str]:
    """Returns individual status for DB and Redis. Useful for support triage."""
    settings = get_settings()
    checks: dict[str, str] = {}

    try:
        await session.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as exc:
        checks["db"] = f"fail: {exc}"

    try:
        client: aioredis.Redis = aioredis.from_url(settings.redis_url)  # type: ignore[no-untyped-call]
        await client.ping()
        await client.aclose()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"fail: {exc}"

    checks["status"] = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return checks


@router.get(
    "/audit-logs",
    response_model=CursorPage[AuditLogRead],
    summary="List this tenant's audit log entries (newest first)",
)
async def list_audit_logs(
    session: SessionDep,
    user: Annotated[User, Depends(require_role("owner", "admin"))],
    limit: int = Query(50, ge=1, le=200),
    cursor: UUID | None = Query(None),
    action: str | None = Query(None, description="Filter by action prefix, e.g. 'billing'"),
) -> CursorPage[AuditLogRead]:
    q = (
        select(AuditLog)
        .where(AuditLog.tenant_id == user.tenant_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit + 1)
    )
    if cursor is not None:
        pivot = await session.scalar(select(AuditLog).where(AuditLog.id == cursor))
        if pivot is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid cursor")
        q = q.where(AuditLog.created_at <= pivot.created_at, AuditLog.id != pivot.id)
    if action:
        q = q.where(AuditLog.action.like(f"{action}%"))

    rows = list(await session.scalars(q))
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = str(items[-1].id) if has_more else None
    return CursorPage(
        items=[AuditLogRead.model_validate(r) for r in items],
        next_cursor=next_cursor,
    )
