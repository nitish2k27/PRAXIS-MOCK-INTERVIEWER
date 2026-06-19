"""Company-profile repository — archetype reads/seeding go through here."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from praxis.db.models import CompanyProfile


class CompanyProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, profile_id: str) -> CompanyProfile | None:
        return await self.session.get(CompanyProfile, profile_id)

    async def list_all(self) -> Sequence[CompanyProfile]:
        return (await self.session.execute(select(CompanyProfile))).scalars().all()

    async def upsert(
        self,
        *,
        profile_id: str,
        name: str,
        round_mix_json: dict[str, Any],
        rubric_weights_json: dict[str, Any],
        persona_json: dict[str, Any],
    ) -> CompanyProfile:
        profile = await self.session.get(CompanyProfile, profile_id)
        if profile is None:
            profile = CompanyProfile(id=profile_id)
            self.session.add(profile)
        profile.name = name
        profile.round_mix_json = round_mix_json
        profile.rubric_weights_json = rubric_weights_json
        profile.persona_json = persona_json
        await self.session.flush()
        return profile
