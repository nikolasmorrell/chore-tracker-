"""Customer CRUD routes."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("", summary="List customers")
async def list_customers() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")


@router.post("", summary="Create a customer", status_code=status.HTTP_201_CREATED)
async def create_customer() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")


@router.get("/{customer_id}", summary="Fetch a single customer")
async def get_customer(customer_id: UUID) -> None:  # noqa: ARG001
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")


@router.patch("/{customer_id}", summary="Update a customer")
async def update_customer(customer_id: UUID) -> None:  # noqa: ARG001
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")


@router.delete("/{customer_id}", summary="Delete a customer")
async def delete_customer(customer_id: UUID) -> None:  # noqa: ARG001
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")
