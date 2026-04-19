"""Alembic migration environment.

Uses the synchronous `DATABASE_SYNC_URL` (psycopg driver) because Alembic
operations run in a blocking context. The async engine lives in app.db.session.
"""
from __future__ import annotations

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import get_settings
from app.db import models  # noqa: F401 — ensure models are registered
from app.db.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()

# Normalize to the psycopg v3 dialect; SQLAlchemy defaults `postgresql://`
# to psycopg2, which we do not install.
_sync_url = settings.database_sync_url
if _sync_url.startswith("postgresql://"):
    _sync_url = "postgresql+psycopg://" + _sync_url.removeprefix("postgresql://")
config.set_main_option("sqlalchemy.url", _sync_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=_sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
