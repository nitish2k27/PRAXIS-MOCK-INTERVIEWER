"""Pytest fixtures: in-memory aiosqlite + async httpx client + Fake OIDC + tmp storage."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from praxis.auth.deps import get_current_user as _gcu  # noqa: F401  (ensure module import)
from praxis.auth.deps import get_oidc_provider
from praxis.auth.providers import FakeOIDCProvider
from praxis.db.base import Base
from praxis.db.session import get_session
from praxis.main import app
from praxis.storage import LocalStorage, get_storage


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        await eng.dispose()


@pytest_asyncio.fixture
async def db(engine) -> AsyncIterator[AsyncSession]:
    sm = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with sm() as s:
        yield s


@pytest.fixture
def fake_oidc() -> FakeOIDCProvider:
    return FakeOIDCProvider()


@pytest_asyncio.fixture
async def client(engine, tmp_path: Path, fake_oidc) -> AsyncIterator[AsyncClient]:
    sm = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with sm() as s:
            yield s

    storage = LocalStorage(base_dir=str(tmp_path / "uploads"))

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_oidc_provider] = lambda: fake_oidc
    app.dependency_overrides[get_storage] = lambda: storage

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
