"""Stripe webhook endpoint — receives signed events and dispatches them."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.services.billing import construct_event, handle_event

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", summary="Stripe webhook receiver (signed)", status_code=200)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(None, alias="stripe-signature"),
) -> dict[str, str]:
    payload = await request.body()
    try:
        event = construct_event(payload, stripe_signature)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    try:
        await handle_event(event)
    except Exception as exc:
        logger.exception("stripe.webhook.handler_error", extra={"exc": str(exc)})
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "handler error") from exc

    return {"status": "ok"}
