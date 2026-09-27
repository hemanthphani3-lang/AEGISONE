from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.config import DATABASE_URL
from app.db.models import Base

# Format database URL for async engine if needed
url = DATABASE_URL
if url.startswith("postgresql://"):
    url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
    url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)

from sqlalchemy.pool import NullPool

engine: AsyncEngine = create_async_engine(
    url,
    echo=False,
    future=True,
    pool_pre_ping=True,
    poolclass=NullPool,
    connect_args={"statement_cache_size": 0, "prepared_statement_cache_size": 0},
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


import asyncio

async def check_database_connection() -> bool:
    """Test database connectivity safely."""
    try:
        async with asyncio.timeout(5.0):
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def create_tables() -> None:
    """Helper to create all tables and apply safe backward-compatible schema updates."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            await conn.execute(text("ALTER TABLE policies ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;"))
        except Exception:
            pass


async def drop_tables() -> None:
    """Helper to drop all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
