"""User management routes (admin+ required)."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("", summary="List users in the tenant")
async def list_users() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")


@router.post("/invite", summary="Invite a new teammate by email")
async def invite_user() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")


@router.patch("/{user_id}", summary="Update a teammate's role or status")
async def update_user(user_id: UUID) -> None:  # noqa: ARG001
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")


@router.delete("/{user_id}", summary="Deactivate a teammate")
async def delete_user(user_id: UUID) -> None:  # noqa: ARG001
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")
