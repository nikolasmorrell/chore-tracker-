"""OCR wrapper.

Textract is the primary; Tesseract is the offline fallback for local/dev and
for tenants without AWS creds. Callers pass raw bytes so the same function
works on S3 objects and uploaded file streams.
"""
from __future__ import annotations

import logging

import anyio

from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def extract_text(data: bytes) -> str:
    provider = get_settings().ocr_provider
    if provider == "textract":
        return await _extract_textract(data)
    if provider == "tesseract":
        return await _extract_tesseract(data)
    return ""


async def _extract_textract(data: bytes) -> str:
    settings = get_settings()
    import boto3  # lazy import

    def _do() -> str:
        client = boto3.client(
            "textract",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )
        response = client.detect_document_text(Document={"Bytes": data})
        lines = [b["Text"] for b in response.get("Blocks", []) if b.get("BlockType") == "LINE"]
        return "\n".join(lines)

    return await anyio.to_thread.run_sync(_do)


async def _extract_tesseract(data: bytes) -> str:
    try:
        import io

        import pytesseract
        from PIL import Image
    except ImportError:
        logger.warning("ocr.tesseract_unavailable")
        return ""

    def _do() -> str:
        image = Image.open(io.BytesIO(data))
        return str(pytesseract.image_to_string(image))

    return await anyio.to_thread.run_sync(_do)
