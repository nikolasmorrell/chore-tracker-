"""Celery tasks for post-call processing.

`calls.summarize` runs Claude over the transcript, writes the summary +
intent back to the Call row, and materializes any action_items as open Tasks.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.core.security import utcnow
from app.core.tenancy import set_current_tenant
from app.db.models.call import Call, CallTurn
from app.db.models.task import Task
from app.db.session import SessionLocal
from app.services.claude_client import ClaudeClient, render_prompt
from app.workers.celery_app import celery

logger = logging.getLogger(__name__)


def _parse_summary(text: str) -> dict[str, Any]:
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
        logger.warning("calls.summary_not_json", extra={"snippet": cleaned[:120]})
        return {"summary": cleaned[:500], "intent": "other", "action_items": []}


async def _summarize(call_id: UUID) -> None:
    async with SessionLocal() as session:
        call = await session.scalar(select(Call).where(Call.id == call_id))
        if call is None:
            logger.warning("calls.summarize.missing", extra={"call_id": str(call_id)})
            return
        await set_current_tenant(session, call.tenant_id)

        turns = (
            await session.scalars(
                select(CallTurn)
                .where(CallTurn.call_id == call.id)
                .order_by(CallTurn.turn_index)
            )
        ).all()
        if not turns:
            return

        prompt = render_prompt(
            "call_summary.j2",
            turns=[{"speaker": t.speaker, "text": t.text} for t in turns],
        )
        client = ClaudeClient()
        response = await client.complete(prompt)
        parsed = _parse_summary(response.text)

        call.summary = str(parsed.get("summary") or "")[:4000] or call.summary
        if parsed.get("intent"):
            call.intent = str(parsed["intent"])[:80]

        now = utcnow()
        for item in parsed.get("action_items") or []:
            title = str(item.get("title") or "").strip()
            if not title:
                continue
            priority = str(item.get("priority") or "normal")
            if priority not in {"low", "normal", "high", "urgent"}:
                priority = "normal"
            task = Task(
                tenant_id=call.tenant_id,
                title=title[:200],
                source="call",
                source_id=call.id,
                priority=priority,
                status="open",
            )
            due_in = item.get("due_in_hours")
            if isinstance(due_in, int | float):
                from datetime import timedelta

                task.due_at = now + timedelta(hours=float(due_in))
            session.add(task)

        await session.commit()


@celery.task(name="calls.summarize")
def summarize_call(call_id: str) -> None:
    asyncio.run(_summarize(UUID(call_id)))
