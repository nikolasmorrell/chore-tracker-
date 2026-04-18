"""Twilio Voice + SMS webhook endpoints.

Flow:
  1. Twilio POSTs to `/voice` — we create a Call row, return TwiML with a
     greeting and a `<Gather input="speech">` pointing at `/voice/turn`.
  2. Twilio transcribes the utterance and POSTs it to `/voice/turn` with
     `SpeechResult`. We run Claude and return more TwiML: `<Say>` + next
     `<Gather>` (or `<Hangup>`/`<Dial>` if the model decided to end/transfer).
  3. When the call ends Twilio POSTs to `/voice/status`; we finalize the row
     and enqueue a summary task.

SMS: `/sms` persists the message as an audit record for now; auto-reply is
out of scope for Phase 3.
"""
from __future__ import annotations

import logging
from xml.sax.saxutils import escape

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.deps import SessionDep
from app.services import voice as voice_service
from app.services.twilio_verify import verify_twilio_request
from app.workers.tasks.calls import summarize_call

logger = logging.getLogger(__name__)
router = APIRouter()


def _twiml(body: str) -> Response:
    xml = f'<?xml version="1.0" encoding="UTF-8"?><Response>{body}</Response>'
    return Response(content=xml, media_type="application/xml")


def _say(text: str) -> str:
    return f"<Say>{escape(text)}</Say>"


def _gather(action: str, prompt: str | None = None) -> str:
    inner = _say(prompt) if prompt else ""
    return (
        f'<Gather input="speech" action="{escape(action)}" method="POST" '
        f'speechTimeout="auto" speechModel="phone_call">{inner}</Gather>'
    )


@router.post("/voice", summary="Inbound voice call → returns TwiML")
async def voice_webhook(request: Request, session: SessionDep) -> Response:
    params = await verify_twilio_request(request)
    call_sid = params.get("CallSid", "")
    from_number = params.get("From", "")
    to_number = params.get("To", "")
    if not call_sid or not to_number:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "missing call identifiers")

    tenant = await voice_service.resolve_tenant_by_to_number(session, to_number)
    if tenant is None:
        logger.warning("voice.unknown_tenant", extra={"to": to_number})
        return _twiml(_say("This number is not currently configured. Goodbye.") + "<Hangup/>")

    await voice_service.get_or_create_call(
        session,
        tenant_id=tenant.id,
        call_sid=call_sid,
        from_number=from_number,
        to_number=to_number,
    )
    await session.commit()

    greeting = f"Thanks for calling {tenant.name}. How can I help you today?"
    body = _gather(action="/api/v1/webhooks/twilio/voice/turn", prompt=greeting)
    # Redirect to self if the caller says nothing — don't just hang up on a pause.
    body += '<Redirect method="POST">/api/v1/webhooks/twilio/voice/turn</Redirect>'
    return _twiml(body)


@router.post("/voice/turn", summary="Handle one speech turn")
async def voice_turn(request: Request, session: SessionDep) -> Response:
    params = await verify_twilio_request(request)
    call_sid = params.get("CallSid", "")
    speech = (params.get("SpeechResult") or "").strip()
    to_number = params.get("To", "")

    if not call_sid:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "missing CallSid")

    # If the caller said nothing, reprompt gently.
    if not speech:
        body = _gather(
            action="/api/v1/webhooks/twilio/voice/turn",
            prompt="Sorry, I didn't catch that. Could you repeat?",
        )
        body += "<Hangup/>"
        return _twiml(body)

    from sqlalchemy import select

    from app.db.models.call import Call
    from app.db.models.tenant import Tenant

    call = await session.scalar(select(Call).where(Call.twilio_call_sid == call_sid))
    if call is None:
        tenant = await voice_service.resolve_tenant_by_to_number(session, to_number)
        if tenant is None:
            return _twiml(_say("Sorry, something went wrong.") + "<Hangup/>")
        call = await voice_service.get_or_create_call(
            session,
            tenant_id=tenant.id,
            call_sid=call_sid,
            from_number=params.get("From", ""),
            to_number=to_number,
        )
    else:
        tenant = await session.scalar(select(Tenant).where(Tenant.id == call.tenant_id))

    if tenant is None:
        return _twiml(_say("Sorry, something went wrong.") + "<Hangup/>")

    decision = await voice_service.handle_turn(
        session, call=call, tenant=tenant, caller_text=speech
    )
    await session.commit()

    reply_twiml = _say(decision["reply_text"])
    if decision.get("transfer"):
        transfer_to = (tenant.twilio_phone_number or "").strip()
        # For now, just say we're transferring and hang up; real transfer
        # numbers are a tenant-level setting we'll add in Phase 5.
        if transfer_to:
            reply_twiml += f"<Dial>{escape(transfer_to)}</Dial>"
        else:
            reply_twiml += _say("I'll have someone reach out shortly.")
        return _twiml(reply_twiml + "<Hangup/>")
    if decision.get("end_call"):
        return _twiml(reply_twiml + "<Hangup/>")

    reply_twiml += _gather(action="/api/v1/webhooks/twilio/voice/turn")
    reply_twiml += "<Hangup/>"
    return _twiml(reply_twiml)


@router.post("/voice/status", summary="Voice call status callback")
async def voice_status(request: Request, session: SessionDep) -> Response:
    params = await verify_twilio_request(request)
    call_sid = params.get("CallSid", "")
    status_value = params.get("CallStatus", "completed")

    from sqlalchemy import select

    from app.db.models.call import Call

    call = await session.scalar(select(Call).where(Call.twilio_call_sid == call_sid))
    if call is not None:
        await voice_service.finalize_call(session, call=call, status=status_value)
        await session.commit()
        if status_value == "completed":
            summarize_call.delay(str(call.id))
    return Response(status_code=204)


@router.post("/sms", summary="Inbound SMS")
async def sms_webhook(request: Request) -> Response:
    # Acknowledge only — tenant-routed SMS replies come in Phase 4.
    await verify_twilio_request(request)
    return _twiml("")
