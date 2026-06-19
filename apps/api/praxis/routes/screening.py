"""Screening pipeline endpoint: resume + JD → parsed state → fit → interview session.

Runs extract → parse (persisting parsed_json) → competency map → fit → company resolution,
then persists an `interview_sessions` row. Every provider (LLM, embeddings, storage) is
injected via FastAPI deps so tests drive the whole thing with fakes. All rows are scoped to
the authenticated user.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from praxis.auth.deps import get_current_user
from praxis.db.models import InterviewSession, JobDescription, Resume, User
from praxis.db.repositories import (
    CompanyProfileRepository,
    JobDescriptionRepository,
    ResumeRepository,
)
from praxis.db.session import get_session
from praxis.ingestion.competency import build_competency_map
from praxis.ingestion.extract import extract_text
from praxis.ingestion.parse import parse_jd, parse_resume
from praxis.orchestrator.llm import LLMAdapter, get_llm
from praxis.retrieval.embeddings import EmbeddingsAdapter, get_embeddings
from praxis.routes.sessions import session_detail
from praxis.schemas.parsing import JDParsed, ResumeParsed
from praxis.screening.company import resolve_company_profile
from praxis.screening.fit import compute_fit
from praxis.storage import StorageBackend, get_storage

router = APIRouter(tags=["screening"])


class ScreeningRequest(BaseModel):
    resume_id: str
    jd_id: str


async def _owned_resume(session: AsyncSession, resume_id: str, user: User) -> Resume:
    resume = await ResumeRepository(session).get_by_id(resume_id)
    if resume is None or resume.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="resume not found")
    return resume


async def _owned_jd(session: AsyncSession, jd_id: str, user: User) -> JobDescription:
    jd = await JobDescriptionRepository(session).get_by_id(jd_id)
    if jd is None or jd.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="job description not found"
        )
    return jd


@router.post("/screening", status_code=status.HTTP_201_CREATED)
async def run_screening(
    body: ScreeningRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
    llm: Annotated[LLMAdapter, Depends(get_llm)],
    embeddings: Annotated[EmbeddingsAdapter, Depends(get_embeddings)],
) -> dict[str, Any]:
    resume = await _owned_resume(session, body.resume_id, user)
    jd = await _owned_jd(session, body.jd_id, user)

    # 1. Inputs → text (JD may have been supplied as raw text instead of a file).
    resume_text = await extract_text(resume.file_url, storage)
    if jd.raw_text:
        jd_text = jd.raw_text
    elif jd.file_url:
        jd_text = await extract_text(jd.file_url, storage)
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="job description has no text or file to screen against",
        )

    # 2. Text → structured, persisted parsing.
    resume_parsed: ResumeParsed = await parse_resume(resume_text, llm)
    jd_parsed: JDParsed = await parse_jd(jd_text, llm)
    await ResumeRepository(session).save_parsed(resume.id, resume_parsed.model_dump(mode="json"))
    await JobDescriptionRepository(session).save_parsed(jd.id, jd_parsed.model_dump(mode="json"))

    # 3. Reconcile, score, resolve archetype.
    competency_map = await build_competency_map(resume_parsed, jd_parsed, embeddings)
    fit = await compute_fit(resume_text, jd_text, jd_parsed.must_haves, llm, embeddings)
    profile = await resolve_company_profile(jd_parsed, CompanyProfileRepository(session))

    # 4. Persist the screened interview session.
    interview = InterviewSession(
        user_id=user.id,
        resume_id=resume.id,
        jd_id=jd.id,
        company_profile_id=profile.id,
        status="screened",
        fit_score=fit.fit_score,
        config_json={
            "competency_map": competency_map.model_dump(mode="json"),
            "fit": fit.model_dump(mode="json"),
            "resume_summary": resume_parsed.model_dump(mode="json"),
            "jd_summary": jd_parsed.model_dump(mode="json"),
        },
    )
    session.add(interview)
    await session.commit()
    await session.refresh(interview)
    return session_detail(interview)
