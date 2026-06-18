"""User repository — all user DB access goes through here."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from praxis.db.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: str) -> User | None:
        return await self.session.get(User, user_id)

    async def upsert_by_oauth(
        self, *, provider: str, sub: str, email: str, name: str | None
    ) -> User:
        stmt = select(User).where(
            User.oauth_provider == provider,
            User.oauth_sub == sub,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            existing.email = email
            if name:
                existing.name = name
            await self.session.flush()
            return existing
        user = User(oauth_provider=provider, oauth_sub=sub, email=email, name=name)
        self.session.add(user)
        await self.session.flush()
        return user
