"""Async database session."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from sqlalchemy.pool import NullPool

from app.core.config import DATABASE_URL

_is_postgres = DATABASE_URL.startswith("postgresql")

# SQLite concurrency safeguards: multi-process/thread connection support
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# Vercel is serverless — persistent pools provide no benefit and leak connections on Neon.
# Use NullPool for PostgreSQL; keep default pool for local SQLite dev.
_pool_kwargs: dict = (
    {"poolclass": NullPool}
    if _is_postgres
    else {"pool_pre_ping": True, "pool_recycle": 3600}
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    **_pool_kwargs,
)

# SQLite WAL mode for better concurrency performance
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

