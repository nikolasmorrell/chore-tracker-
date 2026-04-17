"""Call history routes."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("", summary="List calls (most recent first)")
async def list_calls() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 3")


@router.get("/{call_id}", summary="Fetch a call with transcript + summary")
async def get_call(call_id: UUID) -> None:  # noqa: ARG001
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 3")
