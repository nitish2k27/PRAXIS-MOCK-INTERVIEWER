"""Reconcile JD requirements against resume signals into a weighted competency map.

Deterministic: competencies come from the JD's must-haves and required competencies,
weighted by config; each is marked covered when its best cosine similarity to any resume
signal clears the configured threshold. The embeddings adapter does the signal matching, so
nodes/routes never touch sentence-transformers directly.
"""

from __future__ import annotations

from praxis.config import settings
from praxis.retrieval.embeddings import EmbeddingsAdapter, cosine
from praxis.schemas.parsing import JDParsed, ResumeParsed
from praxis.schemas.screening import Competency, CompetencyMap


def _resume_signals(resume: ResumeParsed) -> list[str]:
    signals: list[str] = list(resume.skills)
    for exp in resume.experience:
        if exp.title:
            signals.append(exp.title)
        signals.extend(exp.highlights)
    for proj in resume.projects:
        if proj.name:
            signals.append(proj.name)
        signals.extend(proj.tech)
    return [s for s in (sig.strip() for sig in signals) if s]


def _weighted_competencies(jd: JDParsed) -> dict[str, float]:
    """Map each JD competency name to its raw (pre-normalization) weight.

    Must-haves outrank required competencies; if a name appears in both, the higher
    (must-have) weight wins.
    """
    weights: dict[str, float] = {}
    for name in jd.required_competencies:
        key = name.strip()
        if key:
            weights[key] = settings.competency_required_weight
    for name in jd.must_haves:
        key = name.strip()
        if key:
            weights[key] = settings.competency_must_have_weight
    return weights


async def build_competency_map(
    resume: ResumeParsed,
    jd: JDParsed,
    embeddings: EmbeddingsAdapter,
) -> CompetencyMap:
    raw_weights = _weighted_competencies(jd)
    if not raw_weights:
        return CompetencyMap()

    names = list(raw_weights)
    total = sum(raw_weights.values())
    signals = _resume_signals(resume)

    comp_vectors = await embeddings.embed(names)
    signal_vectors = await embeddings.embed(signals) if signals else []

    threshold = settings.competency_match_threshold
    competencies: list[Competency] = []
    covered_weight = 0.0
    for name, comp_vec in zip(names, comp_vectors, strict=True):
        best_sim = 0.0
        best_signal: str | None = None
        for signal, sig_vec in zip(signals, signal_vectors, strict=True):
            sim = cosine(comp_vec, sig_vec)
            if sim > best_sim:
                best_sim = sim
                best_signal = signal
        weight = raw_weights[name] / total
        covered = best_sim >= threshold
        if covered:
            covered_weight += weight
        competencies.append(
            Competency(
                name=name,
                weight=weight,
                covered=covered,
                coverage=best_sim,
                evidence=best_signal if covered else None,
            )
        )

    return CompetencyMap(competencies=competencies, coverage_score=covered_weight)
