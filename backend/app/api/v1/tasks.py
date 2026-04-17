"""Internal task routes."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("", summary="List tasks")
async def list_tasks() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")


@router.post("", summary="Create a task", status_code=status.HTTP_201_CREATED)
async def create_task() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")


@router.patch("/{task_id}", summary="Update a task")
async def update_task(task_id: UUID) -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")


@router.post("/{task_id}/assign", summary="Assign a task to a teammate")
async def assign_task(task_id: UUID) -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")
