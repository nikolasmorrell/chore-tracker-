"""Call + transcript DTOs."""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

CallSpeaker = Literal["caller", "assistant"]
CallDirection = Literal["inbound", "outbound"]


class CallTurnRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    turn_index: int
    speaker: CallSpeaker
    text: str
    latency_ms: int | None = None
    created_at: datetime


class CallRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    twilio_call_sid: str
    from_number: str
    to_number: str
    direction: CallDirection
    status: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    summary: str | None = None
    intent: str | None = None
    transferred_to: str | None = None


class CallDetail(CallRead):
    turns: list[CallTurnRead] = []
