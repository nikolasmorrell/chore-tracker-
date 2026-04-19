"""Tenant + Subscription ORM models."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class TenantPlan(str):
    TRIAL = "trial"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class TenantStatus(str):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    SUSPENDED = "suspended"


class Tenant(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    plan: Mapped[str] = mapped_column(
        Enum("trial", "starter", "pro", "enterprise", name="tenant_plan"),
        nullable=False,
        default="trial",
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "past_due", "canceled", "suspended", name="tenant_status"),
        nullable=False,
        default="active",
    )
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stripe_customer_id: Mapped[str | None] = mapped_column(String(120), unique=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(120), unique=True)
    twilio_phone_number: Mapped[str | None] = mapped_column(String(40), unique=True)

    users: Mapped[list[User]] = relationship(back_populates="tenant", cascade="all, delete-orphan")


class Subscription(UUIDPKMixin, TimestampMixin, Base):
    """Denormalized copy of Stripe subscription state for dashboard reads."""

    __tablename__ = "subscriptions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    stripe_subscription_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    price_id: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
