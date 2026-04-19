"""Billing-related DTOs."""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CheckoutSessionRequest(BaseModel):
    plan: Literal["starter", "pro", "enterprise"]


class CheckoutSessionResponse(BaseModel):
    url: str


class PortalSessionResponse(BaseModel):
    url: str


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    stripe_subscription_id: str
    price_id: str
    status: str
    current_period_end: datetime | None
    cancel_at_period_end: bool


class TenantBillingState(BaseModel):
    """Combined view a frontend needs to render the billing page."""

    plan: str
    status: str
    trial_ends_at: datetime | None
    has_payment_method: bool = Field(
        description="True once Stripe has a customer + an active subscription."
    )
    subscription: SubscriptionRead | None = None
    publishable_key: str
