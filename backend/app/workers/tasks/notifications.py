"""Celery tasks for outbound email + SMS."""
from __future__ import annotations

from app.workers.celery_app import celery


@celery.task(name="notifications.send_email")
def send_email_task(to: str, subject: str, html: str) -> None:  # noqa: ARG001 pragma: no cover
    raise NotImplementedError("Wired in Phase 2")


@celery.task(name="notifications.send_sms")
def send_sms_task(to: str, body: str) -> None:  # noqa: ARG001 pragma: no cover
    raise NotImplementedError("Wired in Phase 2")
