"""SQLAlchemy ORM models — core schema from docs/01 §9.1."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("oauth_provider", "oauth_sub", name="uq_users_oauth"),
        Index("ix_users_email", "email"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    oauth_provider: Mapped[str] = mapped_column(String(32), nullable=False)
    oauth_sub: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    raw_text: Mapped[str | None] = mapped_column(Text)
    file_url: Mapped[str | None] = mapped_column(Text)
    parsed_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    round_mix_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    rubric_weights_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    persona_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    __table_args__ = (Index("ix_sessions_user_started", "user_id", "started_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    resume_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("resumes.id", ondelete="SET NULL")
    )
    jd_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("job_descriptions.id", ondelete="SET NULL")
    )
    company_profile_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("company_profiles.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created")
    config_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    fit_score: Mapped[float | None] = mapped_column(Float)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Round(Base):
    __tablename__ = "rounds"
    __table_args__ = (Index("ix_rounds_session", "session_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    stage: Mapped[str | None] = mapped_column(String(32))
    score: Mapped[float | None] = mapped_column(Float)
    rubric_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Turn(Base):
    __tablename__ = "turns"
    __table_args__ = (Index("ix_turns_round_seq", "round_id", "seq"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    round_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    speaker: Mapped[str] = mapped_column(String(32), nullable=False)
    transcript: Mapped[str | None] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(32))
    retrieval_refs_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    scores_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    audio_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CodeArtifact(Base):
    __tablename__ = "code_artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    round_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False
    )
    language: Mapped[str] = mapped_column(String(32), nullable=False)
    code_text: Mapped[str] = mapped_column(Text, nullable=False)
    test_results_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False
    )
    overall_band: Mapped[str | None] = mapped_column(String(32))
    per_competency_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    strengths_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    gaps_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    remediation_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
