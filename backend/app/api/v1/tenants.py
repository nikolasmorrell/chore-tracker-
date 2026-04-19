"""Tenant self-service routes."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, SessionDep, require_role
from app.db.models.tenant import Tenant
from app.db.models.user import User
from app.schemas.tenant import TenantRead, TenantUpdate
from app.services import audit

router = APIRouter()


@router.get("/me", response_model=TenantRead, summary="Return the caller's tenant")
async def get_current_tenant(
    session: SessionDep,
    user: CurrentUser,
) -> TenantRead:
    tenant = await session.scalar(select(Tenant).where(Tenant.id == user.tenant_id))
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "tenant not found")
    return TenantRead.model_validate(tenant)


@router.patch(
    "/me",
    response_model=TenantRead,
    summary="Update tenant name / settings (owner-only)",
)
async def update_current_tenant(
    payload: TenantUpdate,
    session: SessionDep,
    user: Annotated[User, Depends(require_role("owner"))],
) -> TenantRead:
    tenant = await session.scalar(select(Tenant).where(Tenant.id == user.tenant_id))
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "tenant not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tenant, field, value)
    await session.flush()
    await audit.record(
        session,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="tenant.updated",
        entity_type="tenant",
        entity_id=tenant.id,
    )
    await session.commit()
    return TenantRead.model_validate(tenant)
