"""Stripe subscription routes."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, SessionDep, require_role
from app.core.config import get_settings
from app.db.models.tenant import Subscription, Tenant
from app.db.models.user import User
from app.schemas.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    PortalSessionResponse,
    SubscriptionRead,
    TenantBillingState,
)
from app.services import audit
from app.services import billing as billing_service

router = APIRouter()


def _price_for_plan(plan: str) -> str:
    settings = get_settings()
    mapping = {
        "starter": settings.stripe_price_starter,
        "pro": settings.stripe_price_pro,
        "enterprise": settings.stripe_price_enterprise,
    }
    price = mapping.get(plan, "")
    if not price:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"plan '{plan}' is not configured"
        )
    return price


@router.post(
    "/checkout-session",
    response_model=CheckoutSessionResponse,
    summary="Create a Stripe Checkout session",
)
async def create_checkout_session(
    payload: CheckoutSessionRequest,
    session: SessionDep,
    user: Annotated[User, Depends(require_role("owner", "admin"))],
) -> CheckoutSessionResponse:
    settings = get_settings()
    tenant = await session.scalar(select(Tenant).where(Tenant.id == user.tenant_id))
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "tenant not found")

    price_id = _price_for_plan(payload.plan)
    success = f"{settings.frontend_base_url}/billing?status=success"
    cancel = f"{settings.frontend_base_url}/billing?status=cancel"

    try:
        url = await billing_service.create_checkout_session(
            session,
            tenant=tenant,
            owner_email=user.email,
            price_id=price_id,
            success_url=success,
            cancel_url=cancel,
        )
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    await audit.record(
        session,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="billing.checkout_started",
        entity_type="tenant",
        entity_id=tenant.id,
        extra={"plan": payload.plan},
    )
    await session.commit()
    return CheckoutSessionResponse(url=url)


@router.post(
    "/portal-session",
    response_model=PortalSessionResponse,
    summary="Create a Stripe billing-portal session",
)
async def create_portal_session(
    session: SessionDep,
    user: Annotated[User, Depends(require_role("owner", "admin"))],
) -> PortalSessionResponse:
    settings = get_settings()
    tenant = await session.scalar(select(Tenant).where(Tenant.id == user.tenant_id))
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "tenant not found")
    if not tenant.stripe_customer_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "no Stripe customer yet — start a checkout first",
        )

    return_url = f"{settings.frontend_base_url}/billing"
    try:
        url = await billing_service.create_portal_session(
            customer_id=tenant.stripe_customer_id,
            return_url=return_url,
        )
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    return PortalSessionResponse(url=url)


@router.get(
    "/subscription",
    response_model=TenantBillingState,
    summary="Fetch this tenant's current subscription state",
)
async def get_subscription(
    session: SessionDep,
    user: CurrentUser,
) -> TenantBillingState:
    settings = get_settings()
    tenant = await session.scalar(select(Tenant).where(Tenant.id == user.tenant_id))
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "tenant not found")

    sub = await session.scalar(
        select(Subscription).where(Subscription.tenant_id == user.tenant_id)
    )
    return TenantBillingState(
        plan=tenant.plan,
        status=tenant.status,
        trial_ends_at=tenant.trial_ends_at,
        has_payment_method=bool(tenant.stripe_subscription_id),
        subscription=SubscriptionRead.model_validate(sub) if sub else None,
        publishable_key=settings.stripe_publishable_key,
    )
