"""Resume repository — all resume DB access goes through here."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from praxis.db.models import Resume


class ResumeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, resume_id: str) -> Resume | None:
        return await self.session.get(Resume, resume_id)

    async def save_parsed(self, resume_id: str, parsed: dict[str, Any]) -> Resume | None:
        resume = await self.session.get(Resume, resume_id)
        if resume is None:
            return None
        resume.parsed_json = parsed
        await self.session.flush()
        return resume
