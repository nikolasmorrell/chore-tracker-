"""SendGrid email + Twilio SMS senders."""
from __future__ import annotations


async def send_email(to: str, subject: str, html: str) -> None:  # pragma: no cover
    raise NotImplementedError("Email implemented in Phase 2")


async def send_sms(to: str, body: str) -> None:  # pragma: no cover
    raise NotImplementedError("SMS implemented in Phase 2")
