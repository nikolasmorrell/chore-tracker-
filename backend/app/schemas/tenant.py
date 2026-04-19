"""Tenant-level DTOs."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TenantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    plan: str
    status: str
    trial_ends_at: datetime | None
    twilio_phone_number: str | None = None
    created_at: datetime


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    twilio_phone_number: str | None = Field(default=None, max_length=40)
