"""v1 API router aggregator."""
from fastapi import APIRouter

from app.api.v1 import (
    admin,
    alerts,
    auth,
    billing,
    calls,
    customers,
    documents,
    tasks,
    tenants,
    users,
)
from app.api.v1.webhooks import stripe as stripe_webhooks
from app.api.v1.webhooks import twilio as twilio_webhooks

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(calls.router, prefix="/calls", tags=["calls"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(stripe_webhooks.router, prefix="/webhooks/stripe", tags=["webhooks"])
api_router.include_router(twilio_webhooks.router, prefix="/webhooks/twilio", tags=["webhooks"])
