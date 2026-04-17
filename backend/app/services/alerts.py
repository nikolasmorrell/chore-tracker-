"""Alert rule engine.

Schedules 30/14/7/0-day expiration alerts plus missing-field alerts when a
document extraction lands. Implemented in Phase 2.
"""
from __future__ import annotations

from uuid import UUID


async def schedule_expiration_alerts(document_id: UUID) -> None:  # pragma: no cover
    raise NotImplementedError("Alert scheduling implemented in Phase 2")
