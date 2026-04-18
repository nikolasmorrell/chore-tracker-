"""Typed application settings loaded from environment variables.

All configuration flows through `Settings` — no module reads os.environ
directly. Use `get_settings()` which is cached for the lifetime of the process.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: Literal["development", "staging", "production", "test"] = "development"
    app_name: str = "sellable"
    app_base_url: str = "http://localhost:8000"
    frontend_base_url: str = "http://localhost:3000"
    log_level: str = "INFO"

    # Database
    database_url: str
    database_sync_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Auth
    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_seconds: int = 900
    jwt_refresh_ttl_seconds: int = 2_592_000
    password_reset_ttl_seconds: int = 3600
    invite_ttl_seconds: int = 604_800

    # Object storage
    s3_endpoint_url: str | None = None
    s3_region: str = "us-east-1"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_bucket_documents: str = "sellable-documents"
    s3_bucket_call_audio: str = "sellable-call-audio"
    s3_presigned_url_ttl_seconds: int = 900

    # Claude
    anthropic_api_key: str = ""
    claude_model_primary: str = "claude-opus-4-7"
    claude_model_fast: str = "claude-haiku-4-5-20251001"
    claude_max_output_tokens: int = 4096

    # OCR
    ocr_provider: Literal["textract", "tesseract", "none"] = "textract"
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # Voice
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    twilio_voice_webhook_secret: str = ""
    deepgram_api_key: str = ""
    tts_provider: Literal["deepgram", "elevenlabs", "none"] = "deepgram"
    tts_voice: str = "aura-asteria-en"

    # Email
    sendgrid_api_key: str = ""
    email_from_address: str = "no-reply@sellable.app"
    email_from_name: str = "Sellable"

    # Billing
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_starter: str = ""
    stripe_price_pro: str = ""
    stripe_price_enterprise: str = ""
    stripe_trial_days: int = 14

    # Rate limiting
    rate_limit_per_ip_per_minute: int = 120
    rate_limit_per_tenant_per_minute: int = 600

    # Observability
    sentry_dsn: str = ""
    sentry_traces_sample_rate: float = 0.1

    cors_allow_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])


@lru_cache
def get_settings() -> Settings:
    return Settings()
