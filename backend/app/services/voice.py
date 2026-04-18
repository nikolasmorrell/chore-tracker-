"""Voice-assistant orchestrator.

Twilio posts inbound calls to `/webhooks/twilio/voice`. We respond with TwiML
that collects speech via `<Gather>`, forwards each utterance to
`/webhooks/twilio/voice/turn`, runs it through Claude, and replies with `<Say>`
plus the next `<Gather>`. When Twilio posts the status callback with
`CallStatus=completed`, we enqueue a summarize task.
"""
from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import utcnow
from app.core.tenancy import set_current_tenant
from app.db.models.call import Call, CallTurn
from app.db.models.tenant import Tenant
from app.services.claude_client import ClaudeClient, render_prompt

logger = logging.getLogger(__name__)


async def resolve_tenant_by_to_number(session: AsyncSession, to_number: str) -> Tenant | None:
    normalized = to_number.strip()
    tenant: Tenant | None = await session.scalar(
        select(Tenant).where(Tenant.twilio_phone_number == normalized)
    )
    return tenant


async def get_or_create_call(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    call_sid: str,
    from_number: str,
    to_number: str,
) -> Call:
    call = await session.scalar(select(Call).where(Call.twilio_call_sid == call_sid))
    if call is not None:
        return call
    call = Call(
        tenant_id=tenant_id,
        twilio_call_sid=call_sid,
        from_number=from_number,
        to_number=to_number,
        direction="inbound",
        status="in_progress",
        started_at=utcnow(),
    )
    session.add(call)
    await session.flush()
    return call


async def _next_turn_index(session: AsyncSession, call_id: UUID) -> int:
    current: int | None = await session.scalar(
        select(func.max(CallTurn.turn_index)).where(CallTurn.call_id == call_id)
    )
    return (current or 0) + 1


async def record_turn(
    session: AsyncSession,
    *,
    call: Call,
    speaker: str,
    text: str,
    latency_ms: int | None = None,
) -> CallTurn:
    idx = await _next_turn_index(session, call.id)
    turn = CallTurn(
        tenant_id=call.tenant_id,
        call_id=call.id,
        turn_index=idx,
        speaker=speaker,
        text=text,
        latency_ms=latency_ms,
    )
    session.add(turn)
    await session.flush()
    return turn


async def _conversation(session: AsyncSession, call_id: UUID) -> list[CallTurn]:
    rows = await session.scalars(
        select(CallTurn)
        .where(CallTurn.call_id == call_id)
        .order_by(CallTurn.turn_index)
    )
    return list(rows.all())


def _parse_reply(text: str) -> dict[str, Any]:
    """Call_reply prompt returns JSON; be liberal with fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if "\n" in cleaned:
            head, _, rest = cleaned.partition("\n")
            if head.strip().lower() in {"json", ""}:
                cleaned = rest
    try:
        return dict(json.loads(cleaned))
    except json.JSONDecodeError:
        logger.warning("voice.reply_not_json", extra={"snippet": cleaned[:120]})
        return {"reply_text": "Sorry, could you repeat that?", "intent": "other", "transfer": False, "end_call": False}


async def handle_turn(
    session: AsyncSession,
    *,
    call: Call,
    tenant: Tenant,
    caller_text: str,
) -> dict[str, Any]:
    """Runs one turn: persists caller text, calls Claude, persists assistant text, returns decision."""
    await set_current_tenant(session, tenant.id)
    await record_turn(session, call=call, speaker="caller", text=caller_text)

    prior = await _conversation(session, call.id)
    # Drop the last turn (the caller utterance we just wrote) since the prompt
    # lists it separately.
    history = prior[:-1] if prior else []

    prompt = render_prompt(
        "call_reply.j2",
        tenant={"name": tenant.name},
        turns=[{"speaker": t.speaker, "text": t.text} for t in history],
        latest_utterance=caller_text,
    )
    client = ClaudeClient()
    response = await client.complete(prompt)
    decision = _parse_reply(response.text)

    reply_text = str(decision.get("reply_text") or "One moment, please.").strip()
    await record_turn(session, call=call, speaker="assistant", text=reply_text)

    if decision.get("intent"):
        call.intent = str(decision["intent"])[:80]

    return {
        "reply_text": reply_text,
        "transfer": bool(decision.get("transfer")),
        "end_call": bool(decision.get("end_call")),
        "intent": call.intent,
    }


async def finalize_call(session: AsyncSession, *, call: Call, status: str) -> None:
    call.status = status
    if status in {"completed", "failed", "no-answer", "busy", "canceled"}:
        call.ended_at = utcnow()
