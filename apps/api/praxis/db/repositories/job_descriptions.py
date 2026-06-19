"""Job-description repository — all JD DB access goes through here."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from praxis.db.models import JobDescription


class JobDescriptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, jd_id: str) -> JobDescription | None:
        return await self.session.get(JobDescription, jd_id)

    async def save_parsed(self, jd_id: str, parsed: dict[str, Any]) -> JobDescription | None:
        jd = await self.session.get(JobDescription, jd_id)
        if jd is None:
            return None
        jd.parsed_json = parsed
        await self.session.flush()
        return jd
