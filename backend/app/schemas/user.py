"""User + Invite DTOs."""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["owner", "admin", "staff"]


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    email: EmailStr
    full_name: str
    role: Role
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    role: Role | None = None
    is_active: bool | None = None


class InviteCreate(BaseModel):
    email: EmailStr
    role: Role = "staff"


class InviteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    role: Role
    expires_at: datetime
    accepted_at: datetime | None
    created_at: datetime
