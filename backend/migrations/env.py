"""Alembic environment configuration.

Uses SYNC sqlite driver for migrations (Alembic does not support async).
App uses sqlite+aiosqlite for runtime.
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import Base and ALL models so they are registered with metadata
from app.core.database import Base
import app.models.cases  # noqa: F401
import app.models.audit  # noqa: F401
import app.models.documents  # noqa: F401
import app.models.user  # noqa: F401
import app.models.sync_queue  # noqa: F401
import app.models.march  # noqa: F401
import app.models.injuries  # noqa: F401
import app.models.procedures  # noqa: F401
import app.models.medications  # noqa: F401
import app.models.vitals  # noqa: F401
import app.models.evacuation  # noqa: F401
import app.models.events  # noqa: F401
import app.models.field_drop  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    """Derive DB URL from app config — same source as the runtime app, always."""
    from app.core.config import DATABASE_URL
    url = DATABASE_URL
    # Strip async drivers — Alembic requires sync connections
    url = url.replace("sqlite+aiosqlite", "sqlite")
    url = url.replace("postgresql+asyncpg", "postgresql+psycopg2")
    # Remove ?ssl=require — passed via connect_args instead
    url = url.replace("?ssl=require", "").replace("&ssl=require", "")
    return url


def _is_postgres_url(url: str) -> bool:
    return url.startswith("postgresql") or url.startswith("postgres")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no DB connection for autogenerate)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True
    )
    with context.begin_transaction():
        context.run_migrations()


from typing import Dict, Any

def run_migrations_online() -> None:
    """Run migrations in 'online' mode (with DB connection)."""
    configuration: Dict[str, str] = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()  # type: ignore

    connectable = context.config.attributes.get("connection", None)

    if connectable is None:
        from sqlalchemy import create_engine
        url = get_url()
        connect_args = {"sslmode": "require"} if _is_postgres_url(url) else {}
        connectable = create_engine(
            url,
            poolclass=pool.NullPool,
            connect_args=connect_args,
        )

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
