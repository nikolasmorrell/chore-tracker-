"""Tenant self-service routes."""
from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("/me", summary="Return the caller's tenant")
async def get_current_tenant() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")


@router.patch("/me", summary="Update tenant name / settings (owner-only)")
async def update_current_tenant() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")
