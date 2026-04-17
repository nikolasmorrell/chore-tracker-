"""Internal task ORM model."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin, TimestampMixin, UUIDPKMixin


class Task(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(
        Enum("document", "call", "manual", "alert", name="task_source"),
        nullable=False,
        default="manual",
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    priority: Mapped[str] = mapped_column(
        Enum("low", "normal", "high", "urgent", name="task_priority"),
        nullable=False,
        default="normal",
    )
    status: Mapped[str] = mapped_column(
        Enum("open", "in_progress", "done", "cancelled", name="task_status"),
        nullable=False,
        default="open",
    )
