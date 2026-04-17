"""Stripe webhook endpoint.

Signature verification and event dispatch land in Phase 5. Phase 1 only
registers the route so the Stripe dashboard can target the URL.
"""
from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.post("", summary="Stripe webhook receiver (signed)")
async def stripe_webhook() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 5")
