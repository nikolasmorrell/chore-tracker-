"""Voice-assistant orchestrator (Twilio + Deepgram + Claude)."""
from __future__ import annotations


async def handle_turn(call_sid: str, caller_text: str) -> str:  # pragma: no cover
    raise NotImplementedError("Voice loop implemented in Phase 3")
