# Praxis API — Agent Context (apps/api)

FastAPI backend: REST (auth/CRUD) + WebSocket, LangGraph orchestrator, retrieval,
scoring, voice adapters. Read the root `CLAUDE.md` first.

## Stack (locked — see docs/02)
- Python 3.11+, FastAPI (async), Uvicorn, Pydantic v2.
- LangGraph + langchain-core for control flow.
- SQLAlchemy 2.0 async + Alembic. PostgreSQL (Neon in prod, local in dev).
- Redis (live session state, pub/sub, rate limit).
- ChromaDB (vectors), sentence-transformers (bge-small), bge-reranker-base.
- Groq `llama-3.3-70b-versatile` (behind an LLM adapter).
- faster-whisper + silero-vad (STT/VAD), Piper (TTS) — behind adapters.
- Auth: Authlib (Google OIDC) + app JWT in httpOnly cookies.

## Package layout (`praxis/`)
- `orchestrator/` — graphs (controller + per-round) + nodes + conditional edges.
- `schemas/` — Pydantic models, including `graph_state.py` (the ONE state model).
- `voice/` — `stt`, `vad`, `tts` adapters behind interfaces + fakes.
- `retrieval/` — Chroma client, chunking/ingestion per corpus, hybrid search, rerank.
- `scoring/` — scorer interface, prompted impl (MVP) + LoRA impl, rubric defs.
- `rounds/` — `coding`, `system_design`, `hr` (round-specific sources/rubrics; coding
  has the sub-graph + sandbox adapter).
- `auth/` — oauth flow, jwt issue/verify, cookie handling, route guard dependency.
- `db/` — SQLAlchemy models, Alembic env, repositories (no raw SQL in nodes/routes).
- `ws/` — WebSocket lifecycle, message protocol, Redis pub/sub bridge.
- `reports/` — synthesis + persistence + serialization.
- `config.py` — typed config; all model names/thresholds/weights here + `.env`.

## Rules specific to the backend
- Routes/nodes depend on adapters and repositories via FastAPI dependency injection,
  never on concrete SDK clients.
- Blocking ML (whisper, embeddings, scorer) runs via `run_in_executor` / a worker, not
  inline in the event loop.
- All DB access through `db/repositories`. No SQL strings scattered in business logic.
- WebSocket handlers are thin: they translate messages to/from orchestrator events and
  Redis; logic lives in `orchestrator/`.
- Every adapter ships with a deterministic fake so tests don't hit providers/network.

## Commands
- Run dev: `uvicorn praxis.main:app --reload`
- Migrate: `alembic revision --autogenerate -m "msg"` then `alembic upgrade head`
- Quality gate: `ruff check . && ruff format --check . && mypy . && pytest`

## Phase 1 scope here (Ingestion & screening)
Phase 0 (auth, DB models + first migration, upload → object storage, app shell) is
**done**. This phase turns uploaded inputs into structured, persisted state:

1. **Provider adapters first** — `orchestrator/llm.py` (`LLMAdapter` Protocol + `GroqLLM`
   using `groq` SDK at `groq_model` + deterministic `FakeLLM` + `get_llm`) and
   `retrieval/embeddings.py` (`EmbeddingsAdapter` Protocol + `BgeEmbeddings`
   sentence-transformers `bge-small-en-v1.5` + deterministic `FakeEmbeddings` +
   `get_embeddings`). This is the first LLM/embeddings use in the repo.
2. **`ingestion/`** — `extract.py` (pdf/docx → text via pdfplumber/docx2txt, read through
   the storage adapter, blocking work in an executor); `parse.py` (text → structured JSON
   via the LLM adapter); models in `schemas/parsing.py` (`ResumeParsed`, `JDParsed`).
   Persist onto `resumes.parsed_json` / `job_descriptions.parsed_json`.
3. **`ingestion/competency.py` + `screening/`** — weighted competency map (JD must-haves ×
   resume signals, embeddings-assisted); `fit.py` fit score = `w_dense·cosine +
   w_coverage·LLM-coverage-rubric` + rationale; `company.py` resolves a seeded archetype.
   Types in `schemas/screening.py`. Seed 3 archetypes via `db/seeds/company_profiles.py`.
4. **`routes/screening.py`** — `POST /screening {resume_id, jd_id}` runs the pipeline and
   creates the `interview_sessions` row (`fit_score`, `company_profile_id`, and the
   competency map + rationale + parsed summaries in `config_json`). Add `GET /sessions/{id}`.

Locked decisions: competency map lives in `interview_sessions.config_json` (no schema
change / no migration this phase); providers are injected via FastAPI deps so tests use
the fakes; new model names + fit weights/threshold go in `config.py` + `.env`. Nothing
from later phases (no voice, no orchestrator graph, no scoring rubric runtime).
