"""Authentication routes — stubs until Phase 2."""
from fastapi import APIRouter, HTTPException, status

router = APIRouter()


def _stub() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")


@router.post("/signup", summary="Create tenant + owner account and start trial")
async def signup() -> None:
    _stub()


@router.post("/login", summary="Email + password login")
async def login() -> None:
    _stub()


@router.post("/refresh", summary="Rotate refresh token")
async def refresh() -> None:
    _stub()


@router.post("/logout", summary="Revoke refresh token")
async def logout() -> None:
    _stub()


@router.post("/forgot-password", summary="Request a password-reset email")
async def forgot_password() -> None:
    _stub()


@router.post("/reset-password", summary="Redeem a password-reset token")
async def reset_password() -> None:
    _stub()
