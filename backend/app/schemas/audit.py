"""AuditLog DTO."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    actor_user_id: UUID | None
    action: str
    entity_type: str
    entity_id: UUID | None
    extra: dict[str, Any]
    ip: str | None
    created_at: datetime
