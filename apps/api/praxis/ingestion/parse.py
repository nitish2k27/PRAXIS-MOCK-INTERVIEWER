"""Turn resume/JD text into structured Pydantic models via the LLM adapter.

The LLM only produces JSON matching the target schema; it is called through `LLMAdapter`
so tests use `FakeLLM` and nothing here imports the groq SDK.
"""

from __future__ import annotations

from praxis.orchestrator.llm import LLMAdapter
from praxis.schemas.parsing import JDParsed, ResumeParsed

_RESUME_SYSTEM = (
    "You extract structured data from a candidate resume. Return JSON only, matching the "
    "requested fields. Use empty lists/null when something is absent; do not invent facts. "
    "`seniority` is a short label such as junior/mid/senior/staff inferred from the text."
)

_JD_SYSTEM = (
    "You extract structured data from a job description. Return JSON only, matching the "
    "requested fields. `must_haves` are hard requirements; `required_competencies` are the "
    "skill/knowledge areas the role is evaluated on. Use empty lists/null when absent."
)


def _prompt(label: str, fields: str, text: str) -> str:
    return f"Extract the {label} as JSON with fields: {fields}.\n\n{label.upper()} TEXT:\n{text}"


async def parse_resume(text: str, llm: LLMAdapter) -> ResumeParsed:
    prompt = _prompt("resume", "skills, experience, projects, seniority", text)
    return await llm.complete_json(prompt=prompt, schema=ResumeParsed, system=_RESUME_SYSTEM)


async def parse_jd(text: str, llm: LLMAdapter) -> JDParsed:
    prompt = _prompt("job description", "role, role_level, must_haves, required_competencies", text)
    return await llm.complete_json(prompt=prompt, schema=JDParsed, system=_JD_SYSTEM)
