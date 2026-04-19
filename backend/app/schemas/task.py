"""Task DTOs."""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

TaskSource = Literal["document", "call", "manual", "alert"]
TaskPriority = Literal["low", "normal", "high", "urgent"]
TaskStatus = Literal["open", "in_progress", "done", "cancelled"]


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    due_at: datetime | None = None
    priority: TaskPriority = "normal"
    assigned_to: UUID | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    due_at: datetime | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    assigned_to: UUID | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    title: str
    description: str | None
    source: TaskSource
    source_id: UUID | None
    assigned_to: UUID | None
    due_at: datetime | None
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
