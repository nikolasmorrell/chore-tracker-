"""Auth routes: signup, login, refresh, logout, password reset."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Cookie, HTTPException, Response, status

from app.api.deps import SessionDep
from app.core.config import get_settings
from app.core.cookies import REFRESH_COOKIE, clear_auth_cookies, set_auth_cookies
from app.core.security import decode_token
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
)
from app.schemas.common import Message
from app.services import audit
from app.services import auth as auth_service
from app.services.notifications import send_email
from app.services.onboarding import create_tenant_with_owner

router = APIRouter()


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create tenant + owner account and start trial",
)
async def signup(payload: SignupRequest, session: SessionDep, response: Response) -> TokenResponse:
    tenant, user = await create_tenant_with_owner(
        session,
        company_name=payload.company_name,
        full_name=payload.full_name,
        email=payload.email,
        password=payload.password,
    )
    await audit.record(
        session,
        tenant_id=tenant.id,
        actor_user_id=user.id,
        action="tenant.signup",
        entity_type="tenant",
        entity_id=tenant.id,
    )
    await session.commit()

    access, refresh, expires_in = auth_service.issue_tokens(user)
    set_auth_cookies(response, access_token=access, refresh_token=refresh)
    return TokenResponse(access_token=access, expires_in=expires_in)


@router.post("/login", response_model=TokenResponse, summary="Email + password login")
async def login(payload: LoginRequest, session: SessionDep, response: Response) -> TokenResponse:
    try:
        user = await auth_service.authenticate(session, payload.email, payload.password)
    except auth_service.AuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    await audit.record(
        session,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="auth.login",
        entity_type="user",
        entity_id=user.id,
    )
    await session.commit()

    access, refresh, expires_in = auth_service.issue_tokens(user)
    set_auth_cookies(response, access_token=access, refresh_token=refresh)
    return TokenResponse(access_token=access, expires_in=expires_in)


@router.post("/refresh", response_model=TokenResponse, summary="Rotate refresh token")
async def refresh(
    session: SessionDep,
    response: Response,
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
) -> TokenResponse:
    if not refresh_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing refresh token")
    try:
        claims = decode_token(refresh_token, expected_kind="refresh")
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    try:
        user_id = UUID(claims["sub"])
        tenant_id = UUID(claims["tid"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "malformed token") from exc

    try:
        user = await auth_service.rotate_refresh(session, user_id=user_id, tenant_id=tenant_id)
    except auth_service.AuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    access, new_refresh, expires_in = auth_service.issue_tokens(user)
    set_auth_cookies(response, access_token=access, refresh_token=new_refresh)
    return TokenResponse(access_token=access, expires_in=expires_in)


@router.post("/logout", response_model=Message, summary="Clear auth cookies")
async def logout(response: Response) -> Message:
    clear_auth_cookies(response)
    return Message(detail="logged out")


@router.post(
    "/forgot-password",
    response_model=Message,
    summary="Request a password-reset email",
)
async def forgot_password(payload: ForgotPasswordRequest, session: SessionDep) -> Message:
    result = await auth_service.create_password_reset(session, payload.email)
    if result is not None:
        plaintext, user = result
        await audit.record(
            session,
            tenant_id=user.tenant_id,
            actor_user_id=user.id,
            action="auth.password_reset_requested",
            entity_type="user",
            entity_id=user.id,
        )
        await session.commit()

        settings = get_settings()
        link = f"{settings.frontend_base_url}/reset-password?token={plaintext}"
        await send_email(
            to=user.email,
            subject="Reset your Serva password",
            html=f'<p>Click <a href="{link}">here</a> to reset your password. This link expires in one hour.</p>',
            text=f"Reset your password: {link}",
        )
    # Always return 200 so callers cannot enumerate emails.
    return Message(detail="if the email exists, a reset link has been sent")


@router.post(
    "/reset-password",
    response_model=Message,
    summary="Redeem a password-reset token",
)
async def reset_password(payload: ResetPasswordRequest, session: SessionDep) -> Message:
    try:
        user = await auth_service.consume_password_reset(
            session, plaintext=payload.token, new_password=payload.new_password
        )
    except auth_service.AuthError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    await audit.record(
        session,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="auth.password_reset_completed",
        entity_type="user",
        entity_id=user.id,
    )
    await session.commit()
    return Message(detail="password updated")
