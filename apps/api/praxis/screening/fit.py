"""Screening fit score: blends a dense resume↔JD similarity with an LLM coverage rubric.

    fit_score = w_dense · cosine(resume, jd) + w_coverage · coverage(must-haves)

The rubric numbers come from the LLM (it judges how well the resume covers the JD's hard
requirements); the weights, and the proceed threshold, live in config. Both providers are
called through their adapters, so tests use the fakes.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from praxis.config import settings
from praxis.orchestrator.llm import LLMAdapter
from praxis.retrieval.embeddings import EmbeddingsAdapter, cosine
from praxis.schemas.screening import FitResult

_COVERAGE_SYSTEM = (
    "You assess how well a candidate resume covers a job's hard requirements. Return JSON "
    "only. `coverage` is a number from 0 to 1 (fraction of must-haves clearly evidenced). "
    "`met` and `missing` list the must-haves; `rationale` is one or two sentences."
)


class _CoverageRubric(BaseModel):
    coverage: float = 0.0
    rationale: str = ""
    met: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


async def compute_fit(
    resume_text: str,
    jd_text: str,
    must_haves: list[str],
    llm: LLMAdapter,
    embeddings: EmbeddingsAdapter,
) -> FitResult:
    resume_vec, jd_vec = await embeddings.embed([resume_text, jd_text])
    dense = _clamp01(cosine(resume_vec, jd_vec))

    if must_haves:
        rubric = await _assess_coverage(resume_text, must_haves, llm)
        coverage = _clamp01(rubric.coverage)
        llm_rationale = rubric.rationale
    else:
        coverage = 1.0
        llm_rationale = "No must-haves specified; coverage treated as full."

    fit_score = settings.fit_w_dense * dense + settings.fit_w_coverage * coverage
    proceed = fit_score >= settings.fit_proceed_threshold
    rationale = (
        f"dense similarity {dense:.2f}, must-have coverage {coverage:.2f} "
        f"→ fit {fit_score:.2f} ({'proceed' if proceed else 'below threshold'}). {llm_rationale}"
    ).strip()

    return FitResult(
        fit_score=fit_score,
        proceed=proceed,
        rationale=rationale,
        dense_similarity=dense,
        coverage=coverage,
    )


async def _assess_coverage(
    resume_text: str, must_haves: list[str], llm: LLMAdapter
) -> _CoverageRubric:
    listed = "\n".join(f"- {m}" for m in must_haves)
    prompt = (
        "Assess how well the resume below covers each must-have requirement.\n\n"
        f"MUST-HAVES:\n{listed}\n\nRESUME:\n{resume_text}"
    )
    return await llm.complete_json(prompt=prompt, schema=_CoverageRubric, system=_COVERAGE_SYSTEM)
