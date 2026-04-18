"""Expiration + compliance alerts."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser, SessionDep
from app.core.security import utcnow
from app.db.models.document import Alert
from app.schemas.common import CursorPage
from app.schemas.document import AlertRead, AlertStatus
from app.services import audit

router = APIRouter()


@router.get("", response_model=CursorPage[AlertRead], summary="List alerts")
async def list_alerts(
    session: SessionDep,
    user: CurrentUser,
    status_filter: AlertStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
) -> CursorPage[AlertRead]:
    stmt = select(Alert).order_by(Alert.due_at.asc()).limit(limit)
    if status_filter is not None:
        stmt = stmt.where(Alert.status == status_filter)
    rows = (await session.scalars(stmt)).all()
    return CursorPage[AlertRead](items=[AlertRead.model_validate(r) for r in rows])


@router.post("/{alert_id}/dismiss", response_model=AlertRead, summary="Mark an alert as dismissed")
async def dismiss_alert(
    alert_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> AlertRead:
    alert = await session.scalar(select(Alert).where(Alert.id == alert_id))
    if alert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "alert not found")
    alert.status = "dismissed"
    alert.sent_at = alert.sent_at or utcnow()
    await session.flush()
    await audit.record(
        session,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="alert.dismissed",
        entity_type="alert",
        entity_id=alert.id,
    )
    await session.commit()
    return AlertRead.model_validate(alert)
