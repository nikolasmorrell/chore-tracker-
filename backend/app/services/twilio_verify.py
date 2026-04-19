"""Twilio request signature verification.

Twilio signs each webhook with `X-Twilio-Signature` = base64(HMAC-SHA1(auth_token,
full_url + sorted concatenation of form params)). We verify by reconstructing
that string and comparing in constant time.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import logging

from fastapi import HTTPException, Request, status

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def compute_signature(auth_token: str, url: str, params: dict[str, str]) -> str:
    payload = url + "".join(f"{k}{params[k]}" for k in sorted(params))
    digest = hmac.new(auth_token.encode("utf-8"), payload.encode("utf-8"), hashlib.sha1).digest()
    return base64.b64encode(digest).decode("ascii")


async def verify_twilio_request(request: Request) -> dict[str, str]:
    """Parse the form body and verify the Twilio signature.

    Returns the form dict so the handler doesn't need to re-parse. Raises 403
    on any mismatch. In dev (no auth token set) we log + skip verification.
    """
    settings = get_settings()
    form = await request.form()
    params: dict[str, str] = {k: str(v) for k, v in form.items()}

    if not settings.twilio_auth_token:
        logger.warning("twilio.signature_skipped", extra={"reason": "no_auth_token"})
        return params

    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "missing twilio signature")

    # Twilio signs the full public URL Twilio used, including scheme. Behind a
    # proxy we honor X-Forwarded-Proto so reverse-proxied HTTPS still matches.
    proto = request.headers.get("X-Forwarded-Proto", request.url.scheme)
    host = request.headers.get("X-Forwarded-Host", request.url.netloc)
    path = request.url.path + (f"?{request.url.query}" if request.url.query else "")
    full_url = f"{proto}://{host}{path}"

    expected = compute_signature(settings.twilio_auth_token, full_url, params)
    if not hmac.compare_digest(expected, signature):
        logger.warning("twilio.signature_mismatch", extra={"url": full_url})
        raise HTTPException(status.HTTP_403_FORBIDDEN, "invalid twilio signature")
    return params
