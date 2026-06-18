# Praxis — Technical Requirements Document (TRD)

> Purpose: this is the **locked stack**. When building with Claude Code, do not introduce technologies outside this list without an explicit decision recorded here. Drift is the #1 risk in agent-assisted builds.

---

## 1. Locked stack (do not substitute)

### Frontend
- **React 18 + Vite + TypeScript** (strict mode on).
- **Tailwind CSS** for styling.
- **Monaco Editor** (`@monaco-editor/react`) — coding round.
- **Native Web Audio API / MediaRecorder** for mic capture; Web Audio for playback.
- Native **WebSocket** client (no socket.io unless a concrete reason is recorded).
- State: React Query (server state) + Zustand (local UI/session state). No Redux.

### Backend
- **Python 3.11+**, **FastAPI** (async), served by **Uvicorn** (with `--workers` behind a process manager in prod).
- WebSocket via FastAPI's native support.
- **Pydantic v2** for all request/response and state models.

### Orchestration & AI
- **LangGraph** (+ `langchain-core`) for the round controller and per-round loops. LangGraph owns control flow; do not hand-roll the state machine.
- **LLM:** **Groq API**, model `llama-3.3-70b-versatile` (primary). Model name in config; one place to change it.
- **STT:** **faster-whisper** (local, `small`/`medium` model) + **silero-vad** for voice-activity & end-of-turn. (Deepgram is an allowed swap if local latency is unacceptable — record the decision.)
- **TTS:** **Piper** (local, default) with an adapter so **ElevenLabs** can be swapped for quality. TTS behind an interface; never call a provider SDK directly from a node.
- **Embeddings:** `sentence-transformers`, model `BAAI/bge-small-en-v1.5` (or `bge-m3` if multilingual needed).
- **Reranker:** `BAAI/bge-reranker-base` (cross-encoder). Cohere rerank is an allowed API swap.
- **Vector DB:** **ChromaDB** (persistent client). Weaviate only if scale demands it later.
- **Fine-tuning:** `transformers` + `peft` + `trl` for the **LoRA rubric scorer**, trained on Colab. Served via a small `transformers` pipeline (or vLLM if throughput needs it). A `DeBERTa-v3` classifier is an allowed alternative for the scorer — pick one and stick to it.

### Data & infra
- **PostgreSQL** (Neon) + **SQLAlchemy 2.0 (async)** + **Alembic** migrations. (No Prisma — this backend is Python.)
- **Redis** for live session state, pub/sub, rate limiting.
- **Object storage:** Cloudflare R2 / S3-compatible (`boto3`). Local disk in dev.
- **Sandbox (code execution):** **Judge0** self-hosted via Docker (coding round tests). piston is an allowed swap.
- **Docker + docker-compose** for the whole dev environment (db, redis, chroma, judge0, api, web).

### Auth (standard)
- **OAuth 2.0 / OpenID Connect**, **Google** as primary IdP (GitHub optional), via **Authlib** on FastAPI.
- App-issued **JWT**: short-lived access token + refresh token, stored in **httpOnly, Secure, SameSite cookies**.
- No password storage, no custom crypto. This is the "most standard" path and is fully interview-explainable.

### Quality tooling
- Python: **Ruff** (lint+format), **mypy** (type check), **pytest** + **pytest-asyncio**.
- TS: **ESLint** + **Prettier** + **tsc --strict**, **Vitest** + React Testing Library.
- **pre-commit** hooks running the above on staged files.

---

## 2. Repository layout (monorepo)

```
praxis/
├─ docs/                      # these six documents
├─ apps/
│  ├─ web/                    # React + Vite + TS
│  └─ api/                    # FastAPI
│     ├─ praxis/
│     │  ├─ orchestrator/     # LangGraph graphs + nodes
│     │  ├─ voice/            # STT, VAD, TTS adapters
│     │  ├─ retrieval/        # chroma, hybrid search, rerank
│     │  ├─ scoring/          # LoRA scorer client, rubrics
│     │  ├─ rounds/           # coding, system_design, hr
│     │  ├─ auth/             # oauth, jwt
│     │  ├─ db/               # sqlalchemy models, alembic
│     │  ├─ schemas/          # pydantic models incl. graph state
│     │  └─ ws/               # websocket handlers
│     └─ tests/
├─ ml/                        # LoRA training notebooks/scripts, datasets
├─ infra/                     # docker-compose, Dockerfiles, seed scripts
└─ docs/
```

---

## 3. Hard technical constraints

1. **All provider calls behind adapters.** STT/TTS/LLM/embeddings/rerank each have an interface in `voice/`, `orchestrator/`, `retrieval/`. Nodes call interfaces, never SDKs. This is what lets you swap Piper↔ElevenLabs or Groq↔other without touching graph logic.
2. **LangGraph owns control flow.** No imperative round-sequencing outside the graph. Gates are conditional edges.
3. **Graph state is a single Pydantic model.** No ad-hoc dicts passed between nodes.
4. **Scoring numbers come from the scorer, not the LLM.** The LLM produces qualitative critique and the probe decision; rubric numbers come from the fine-tuned model for consistency.
5. **No browser storage for app data.** Server is the source of truth; the SPA caches via React Query.
6. **Config in one place.** Model names, thresholds, weights, time budgets live in a typed config module + `.env`. No magic numbers in nodes.
7. **Async end-to-end.** FastAPI, SQLAlchemy, and the orchestrator are async; blocking ML calls run in a thread/process pool.

---

## 4. External services & keys (dev)
- Groq API key.
- Google OAuth client id/secret (+ GitHub optional).
- Cloudflare R2 / S3 credentials (or local in dev).
- ElevenLabs / Deepgram / Cohere keys only if those swaps are enabled.
- Everything else (Postgres, Redis, Chroma, Judge0) runs locally via docker-compose.

---

## 5. Decision log (append here when deviating)
| Date | Decision | Reason |
|------|----------|--------|
| init | faster-whisper + Piper as defaults | cost/self-host; swap to Deepgram/ElevenLabs if latency/quality forces it |
| init | ChromaDB over Weaviate | simplest for solo build at this scale |
| init | LoRA scorer over scoring with the main LLM | latency + consistency in the real-time loop |
