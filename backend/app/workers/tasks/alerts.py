"""Celery tasks for alert scheduling + delivery."""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.core.tenancy import set_current_tenant
from app.db.models.document import Alert, Document
from app.db.models.user import User
from app.db.session import SessionLocal
from app.services.alerts import claim_due_alerts
from app.services.notifications import send_email, send_sms
from app.workers.celery_app import celery

logger = logging.getLogger(__name__)


def _message_for(alert: Alert, document: Document | None) -> tuple[str, str]:
    filename = document.original_filename if document else "a document"
    if alert.kind == "missing_field":
        return (
            "Action needed: missing fields on a document",
            f"We detected missing fields on {filename}. Please open Sellable to review.",
        )
    days_map = {
        "expiring_30": 30,
        "expiring_14": 14,
        "expiring_7": 7,
        "expiring_0": 0,
    }
    days = days_map.get(alert.kind, 0)
    when = "today" if days == 0 else f"in {days} days"
    return (
        f"Document expiring {when}: {filename}",
        f"{filename} expires {when}. Open Sellable to renew.",
    )


async def _dispatch() -> int:
    async with SessionLocal() as session:
        alerts = await claim_due_alerts(session, limit=100)
        if not alerts:
            await session.commit()
            return 0

        for alert in alerts:
            await set_current_tenant(session, alert.tenant_id)
            document = None
            if alert.document_id is not None:
                document = await session.scalar(
                    select(Document).where(Document.id == alert.document_id)
                )
            # Fan out to every admin/owner in the tenant as MVP; fine-grained
            # routing (e.g. per-customer recipients) lands in Phase 4.
            recipients = (
                await session.scalars(
                    select(User).where(
                        User.role.in_(("owner", "admin")),
                        User.is_active.is_(True),
                    )
                )
            ).all()

            subject, body = _message_for(alert, document)
            for user in recipients:
                try:
                    if alert.channel == "sms" and user.email:
                        await send_sms(to=user.email, body=body)
                    else:
                        await send_email(to=user.email, subject=subject, html=f"<p>{body}</p>", text=body)
                except Exception:
                    logger.exception("alert.dispatch_failed", extra={"alert_id": str(alert.id)})

        await session.commit()
        return len(alerts)


@celery.task(name="alerts.dispatch_due")
def dispatch_due_alerts() -> int:
    return asyncio.run(_dispatch())
