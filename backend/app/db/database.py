"""
Database connection and session management.
Supports both SQLite (dev) and PostgreSQL (production).
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()

# Engine — NullPool for SQLite, default for PostgreSQL
_is_sqlite = settings.database_url.startswith("sqlite")
_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    poolclass=NullPool if _is_sqlite else None,
    pool_pre_ping=True,
)

_async_session_factory = async_sessionmaker(
    _engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yield a database session."""
    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def session_context() -> AsyncGenerator[AsyncSession, None]:
    """Programmatic session context (for scripts / workers)."""
    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables. Call once on startup."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close engine on shutdown."""
    await _engine.dispose()
