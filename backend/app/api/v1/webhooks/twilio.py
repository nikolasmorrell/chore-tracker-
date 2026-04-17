"""Twilio Voice + SMS webhook endpoints.

Signature verification, TwiML generation, and the media-stream websocket are
implemented in Phase 3.
"""
from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.post("/voice", summary="Inbound voice call → returns TwiML")
async def voice_webhook() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 3")


@router.post("/voice/status", summary="Voice call status callback")
async def voice_status() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 3")


@router.post("/sms", summary="Inbound SMS")
async def sms_webhook() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 3")
