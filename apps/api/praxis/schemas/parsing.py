"""Structured-parsing models for resumes and job descriptions (Phase 1 ingestion).

These are the shapes the LLM adapter fills in via JSON output and that get persisted onto
`resumes.parsed_json` / `job_descriptions.parsed_json`. Every field is defaulted so that a
partial or sparse LLM response still validates — normalization (e.g. of seniority/level
vocabulary) happens later in screening, not here.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ExperienceItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    company: str | None = None
    title: str | None = None
    duration: str | None = None
    highlights: list[str] = Field(default_factory=list)


class ProjectItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    description: str | None = None
    tech: list[str] = Field(default_factory=list)


class ResumeParsed(BaseModel):
    model_config = ConfigDict(extra="ignore")

    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    seniority: str | None = None


class JDParsed(BaseModel):
    model_config = ConfigDict(extra="ignore")

    role: str | None = None
    role_level: str | None = None
    must_haves: list[str] = Field(default_factory=list)
    required_competencies: list[str] = Field(default_factory=list)
