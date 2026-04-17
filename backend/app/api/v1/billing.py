"""Stripe subscription routes."""
from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.post("/checkout-session", summary="Create a Stripe Checkout session")
async def create_checkout_session() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 5")


@router.post("/portal-session", summary="Create a Stripe billing-portal session")
async def create_portal_session() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 5")


@router.get("/subscription", summary="Fetch this tenant's current subscription")
async def get_subscription() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 5")
