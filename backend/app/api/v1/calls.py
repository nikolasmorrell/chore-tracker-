"""Call history routes."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, SessionDep
from app.db.models.call import Call
from app.schemas.call import CallDetail, CallRead, CallTurnRead
from app.schemas.common import CursorPage

router = APIRouter()


@router.get("", response_model=CursorPage[CallRead], summary="List calls (most recent first)")
async def list_calls(
    session: SessionDep,
    user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
) -> CursorPage[CallRead]:
    rows = (
        await session.scalars(select(Call).order_by(Call.created_at.desc()).limit(limit))
    ).all()
    return CursorPage[CallRead](items=[CallRead.model_validate(r) for r in rows])


@router.get("/{call_id}", response_model=CallDetail, summary="Fetch a call with transcript")
async def get_call(
    call_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> CallDetail:
    call = await session.scalar(
        select(Call)
        .where(Call.id == call_id)
        .options(selectinload(Call.turns))
    )
    if call is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "call not found")
    turns = sorted(call.turns, key=lambda t: t.turn_index)
    payload = CallRead.model_validate(call).model_dump()
    return CallDetail(
        **payload,
        turns=[CallTurnRead.model_validate(t) for t in turns],
    )
