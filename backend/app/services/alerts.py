"""Alert rule engine.

For each extraction we drop old scheduled alerts for the document, then:
  - schedule 30/14/7/0-day expiration alerts off `expiration_date`
  - schedule a single missing-field alert if the extraction flagged any gaps

Sending happens in `app.workers.tasks.alerts.dispatch_due_alerts` which polls
`alerts.due_at <= now` and hands off to the notification service.
"""
from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import cast

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import utcnow
from app.db.models.document import Alert, Document, DocumentExtraction

# (kind, days_before_expiration)
EXPIRATION_WINDOWS: tuple[tuple[str, int], ...] = (
    ("expiring_30", 30),
    ("expiring_14", 14),
    ("expiring_7", 7),
    ("expiring_0", 0),
)


def _parse_expiration(value: object) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return None
    return None


async def schedule_alerts_for_extraction(
    session: AsyncSession,
    *,
    document: Document,
    extraction: DocumentExtraction,
) -> list[Alert]:
    # Wipe any still-pending alerts for this document so we re-schedule from
    # the latest extraction without dupes.
    await session.execute(
        delete(Alert).where(
            Alert.document_id == document.id,
            Alert.status == "scheduled",
        )
    )

    structured = extraction.structured or {}
    expiration = _parse_expiration(structured.get("expiration_date"))
    missing_fields = cast(list[str], structured.get("missing_fields") or [])
    missing_signatures = cast(list[str], structured.get("missing_signatures") or [])

    now = utcnow()
    created: list[Alert] = []

    if expiration is not None:
        expiration_at = datetime.combine(expiration, time.min, tzinfo=UTC)
        for kind, days in EXPIRATION_WINDOWS:
            due_at = expiration_at - timedelta(days=days)
            if due_at < now - timedelta(days=1):
                # Already past — skip so we don't blast yesterday's reminders.
                continue
            alert = Alert(
                tenant_id=document.tenant_id,
                document_id=document.id,
                kind=kind,
                due_at=due_at,
                status="scheduled",
                channel="email",
            )
            session.add(alert)
            created.append(alert)

    if missing_fields or missing_signatures:
        alert = Alert(
            tenant_id=document.tenant_id,
            document_id=document.id,
            kind="missing_field",
            due_at=now,
            status="scheduled",
            channel="email",
        )
        session.add(alert)
        created.append(alert)

    await session.flush()
    return created


async def claim_due_alerts(session: AsyncSession, *, limit: int = 100) -> list[Alert]:
    """Atomically grab a batch of due alerts and mark them 'sent'.

    Returns the rows so the caller can dispatch them. We flip status first so
    a crash between claim and dispatch never double-sends; callers treat
    dispatch failures as retry-worthy, not as re-claim.
    """
    now = utcnow()
    stmt = (
        select(Alert)
        .where(Alert.status == "scheduled", Alert.due_at <= now)
        .order_by(Alert.due_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    result = await session.scalars(stmt)
    rows = list(result.all())
    if not rows:
        return rows
    ids = [r.id for r in rows]
    await session.execute(
        update(Alert)
        .where(Alert.id.in_(ids))
        .values(status="sent", sent_at=now)
    )
    return rows
