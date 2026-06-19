"""End-to-end POST /screening with fake providers, asserting the persisted session."""

from __future__ import annotations

import io

from praxis.db.models import Resume, User
from praxis.db.seeds.company_profiles import seed_company_profiles
from praxis.main import app
from praxis.orchestrator.llm import FakeLLM, get_llm
from praxis.retrieval.embeddings import FakeEmbeddings, get_embeddings
from tests._fixtures import make_pdf

# Queued in pipeline order: resume parse, JD parse, then the fit coverage rubric.
_LLM_RESPONSES = [
    {
        "skills": ["python", "fastapi"],
        "experience": [{"company": "Acme", "title": "Engineer", "highlights": ["built apis"]}],
        "projects": [{"name": "praxis", "tech": ["langgraph"]}],
        "seniority": "senior",
    },
    {
        "role": "Backend Engineer",
        "role_level": "senior",
        "must_haves": ["python"],
        "required_competencies": ["python", "api design"],
    },
    {"coverage": 0.8, "rationale": "covers python well", "met": ["python"], "missing": []},
]


async def _login(client) -> None:
    await client.get("/auth/google/callback", follow_redirects=False)


def _use_fake_providers() -> FakeLLM:
    fake_llm = FakeLLM(responses=list(_LLM_RESPONSES))
    app.dependency_overrides[get_llm] = lambda: fake_llm
    app.dependency_overrides[get_embeddings] = lambda: FakeEmbeddings()
    return fake_llm


async def _upload_inputs(client) -> tuple[str, str]:
    r = await client.post(
        "/resumes",
        files={
            "file": (
                "cv.pdf",
                io.BytesIO(make_pdf("python fastapi senior engineer")),
                "application/pdf",
            )
        },
    )
    assert r.status_code == 201, r.text
    resume_id = r.json()["id"]

    j = await client.post(
        "/job_descriptions",
        data={"raw_text": "We need a senior backend engineer strong in python and api design."},
    )
    assert j.status_code == 201, j.text
    return resume_id, j.json()["id"]


async def test_screening_end_to_end(client, db) -> None:
    await seed_company_profiles(db)
    await db.commit()
    await _login(client)
    fake_llm = _use_fake_providers()
    resume_id, jd_id = await _upload_inputs(client)

    resp = await client.post("/screening", json={"resume_id": resume_id, "jd_id": jd_id})

    assert resp.status_code == 201, resp.text
    detail = resp.json()
    assert detail["status"] == "screened"
    assert detail["resume_id"] == resume_id
    assert detail["jd_id"] == jd_id
    assert detail["company_profile_id"] == "faang-structured"  # default (no archetype keywords)
    assert isinstance(detail["fit_score"], float)
    assert 0.0 <= detail["fit_score"] <= 1.0

    cfg = detail["config_json"]
    assert set(cfg) == {"competency_map", "fit", "resume_summary", "jd_summary"}
    assert cfg["fit"]["coverage"] == 0.8
    by_name = {c["name"]: c for c in cfg["competency_map"]["competencies"]}
    assert by_name["python"]["covered"] is True  # resume skill "python" matches identically
    assert by_name["api design"]["covered"] is False
    assert cfg["resume_summary"]["seniority"] == "senior"
    assert cfg["jd_summary"]["role"] == "Backend Engineer"

    # All three LLM responses were consumed (resume, jd, coverage).
    assert len(fake_llm.calls) == 3

    # Re-read through the API proves the row persisted; and parsed_json landed on the inputs.
    got = await client.get(f"/sessions/{detail['id']}")
    assert got.status_code == 200
    assert got.json()["fit_score"] == detail["fit_score"]

    db.expire_all()
    resume_row = await db.get(Resume, resume_id)
    assert resume_row is not None
    assert resume_row.parsed_json is not None
    assert resume_row.parsed_json["skills"] == ["python", "fastapi"]


async def test_screening_requires_auth(client) -> None:
    r = await client.post("/screening", json={"resume_id": "x", "jd_id": "y"})
    assert r.status_code == 401


async def test_screening_rejects_unowned_resume(client, db) -> None:
    await _login(client)
    _use_fake_providers()

    other = User(oauth_provider="google", oauth_sub="other-sub", email="o@x.com", name="O")
    db.add(other)
    await db.flush()
    foreign = Resume(user_id=other.id, file_url="file:///tmp/foreign.pdf")
    db.add(foreign)
    await db.commit()

    r = await client.post("/screening", json={"resume_id": foreign.id, "jd_id": "anything"})
    assert r.status_code == 404
