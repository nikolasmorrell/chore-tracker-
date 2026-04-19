"""S3/MinIO wrapper.

We use boto3's sync client from a thread pool. Each call constructs a fresh
client so credentials rotate cleanly and tests can stub `_s3_client`.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

import anyio
import boto3
from botocore.config import Config

from app.core.config import get_settings


def _s3_client() -> Any:
    settings = get_settings()
    return boto3.client(
        "s3",
        region_name=settings.s3_region,
        endpoint_url=settings.s3_endpoint_url or None,
        aws_access_key_id=settings.s3_access_key_id or None,
        aws_secret_access_key=settings.s3_secret_access_key or None,
        config=Config(signature_version="s3v4"),
    )


def build_document_key(tenant_id: str, original_filename: str) -> str:
    """Opaque key so original filenames never leak across tenants."""
    suffix = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else "bin"
    # keep only alnum in suffix — defense in depth
    suffix = "".join(c for c in suffix if c.isalnum())[:10] or "bin"
    return f"documents/{tenant_id}/{uuid4().hex}.{suffix}"


async def presigned_post(bucket: str, key: str, *, content_type: str, max_bytes: int) -> dict[str, Any]:
    """Return a presigned POST contract the browser can upload to directly."""
    settings = get_settings()

    def _do() -> dict[str, Any]:
        client = _s3_client()
        result: dict[str, Any] = client.generate_presigned_post(
            Bucket=bucket,
            Key=key,
            Fields={"Content-Type": content_type},
            Conditions=[
                {"Content-Type": content_type},
                ["content-length-range", 1, max_bytes],
            ],
            ExpiresIn=settings.s3_presigned_url_ttl_seconds,
        )
        return result

    return await anyio.to_thread.run_sync(_do)


async def presigned_get(bucket: str, key: str) -> str:
    settings = get_settings()

    def _do() -> str:
        client = _s3_client()
        url: str = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=settings.s3_presigned_url_ttl_seconds,
        )
        return url

    return await anyio.to_thread.run_sync(_do)


async def get_object_bytes(bucket: str, key: str) -> bytes:
    def _do() -> bytes:
        client = _s3_client()
        obj = client.get_object(Bucket=bucket, Key=key)
        body = obj["Body"]
        try:
            return bytes(body.read())
        finally:
            body.close()

    return await anyio.to_thread.run_sync(_do)


async def head_object(bucket: str, key: str) -> dict[str, Any] | None:
    def _do() -> dict[str, Any] | None:
        client = _s3_client()
        try:
            return dict(client.head_object(Bucket=bucket, Key=key))
        except client.exceptions.ClientError:
            return None

    return await anyio.to_thread.run_sync(_do)
