"""Interview-session listing + detail for the dashboard."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from praxis.auth.deps import get_current_user
from praxis.db.models import InterviewSession, User
from praxis.db.session import get_session

router = APIRouter(tags=["sessions"])


def session_detail(s: InterviewSession) -> dict[str, Any]:
    """Full detail shape, shared by `POST /screening` and `GET /sessions/{id}`."""
    return {
        "id": s.id,
        "status": s.status,
        "resume_id": s.resume_id,
        "jd_id": s.jd_id,
        "company_profile_id": s.company_profile_id,
        "fit_score": s.fit_score,
        "config_json": s.config_json,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "completed_at": s.completed_at.isoformat() if s.completed_at else None,
    }


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


@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    row = await session.get(InterviewSession, session_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")
    return session_detail(row)
