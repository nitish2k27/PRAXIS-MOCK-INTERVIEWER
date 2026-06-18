"""Interview-session listing for the dashboard."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from praxis.auth.deps import get_current_user
from praxis.db.models import InterviewSession, User
from praxis.db.session import get_session

router = APIRouter(tags=["sessions"])


@router.get("/sessions")
async def list_sessions(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[dict[str, Any]]:
    stmt = (
        select(InterviewSession)
        .where(InterviewSession.user_id == user.id)
        .order_by(InterviewSession.started_at.desc())
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": r.id,
            "status": r.status,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "company_profile_id": r.company_profile_id,
            "fit_score": r.fit_score,
        }
        for r in rows
    ]
