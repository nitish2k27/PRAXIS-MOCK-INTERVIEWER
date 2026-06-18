"""Async SQLAlchemy engine + session dependency."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from praxis.config import settings

engine = create_async_engine(
    settings.database_url,
    future=True,
    echo=False,
    pool_pre_ping=True,
)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
