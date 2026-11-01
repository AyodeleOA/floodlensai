from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_settings = get_settings()

# Strip the +psycopg suffix for SQLite test fallback
_db_url = _settings.DATABASE_URL

# SQLite doesn't support pool_size/max_overflow
_is_sqlite = _db_url.startswith("sqlite")

engine: AsyncEngine = create_async_engine(
    _db_url,
    echo=False,
    pool_pre_ping=True,
    **({} if _is_sqlite else {"pool_size": 10, "max_overflow": 20}),
)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for getting a session outside of FastAPI (workers, tasks)."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
