# Praxis — Build Plan

> Build order is chosen so the hardest piece (the coding round) comes last and you always have a complete, demoable system before starting it. Each phase ends with something you can run.

---

## Guiding rule

Build **one full round end-to-end first** (HR), proving the entire pipeline on the simplest round. Then add cheap rounds, then the controller, then the expensive coding round — internally tiered. If you run out of time after Phase 4, you still ship a strong project; everything after is roadmap.

---

## Phase 0 — Foundations (week 1)

**Goal:** the skeleton runs, you can log in, upload, and store.

Modules:
- `infra/` docker-compose: Postgres, Redis, Chroma, Judge0, api, web. App boots with one command.
- `auth/` OAuth 2.0 (Google) + JWT in httpOnly cookies; `users` upsert; protected route guard.
- `db/` SQLAlchemy models + Alembic migrations for all core tables (§9 of architecture doc).
- `web/` shell: login, dashboard (empty history), upload form.
- Upload + storage: resume/JD to R2/S3; rows created.

**Done when:** a user signs in, uploads a resume + JD, and rows + files exist; revisiting shows their (empty) session list.

---

## Phase 1 — Ingestion & screening (week 1–2)

**Goal:** inputs become structured state.

Modules:
- `ingestion/` text extraction (pdfplumber/docx2txt) → LLM structured extraction → `parsed_json`.
- Competency mapping: JD must-haves × resume signals → weighted competency map.
- `retrieval/` Chroma bootstrap + embedding + screening fit score (dense similarity + LLM coverage rubric).
- Seed `company_profiles` (2–3 archetypes).

**Done when:** uploading produces a competency map, a fit score, and a resolved company profile, all persisted and visible.

---

## Phase 2 — Voice layer (week 2–3) — *the hard infra, do it early*

**Goal:** a real spoken round-trip with good turn-taking.

Modules:
- `voice/stt` faster-whisper streaming + silero-vad end-of-turn.
- `voice/tts` Piper adapter (interface so ElevenLabs swaps in).
- `ws/` WebSocket: continuous audio in/out, barge-in (cancel in-flight TTS), `audio_chunk`/`tts_chunk` protocol.
- Latency budget instrumentation (measure each leg).

**Done when:** you can hold a spoken back-and-forth with sub-second perceived response and interrupt the voice mid-sentence.

---

## Phase 3 — HR round end-to-end (week 3–4) — *the whole pipeline on one round*

**Goal:** a complete, scored, voice interview round with a report.

Modules:
- `orchestrator/` per-round LangGraph loop: Planner → Ask → Evaluator → Router → Probe.
- `orchestrator/intent` turn-intent handling (prompt-based at MVP): `answer/clarification/repeat/hint/done`; non-answers answered instantly (two-way interaction).
- `retrieval/` hybrid (BM25 + dense) + bge reranker; HR question bank + company-style corpus.
- `scoring/` rubric scoring — **prompted LLM scorer at MVP** (swap to LoRA in Phase 6); HR rubric (communication, structure/STAR, specificity, fit).
- `reports/` cross-round (here single-round) report synthesis + persistence + SPA render.

**Done when:** a full HR round runs over voice, handles clarifications, scores per rubric, and saves a report a returning user can re-open.

---

## Phase 4 — Round controller + system-design round (week 4–6)

**Goal:** a real multi-round funnel with a second round (cheap, reuses the engine).

Modules:
- `orchestrator/controller` top-level LangGraph state machine: sequences rounds per company profile, gates on round score, handles early exit.
- `rounds/system_design` scenario prompts; design-pattern corpus; rubric (requirements, components, tradeoffs, scalability, data modeling); two-way constraint answers.
- Report node upgraded to cross-round synthesis.

**Done when:** screening → system-design → HR runs as one gated session producing one combined report.

---

## Phase 5 — Coding round MVP (week 6–8) — *tier it*

**Goal:** approach-gated coding round with combined scoring, no live monitoring yet.

Modules:
- `rounds/coding` sub-graph: Approach → Pseudocode → Gate(≥~0.55) → (live) Coding → Combined score. Early-exit branch.
- `web/` Monaco editor integrated into the coding round UI.
- `sandbox/` Judge0 adapter: run hidden tests on submit; `code_score` = test pass rate + quality rubric + approach consistency.
- Combined scoring: `round_score = w_a·approach + w_c·code`.

**Done when:** the candidate discusses approach, gets gated, codes, submits, tests run, and a blended score lands in the report.

---

## Phase 6 — Fine-tuned scorer + eval harness (week 8–9)

**Goal:** replace prompted scoring with the distilled model and prove it with numbers.

Modules:
- `ml/` dataset construction: collect Q–A pairs (synthetic + your own transcripts), label rubric dimensions with a strong-LLM teacher + a human-labeled validation slice.
- LoRA training on Colab (`peft`/`trl`), eval against held-out (Cohen's κ vs human/teacher).
- `scoring/` swap the prompted scorer for the LoRA scorer behind the same interface; measure inference latency.
- Eval harness: end-to-end spoken-turn latency, scorer agreement, retrieval hit-rate / grounding rate.

**Done when:** the scorer interface is backed by your fine-tuned model and you have three headline metrics.

---

## Phase 7 — Stretch (week 9–10, optional)
- Live code monitoring + mid-coding interjection (the wow feature).
- Turn-intent as a trained classifier (replacing the prompt).
- System-design sketch canvas.
- Additional company archetypes.

---

## What each top-level module must contain (checklist)

- `orchestrator/` — graph definitions (controller + per-round), node implementations, the Pydantic state model, conditional-edge logic. No provider SDK calls.
- `voice/` — `stt`, `vad`, `tts` adapters behind interfaces; barge-in logic; latency instrumentation.
- `retrieval/` — Chroma client, ingestion/chunking scripts per corpus, hybrid search, reranker, metadata filters.
- `scoring/` — scorer interface, prompted impl (MVP) + LoRA impl, rubric definitions per round.
- `rounds/` — one module per round; round-specific question sources, rubrics, and (coding) the sub-graph + sandbox.
- `auth/` — oauth flow, jwt issue/verify, cookie handling, route guards.
- `db/` — models, migrations, repositories (no raw SQL in nodes).
- `ws/` — connection lifecycle, message protocol, Redis pub/sub bridge.
- `reports/` — synthesis + persistence + serialization for the SPA.
- `ml/` — dataset, training, eval (lives outside the serving path).
