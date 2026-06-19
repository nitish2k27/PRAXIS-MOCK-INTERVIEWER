"""Screening artifacts: the weighted competency map and the fit result (Phase 1).

These are persisted onto `interview_sessions.config_json` / `fit_score` in step 4. The
competency map is built deterministically (embeddings-assisted); the fit score blends a
dense similarity with an LLM coverage rubric.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Competency(BaseModel):
    name: str
    weight: float
    covered: bool
    coverage: float  # best cosine similarity of this competency to any resume signal
    evidence: str | None = None  # the resume signal that best matched


class CompetencyMap(BaseModel):
    competencies: list[Competency] = Field(default_factory=list)
    coverage_score: float = 0.0  # weighted fraction of competencies covered (0..1)


class FitResult(BaseModel):
    fit_score: float
    proceed: bool
    rationale: str
    dense_similarity: float
    coverage: float  # LLM coverage rubric over must-haves (0..1)
