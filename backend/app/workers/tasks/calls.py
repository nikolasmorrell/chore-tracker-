"""Celery tasks for post-call processing (summary, follow-up task creation)."""
from __future__ import annotations

from app.workers.celery_app import celery


@celery.task(name="calls.summarize")
def summarize_call(call_id: str) -> None:  # noqa: ARG001 pragma: no cover
    raise NotImplementedError("Wired in Phase 3")
