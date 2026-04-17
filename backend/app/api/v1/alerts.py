"""Expiration + compliance alerts."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("", summary="List active alerts")
async def list_alerts() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")


@router.post("/{alert_id}/dismiss", summary="Mark an alert as dismissed")
async def dismiss_alert(alert_id: UUID) -> None:  # noqa: ARG001
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")
