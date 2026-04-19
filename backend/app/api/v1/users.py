"""User management routes (admin+ required)."""
from __future__ import annotations

from datetime import timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import SessionDep, require_role
from app.core.config import get_settings
from app.core.security import generate_secret_token, hash_secret_token, utcnow
from app.db.models.user import Invite, User
from app.schemas.common import CursorPage, Message
from app.schemas.user import InviteCreate, InviteRead, UserRead, UserUpdate
from app.services import audit
from app.services.notifications import send_email

router = APIRouter()


@router.get("", response_model=CursorPage[UserRead], summary="List users in the tenant")
async def list_users(
    session: SessionDep,
    user: Annotated[User, Depends(require_role("owner", "admin"))],
    limit: int = Query(default=100, ge=1, le=500),
) -> CursorPage[UserRead]:
    del user
    rows = (
        await session.scalars(select(User).order_by(User.created_at.desc()).limit(limit))
    ).all()
    return CursorPage[UserRead](items=[UserRead.model_validate(r) for r in rows])


@router.post(
    "/invite",
    response_model=InviteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Invite a new teammate by email",
)
async def invite_user(
    payload: InviteCreate,
    session: SessionDep,
    user: Annotated[User, Depends(require_role("owner", "admin"))],
) -> InviteRead:
    settings = get_settings()
    plaintext = generate_secret_token()
    invite = Invite(
        tenant_id=user.tenant_id,
        email=payload.email.lower().strip(),
        role=payload.role,
        token_hash=hash_secret_token(plaintext),
        expires_at=utcnow() + timedelta(seconds=settings.invite_ttl_seconds),
    )
    session.add(invite)
    await session.flush()
    await audit.record(
        session,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="user.invited",
        entity_type="invite",
        entity_id=invite.id,
        extra={"email": invite.email, "role": invite.role},
    )
    await session.commit()

    link = f"{settings.frontend_base_url}/accept-invite?token={plaintext}"
    await send_email(
        to=invite.email,
        subject="You're invited to Serva",
        html=f'<p><a href="{link}">Accept your invite</a> — expires in 7 days.</p>',
        text=f"Accept your invite: {link}",
    )
    return InviteRead.model_validate(invite)


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Update a teammate's role or status",
)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    session: SessionDep,
    current: Annotated[User, Depends(require_role("owner", "admin"))],
) -> UserRead:
    target = await session.scalar(select(User).where(User.id == user_id))
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    if target.role == "owner" and current.role != "owner":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "cannot modify owner")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(target, field, value)
    await session.flush()
    await audit.record(
        session,
        tenant_id=current.tenant_id,
        actor_user_id=current.id,
        action="user.updated",
        entity_type="user",
        entity_id=target.id,
    )
    await session.commit()
    return UserRead.model_validate(target)


@router.delete(
    "/{user_id}",
    response_model=Message,
    summary="Deactivate a teammate",
)
async def delete_user(
    user_id: UUID,
    session: SessionDep,
    current: Annotated[User, Depends(require_role("owner", "admin"))],
) -> Message:
    target = await session.scalar(select(User).where(User.id == user_id))
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    if target.id == current.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "cannot deactivate yourself")
    if target.role == "owner":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "cannot deactivate owner")
    target.is_active = False
    await session.flush()
    await audit.record(
        session,
        tenant_id=current.tenant_id,
        actor_user_id=current.id,
        action="user.deactivated",
        entity_type="user",
        entity_id=target.id,
    )
    await session.commit()
    return Message(detail="user deactivated")
