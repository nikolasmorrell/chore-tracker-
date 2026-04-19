"""Unit tests for billing service helpers (no DB, no Stripe network calls)."""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import UTC
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.billing import (
    PLAN_BY_PRICE,
    _plan_for_price,
    _status_to_tenant_status,
    _ts_to_dt,
)

# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def test_plan_for_price_known() -> None:
    PLAN_BY_PRICE["price_starter_test"] = "starter"
    assert _plan_for_price("price_starter_test") == "starter"
    del PLAN_BY_PRICE["price_starter_test"]


def test_plan_for_price_unknown_defaults_starter() -> None:
    assert _plan_for_price("price_does_not_exist") == "starter"


def test_plan_for_price_none() -> None:
    assert _plan_for_price(None) == "starter"  # type: ignore[arg-type]


def test_status_to_tenant_status_active() -> None:
    assert _status_to_tenant_status("active") == "active"
    assert _status_to_tenant_status("trialing") == "active"


def test_status_to_tenant_status_past_due() -> None:
    assert _status_to_tenant_status("past_due") == "past_due"
    assert _status_to_tenant_status("unpaid") == "past_due"


def test_status_to_tenant_status_canceled() -> None:
    assert _status_to_tenant_status("canceled") == "canceled"
    assert _status_to_tenant_status("incomplete_expired") == "canceled"


def test_status_to_tenant_status_unknown() -> None:
    assert _status_to_tenant_status("incomplete") == "suspended"


def test_ts_to_dt_none() -> None:
    assert _ts_to_dt(None) is None


def test_ts_to_dt_epoch() -> None:

    dt = _ts_to_dt(0)
    assert dt is not None
    assert dt.year == 1970
    assert dt.tzinfo == UTC


# ---------------------------------------------------------------------------
# construct_event: signature verification
# ---------------------------------------------------------------------------


def _make_stripe_signature(secret: str, payload: bytes, timestamp: int) -> str:
    signed = f"{timestamp}.{payload.decode()}".encode()
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={sig}"


def test_construct_event_valid() -> None:
    import stripe

    secret = "whsec_test_secret"
    payload = json.dumps({"type": "ping", "object": "event", "data": {"object": {}}}).encode()
    ts = int(time.time())
    sig = _make_stripe_signature(secret, payload, ts)

    with patch("app.services.billing.get_settings") as mock_settings:
        mock_settings.return_value.stripe_webhook_secret = secret
        event = stripe.Webhook.construct_event(payload, sig, secret)
    assert event["type"] == "ping"


def test_construct_event_no_secret() -> None:
    from app.services.billing import construct_event

    with patch("app.services.billing.get_settings") as mock_settings:
        mock_settings.return_value.stripe_webhook_secret = ""
        with pytest.raises(RuntimeError, match="STRIPE_WEBHOOK_SECRET"):
            construct_event(b"{}", "t=1,v1=abc")


def test_construct_event_no_signature() -> None:
    from app.services.billing import construct_event

    with patch("app.services.billing.get_settings") as mock_settings:
        mock_settings.return_value.stripe_webhook_secret = "whsec_something"
        with pytest.raises(ValueError, match="missing"):
            construct_event(b"{}", None)


# ---------------------------------------------------------------------------
# handle_event dispatch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_event_ignored_type() -> None:
    """Unknown event types are silently skipped (no DB write)."""
    from app.services.billing import handle_event

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.commit = AsyncMock()

    with patch("app.services.billing.SessionLocal", return_value=mock_session):
        await handle_event({"type": "payment_intent.created", "data": {"object": {}}})

    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_event_subscription_deleted() -> None:
    """Deleted subscriptions call cancel_subscription."""
    from app.services.billing import handle_event

    tid = uuid4()
    sub_payload: dict[str, Any] = {
        "id": "sub_test",
        "metadata": {"tenant_id": str(tid)},
        "customer": "cus_test",
    }

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.commit = AsyncMock()

    tenant_mock = MagicMock()
    tenant_mock.id = tid
    mock_session.scalar = AsyncMock(return_value=tenant_mock)

    with (
        patch("app.services.billing.SessionLocal", return_value=mock_session),
        patch("app.services.billing.set_current_tenant", new_callable=AsyncMock),
    ):
        await handle_event(
            {"type": "customer.subscription.deleted", "data": {"object": sub_payload}}
        )

    assert tenant_mock.status == "canceled"
    assert tenant_mock.plan == "trial"
    mock_session.commit.assert_awaited_once()
