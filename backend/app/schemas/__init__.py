"""Pydantic DTOs exposed by the API.

Schemas mirror the DB models but expose only fields safe for API callers.
Prefer composing `Read`-shaped schemas for responses and explicit `Create`/
`Update` schemas for request bodies so OpenAPI stays accurate.
"""
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenPair,
    TokenResponse,
)
from app.schemas.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    PortalSessionResponse,
    SubscriptionRead,
    TenantBillingState,
)
from app.schemas.call import CallDetail, CallRead, CallTurnRead
from app.schemas.common import CursorPage, Message
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from app.schemas.document import (
    AlertRead,
    DocumentExtractionRead,
    DocumentRead,
    DocumentUploadRequest,
    DocumentUploadResponse,
)
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.schemas.tenant import TenantRead, TenantUpdate
from app.schemas.user import InviteCreate, InviteRead, UserRead, UserUpdate

__all__ = [
    "AlertRead",
    "CallDetail",
    "CallRead",
    "CallTurnRead",
    "CheckoutSessionRequest",
    "CheckoutSessionResponse",
    "CursorPage",
    "CustomerCreate",
    "CustomerRead",
    "CustomerUpdate",
    "DocumentExtractionRead",
    "DocumentRead",
    "DocumentUploadRequest",
    "DocumentUploadResponse",
    "ForgotPasswordRequest",
    "InviteCreate",
    "InviteRead",
    "LoginRequest",
    "Message",
    "PortalSessionResponse",
    "ResetPasswordRequest",
    "SignupRequest",
    "SubscriptionRead",
    "TaskCreate",
    "TaskRead",
    "TaskUpdate",
    "TenantBillingState",
    "TenantRead",
    "TenantUpdate",
    "TokenPair",
    "TokenResponse",
    "UserRead",
    "UserUpdate",
]
