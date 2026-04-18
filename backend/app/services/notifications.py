"""Email + SMS senders (SendGrid + Twilio).

Both senders short-circuit when credentials are unset so local/dev/tests can
run without reaching out. Production configures real keys.
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, html: str, text: str | None = None) -> None:
    settings = get_settings()
    if not settings.sendgrid_api_key:
        logger.info("email.skip", extra={"to": to, "subject": subject})
        return

    # Import lazily so tests / dev don't need the SendGrid SDK installed.
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    message = Mail(
        from_email=(settings.email_from_address, settings.email_from_name),
        to_emails=to,
        subject=subject,
        html_content=html,
        plain_text_content=text or "",
    )
    client = SendGridAPIClient(settings.sendgrid_api_key)
    # SendGrid SDK is sync — run in thread to avoid blocking the loop.
    import anyio

    await anyio.to_thread.run_sync(client.send, message)


async def send_sms(to: str, body: str) -> None:
    settings = get_settings()
    if not (settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_phone_number):
        logger.info("sms.skip", extra={"to": to, "body": body[:80]})
        return

    from twilio.rest import Client

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

    def _send() -> Any:
        return client.messages.create(to=to, from_=settings.twilio_phone_number, body=body)

    import anyio

    await anyio.to_thread.run_sync(_send)
