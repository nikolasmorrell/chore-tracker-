"""Stripe wrapper: checkout sessions, customer portal, webhook event handlers.

All Stripe SDK calls live here so the API layer stays thin and testable. The
SDK is configured lazily off `get_settings()` so the app can boot without a
secret key (tests, local dev) — calls just fail loudly when they actually run.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.tenancy import set_current_tenant
from app.db.models.tenant import Tenant
from app.db.models.user import User
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


PLAN_BY_PRICE: dict[str, str] = {}


def _configure() -> None:
    """Configure the Stripe SDK + the price→plan map from settings."""
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise RuntimeError("STRIPE_SECRET_KEY not configured")
    stripe.api_key = settings.stripe_secret_key
    PLAN_BY_PRICE.clear()
    if settings.stripe_price_starter:
        PLAN_BY_PRICE[settings.stripe_price_starter] = "starter"
    if settings.stripe_price_pro:
        PLAN_BY_PRICE[settings.stripe_price_pro] = "pro"
    if settings.stripe_price_enterprise:
        PLAN_BY_PRICE[settings.stripe_price_enterprise] = "enterprise"


def _ensure_customer(tenant: Tenant, owner_email: str) -> str:
    """Get or create the Stripe customer for a tenant."""
    if tenant.stripe_customer_id:
        return tenant.stripe_customer_id
    customer = stripe.Customer.create(
        email=owner_email,
        name=tenant.name,
        metadata={"tenant_id": str(tenant.id), "tenant_slug": tenant.slug},
    )
    return str(customer.id)


async def create_checkout_session(
    session: AsyncSession,
    *,
    tenant: Tenant,
    owner_email: str,
    price_id: str,
    success_url: str,
    cancel_url: str,
) -> str:
    """Create a Checkout session and persist the Stripe customer id."""
    _configure()
    customer_id = _ensure_customer(tenant, owner_email)
    if tenant.stripe_customer_id != customer_id:
        tenant.stripe_customer_id = customer_id
        await session.flush()

    checkout = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(tenant.id),
        allow_promotion_codes=True,
        subscription_data={"metadata": {"tenant_id": str(tenant.id)}},
    )
    if not checkout.url:
        raise RuntimeError("Stripe returned a checkout session without a url")
    return str(checkout.url)


async def create_portal_session(
    *,
    customer_id: str,
    return_url: str,
) -> str:
    """Create a Stripe customer-portal session."""
    _configure()
    portal = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )
    return str(portal.url)


def construct_event(payload: bytes, signature: str | None) -> stripe.Event:
    """Verify Stripe webhook signature and parse the event."""
    settings = get_settings()
    if not settings.stripe_webhook_secret:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET not configured")
    if not signature:
        raise ValueError("missing Stripe-Signature header")
    result: stripe.Event = stripe.Webhook.construct_event(  # type: ignore[no-untyped-call]
        payload, signature, settings.stripe_webhook_secret
    )
    return result


def _ts_to_dt(ts: int | None) -> datetime | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=UTC)


def _plan_for_price(price_id: str | None) -> str:
    if price_id and price_id in PLAN_BY_PRICE:
        return PLAN_BY_PRICE[price_id]
    return "starter"


def _status_to_tenant_status(stripe_status: str) -> str:
    if stripe_status in {"active", "trialing"}:
        return "active"
    if stripe_status in {"past_due", "unpaid"}:
        return "past_due"
    if stripe_status in {"canceled", "incomplete_expired"}:
        return "canceled"
    return "suspended"


async def _tenant_for_subscription(
    session: AsyncSession, sub: dict[str, Any]
) -> Tenant | None:
    tenant_id_meta = (sub.get("metadata") or {}).get("tenant_id")
    if tenant_id_meta:
        try:
            tid = UUID(tenant_id_meta)
        except ValueError:
            tid = None
        if tid is not None:
            tenant: Tenant | None = await session.scalar(
                select(Tenant).where(Tenant.id == tid)
            )
            if tenant is not None:
                return tenant
    customer_id = sub.get("customer")
    if customer_id:
        found: Tenant | None = await session.scalar(
            select(Tenant).where(Tenant.stripe_customer_id == str(customer_id))
        )
        return found
    return None


async def apply_subscription(session: AsyncSession, sub: dict[str, Any]) -> None:
    """Sync a Stripe subscription payload onto Tenant + Subscription rows."""
    from app.db.models.tenant import Subscription  # local import: cycle-safe

    tenant = await _tenant_for_subscription(session, sub)
    if tenant is None:
        logger.warning("stripe.subscription_no_tenant_match", extra={"sub_id": sub.get("id")})
        return

    await set_current_tenant(session, tenant.id)

    items = (sub.get("items") or {}).get("data") or []
    price_id = (items[0].get("price") or {}).get("id") if items else None
    sub_id = str(sub["id"])
    status_str = str(sub.get("status") or "incomplete")

    tenant.stripe_subscription_id = sub_id
    tenant.plan = _plan_for_price(price_id)
    tenant.status = _status_to_tenant_status(status_str)

    existing: Subscription | None = await session.scalar(
        select(Subscription).where(Subscription.tenant_id == tenant.id)
    )
    period_end = _ts_to_dt(sub.get("current_period_end"))
    cancel_at_end = bool(sub.get("cancel_at_period_end"))
    if existing is None:
        session.add(
            Subscription(
                tenant_id=tenant.id,
                stripe_subscription_id=sub_id,
                price_id=price_id or "",
                status=status_str,
                current_period_end=period_end,
                cancel_at_period_end=cancel_at_end,
            )
        )
    else:
        existing.stripe_subscription_id = sub_id
        existing.price_id = price_id or existing.price_id
        existing.status = status_str
        existing.current_period_end = period_end
        existing.cancel_at_period_end = cancel_at_end

    await session.flush()


async def cancel_subscription(session: AsyncSession, sub: dict[str, Any]) -> None:
    """Mark a tenant as canceled when Stripe deletes their subscription."""
    tenant = await _tenant_for_subscription(session, sub)
    if tenant is None:
        return
    await set_current_tenant(session, tenant.id)
    tenant.status = "canceled"
    tenant.plan = "trial"
    await session.flush()


async def handle_event(event: stripe.Event | dict[str, Any]) -> None:
    """Dispatch a verified Stripe event to its tenant-mutating handler."""
    raw: Any = event
    event_dict: dict[str, Any] = dict(raw) if not isinstance(event, dict) else event
    event_type = event_dict.get("type")
    data: dict[str, Any] = (event_dict.get("data") or {}).get("object") or {}

    async with SessionLocal() as session:
        try:
            if event_type in {
                "customer.subscription.created",
                "customer.subscription.updated",
                "checkout.session.completed",
            }:
                if event_type == "checkout.session.completed":
                    sub_id = data.get("subscription")
                    if not sub_id:
                        return
                    _configure()
                    raw_sub: Any = stripe.Subscription.retrieve(str(sub_id))
                    sub_payload: dict[str, Any] = dict(raw_sub)
                else:
                    sub_payload = data
                await apply_subscription(session, sub_payload)
            elif event_type == "customer.subscription.deleted":
                await cancel_subscription(session, data)
            else:
                logger.info("stripe.event.ignored", extra={"event_type": event_type})
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def find_owner_email(session: AsyncSession, tenant_id: UUID) -> str | None:
    user: User | None = await session.scalar(
        select(User).where(User.tenant_id == tenant_id, User.role == "owner")
    )
    return user.email if user else None
