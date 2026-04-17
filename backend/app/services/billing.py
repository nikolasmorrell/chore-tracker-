"""Stripe wrapper (checkout, portal, webhook handlers)."""
from __future__ import annotations


async def create_checkout_session(tenant_id: str, price_id: str) -> str:  # pragma: no cover
    raise NotImplementedError("Billing implemented in Phase 5")
