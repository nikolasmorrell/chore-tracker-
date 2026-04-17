"""OCR wrapper (AWS Textract primary, Tesseract fallback)."""
from __future__ import annotations


async def extract_text(s3_key: str) -> str:  # pragma: no cover
    raise NotImplementedError("OCR implemented in Phase 2")
