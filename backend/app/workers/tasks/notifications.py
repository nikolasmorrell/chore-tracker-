"""Celery tasks for outbound email + SMS."""
from __future__ import annotations

import asyncio

from app.services.notifications import send_email, send_sms
from app.workers.celery_app import celery


@celery.task(name="notifications.send_email")
def send_email_task(to: str, subject: str, html: str) -> None:
    asyncio.run(send_email(to, subject, html))


@celery.task(name="notifications.send_sms")
def send_sms_task(to: str, body: str) -> None:
    asyncio.run(send_sms(to, body))
