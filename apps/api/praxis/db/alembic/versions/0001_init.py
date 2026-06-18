"""init core schema

Revision ID: 0001_init
Revises:
Create Date: 2026-06-16
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("oauth_provider", sa.String(32), nullable=False),
        sa.Column("oauth_sub", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("oauth_provider", "oauth_sub", name="uq_users_oauth"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "resumes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_url", sa.Text, nullable=False),
        sa.Column("parsed_json", sa.JSON),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "job_descriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("raw_text", sa.Text),
        sa.Column("file_url", sa.Text),
        sa.Column("parsed_json", sa.JSON),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "company_profiles",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("round_mix_json", sa.JSON, nullable=False),
        sa.Column("rubric_weights_json", sa.JSON, nullable=False),
        sa.Column("persona_json", sa.JSON, nullable=False),
    )

    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("resume_id", sa.String(36), sa.ForeignKey("resumes.id", ondelete="SET NULL")),
        sa.Column(
            "jd_id", sa.String(36), sa.ForeignKey("job_descriptions.id", ondelete="SET NULL")
        ),
        sa.Column(
            "company_profile_id",
            sa.String(64),
            sa.ForeignKey("company_profiles.id", ondelete="SET NULL"),
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="created"),
        sa.Column("config_json", sa.JSON),
        sa.Column("fit_score", sa.Float),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_sessions_user_started", "interview_sessions", ["user_id", "started_at"])

    op.create_table(
        "rounds",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("interview_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("stage", sa.String(32)),
        sa.Column("score", sa.Float),
        sa.Column("rubric_json", sa.JSON),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_rounds_session", "rounds", ["session_id"])

    op.create_table(
        "turns",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "round_id",
            sa.String(36),
            sa.ForeignKey("rounds.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("seq", sa.Integer, nullable=False),
        sa.Column("speaker", sa.String(32), nullable=False),
        sa.Column("transcript", sa.Text),
        sa.Column("intent", sa.String(32)),
        sa.Column("retrieval_refs_json", sa.JSON),
        sa.Column("scores_json", sa.JSON),
        sa.Column("audio_url", sa.Text),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_turns_round_seq", "turns", ["round_id", "seq"])

    op.create_table(
        "code_artifacts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "round_id",
            sa.String(36),
            sa.ForeignKey("rounds.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("language", sa.String(32), nullable=False),
        sa.Column("code_text", sa.Text, nullable=False),
        sa.Column("test_results_json", sa.JSON),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("interview_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("overall_band", sa.String(32)),
        sa.Column("per_competency_json", sa.JSON),
        sa.Column("strengths_json", sa.JSON),
        sa.Column("gaps_json", sa.JSON),
        sa.Column("remediation_json", sa.JSON),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("code_artifacts")
    op.drop_index("ix_turns_round_seq", table_name="turns")
    op.drop_table("turns")
    op.drop_index("ix_rounds_session", table_name="rounds")
    op.drop_table("rounds")
    op.drop_index("ix_sessions_user_started", table_name="interview_sessions")
    op.drop_table("interview_sessions")
    op.drop_table("company_profiles")
    op.drop_table("job_descriptions")
    op.drop_table("resumes")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
