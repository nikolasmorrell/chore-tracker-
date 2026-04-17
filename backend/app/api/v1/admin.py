"""Owner-only admin routes."""
from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("/health", summary="Deep health + dependency check (owner-only)")
async def deep_health() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")


@router.get("/audit-logs", summary="List this tenant's audit log entries")
async def list_audit_logs() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")
