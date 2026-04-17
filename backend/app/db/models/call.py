"""Call + CallTurn ORM models."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin, TimestampMixin, UUIDPKMixin


class Call(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "calls"
    __table_args__ = (UniqueConstraint("twilio_call_sid", name="uq_calls_twilio_sid"),)

    twilio_call_sid: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    from_number: Mapped[str] = mapped_column(String(40), nullable=False)
    to_number: Mapped[str] = mapped_column(String(40), nullable=False)
    direction: Mapped[str] = mapped_column(
        Enum("inbound", "outbound", name="call_direction"),
        nullable=False,
        default="inbound",
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="in_progress")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recording_url: Mapped[str | None] = mapped_column(String(500))
    summary: Mapped[str | None] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(80))
    transferred_to: Mapped[str | None] = mapped_column(String(80))

    turns: Mapped[list[CallTurn]] = relationship(
        back_populates="call", cascade="all, delete-orphan", order_by="CallTurn.turn_index"
    )


class CallTurn(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "call_turns"

    call_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    speaker: Mapped[str] = mapped_column(
        Enum("caller", "assistant", name="call_speaker"),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    audio_key: Mapped[str | None] = mapped_column(String(500))
    latency_ms: Mapped[int | None] = mapped_column(Integer)

    call: Mapped[Call] = relationship(back_populates="turns")
