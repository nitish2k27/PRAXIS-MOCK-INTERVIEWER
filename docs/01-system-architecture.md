# Praxis — System Architecture Document

> Working codename: **Praxis** (voice-native adaptive technical interview engine). Rename freely.
> Status: pre-implementation. This document is the source of truth for system flow, data, RAG/LLM usage, rounds, and scoring.

---

## 1. What Praxis is (one paragraph)

Praxis is a single-player, voice-native mock-interview engine. A user logs in, uploads a resume and a target job description (JD), and Praxis runs a realistic, multi-round interview over voice — a coding round (approach → pseudocode → live coding), a system-design round, and an HR/behavioral round — adapting questions to the candidate and the company style, allowing two-way interaction (the candidate can ask clarifying questions and get instant answers), and producing a structured cross-round report at the end. Every session and report is persisted, so a returning user sees their full history.

It is **not** a generic chatbot and **not** a two-sided SaaS. The intelligence lives in adaptive question planning, RAG-grounded evaluation, and a fine-tuned scoring model.

---

## 2. High-level component map

```
                         ┌──────────────────────────────┐
                         │        React + Vite SPA        │
                         │  auth · upload · voice client  │
                         │  Monaco editor · history view  │
                         └───────────────┬────────────────┘
                                         │ HTTPS + WSS
                         ┌───────────────▼────────────────┐
                         │          FastAPI backend         │
                         │  REST (CRUD/auth) + WebSocket     │
                         │  LangGraph orchestrator           │
                         └──┬─────┬─────┬─────┬─────┬────────┘
                            │     │     │     │     │
        ┌───────────────────┘     │     │     │     └───────────────────┐
        ▼                         ▼     ▼     ▼                         ▼
 ┌────────────┐         ┌──────────────┐  ┌──────────────┐      ┌──────────────┐
 │ Voice layer │         │  Retrieval    │  │  Inference    │      │  Persistence  │
 │ STT/VAD/TTS │         │  Chroma +     │  │  Groq LLM +   │      │  Postgres +   │
 │             │         │  reranker     │  │  LoRA scorer  │      │  Redis + R2   │
 └────────────┘         └──────────────┘  └──────────────┘      └──────────────┘
```

Three logical planes run through every round:
- **Voice plane** — streaming STT in, TTS out, over a WebSocket, with VAD, end-of-turn detection, and barge-in.
- **Retrieval plane** — hybrid search (BM25 + dense) + reranking over four corpora (question bank, concept references, system-design patterns, company styles).
- **Reasoning plane** — Groq LLM for generation and grounded critique; a fine-tuned LoRA scorer for fast, consistent rubric scoring; a small intent classifier for two-way interaction.

---

## 3. End-to-end flow (login → report)

### 3.1 Authentication & session bootstrap
1. User clicks "Sign in" → OAuth 2.0 / OIDC redirect to Google (GitHub optional).
2. On callback, backend verifies the ID token, upserts a `users` row keyed on `(oauth_provider, oauth_sub)`, and issues an app JWT (short-lived access + refresh) stored in httpOnly cookies.
3. The SPA loads the user's dashboard: prior `interview_sessions` and their `reports` are fetched from Postgres so a returning user immediately sees their history.

### 3.2 Input: resume + JD
1. User uploads a resume (PDF/DOCX) and pastes/uploads a JD.
2. Files go to object storage (R2/S3); a `resumes` row and `job_descriptions` row are created with the file URL.
3. **Parsing (LLM extraction step):** the resume is text-extracted (pdfplumber/docx2txt), then an LLM call converts both resume and JD into structured JSON — skills, experience, projects, seniority signals (resume); required competencies, must-haves, role level (JD). Stored as `parsed_json` on each row.
4. **Competency mapping:** the JD's required competencies are reconciled with the resume's signals into a weighted competency map, which seeds the session state (see §5).

### 3.3 Screening (round 0, gate)
1. Embed the resume and JD; compute a fit score from (a) dense similarity and (b) an LLM rubric pass over coverage of must-haves.
2. Write `interview_sessions.fit_score`. A configurable threshold decides whether the candidate "proceeds" — in practice we always proceed (it is practice) but the score and a short rationale are recorded and shown in the report.

### 3.4 Company style resolution
The user (or the JD) maps to one of 2–3 **company-style archetypes** (e.g., "FAANG-structured," "startup-pragmatic," "enterprise-behavioral"). The archetype's profile parameterizes: which rounds run and in what order, the rubric weights per round, question-corpus filters, and the interviewer persona/tone used by TTS.

### 3.5 The interview (round controller → per-round loop)
The **round controller** is a top-level LangGraph state machine that sequences rounds per the company profile and gates between them on round score. Each round is itself the per-round interview loop:

```
Planner → Ask(voice) → Evaluator → Router ──▶ Probe ──┐
   ▲                                   │               │
   └───────────── next topic ──────────┘◀──────────────┘
                                        └──▶ Report (when round complete)
```

Per-round loop (one turn):
1. **Planner** selects the next competency to probe (coverage-aware), retrieves a candidate question via hybrid RAG, and drafts it.
2. **Ask (voice)** speaks the question (TTS) and captures the answer (streaming STT + end-of-turn).
3. **Listen/intent** classifies the incoming utterance: `answer | clarification | repeat | hint_request | done`. Non-answers are handled instantly (two-way interaction) and do not consume the scoring path.
4. **Evaluator** retrieves the authoritative concept reference (RAG grounding), runs the LoRA scorer for rubric dimensions, and produces a grounded critique.
5. **Router** (conditional edge) decides: probe deeper, move to next competency, or end the round.
6. **Probe** generates a targeted follow-up grounded in the specific gap, then loops back to Ask.

Round-specific behavior is described in §4.

### 3.6 Report
When the controller terminates (all rounds done, time budget hit, or early exit), the **report node** reads accumulated state — no new retrieval/scoring — and synthesizes a cross-round report (overall band, per-competency scores with evidence quotes, strengths, gaps, remediation). It is persisted to `reports` and rendered in the SPA. Audio clips, transcripts, and per-turn scores are stored for the offline eval harness.

---

## 4. The rounds (mechanics, RAG, LLM, scoring)

> Removed from scope: a standalone theory/MCQ round (it added CRUD without ML value). All rounds are voice-native and reuse the same engine.

### 4.1 Coding round (multi-stage sub-graph)
A round that is itself a gated state machine.

- **Stage A — Approach discussion (voice):** interviewer poses the problem; candidate explains strategy verbally. Two-way: candidate may ask about constraints (input size, duplicates, etc.). Scored on strategy soundness, complexity awareness, edge cases.
- **Stage B — Pseudocode discussion (voice):** candidate walks through pseudocode; interviewer probes and gives bounded hints. Updates the approach score.
- **Gate:** if the accumulated approach score clears ~0.55 (configurable), advance to live coding. If not, give bounded hints; if still stuck, **early-exit** the round with a partial score.
- **Stage C — Live coding (voice + code):** candidate writes code in the Monaco editor. The editor streams contents over the WebSocket (debounced); the agent holds the current code in state, runs lightweight checks (compiles? diverging from stated approach? obvious complexity issue?), and may interject over voice. Two-way interaction continues.
- **Stage D — Combined scoring:** `round_score = w_a · approach_score + w_c · code_score`, where `code_score` blends hidden-test pass rate (executed in a sandbox) with a code-quality rubric and consistency with the stated approach. Weights come from the company profile.

RAG here: question selection from the coding question bank (filtered by role/difficulty/company, anti-repetition); concept grounding for hints and approach evaluation. LLM here: problem posing, hint/clarification responses, qualitative critique, interject decisions. Scorer: rubric dimensions for approach and code quality. Sandbox: Judge0 for objective correctness.

**Tiering:** MVP = stages A/B + gate + submit-then-run scoring (no live monitoring). Stretch = live code streaming + mid-coding interjection.

### 4.2 System-design round (scenario, voice)
- Scenario prompt ("design a rate limiter for our API"). Pure voice discussion: requirements, components, data model, tradeoffs, scaling.
- Two-way: candidate asks about scale/constraints; interviewer answers ("assume 10M users").
- RAG: retrieve canonical design patterns/components for the scenario from the system-design corpus; ground the evaluation against expected dimensions (requirements gathering, component coverage, tradeoff reasoning, scalability, data modeling).
- Scoring: rubric dimensions, no execution. Lowest-complexity round; reuses the engine almost entirely. Optional stretch: a lightweight sketch canvas.

### 4.3 HR / behavioral round (voice)
- Behavioral and motivational questions adapted to resume + company values (e.g., STAR-style prompts, leadership-principle probes for enterprise archetype).
- RAG: company-style corpus for value-aligned prompts; resume signals for tailored questions.
- Scoring: communication, structure (STAR completeness), authenticity/specificity, role fit. Simplest, fullest fit — **build this round first.**

---

## 5. The shared state object (the backbone)

A single LangGraph state object lives across the whole session. Every node reads and writes it; the report is its synthesis. Conceptual shape:

```jsonc
{
  "session_id": "s_8f2a",
  "user_id": "u_123",
  "company_profile_id": "faang_structured",
  "config": { "max_questions_per_round": 8, "time_budget_min": 45, "probe_depth_max": 2 },
  "resume": { "skills": [...], "projects": [...], "seniority": "entry" },
  "jd": { "must_haves": [...], "role": "Backend Engineer" },
  "fit_score": 0.71,
  "competencies": [
    { "id": "db_indexing", "weight": 0.9, "covered": false, "score": null }
  ],
  "rounds": [
    {
      "type": "coding",
      "status": "in_progress",
      "stage": "live_coding",
      "approach_score": 0.62,
      "code": { "language": "python", "text": "...", "tests": { "passed": 7, "total": 10 } },
      "turns": [ { "seq": 1, "speaker": "candidate", "intent": "answer",
                   "transcript": "...", "scores": {...}, "refs": ["btree_11"] } ],
      "round_score": null
    }
  ],
  "report": null
}
```

In-progress state is held in **Redis** (fast read/write during the live session) and **persisted to Postgres** on round/session completion.

---

## 6. Where RAG is used (complete map)

| # | Location | Corpus | Why it is load-bearing |
|---|----------|--------|------------------------|
| 1 | Screening fit score | resume/JD embeddings | dense + rubric coverage of must-haves |
| 2 | Question selection (all rounds) | question bank (role/company/difficulty tagged) | coverage-aware, anti-repetition, calibrated selection |
| 3 | Answer evaluation grounding | concept reference corpus | verify claims, target follow-ups, reduce eval hallucination |
| 4 | System-design grounding | design-pattern corpus | score discussion against canonical components/tradeoffs |
| 5 | Company style | company-style corpus | persona, question emphasis, rubric weights |

All retrieval is **hybrid (BM25 + dense) + cross-encoder rerank**. Chunking: reference docs chunked ~300–500 tokens with overlap; question-bank items stored atomically with metadata for filtering.

---

## 7. Where the LLM and fine-tuned models are used (complete map)

| Step | Model | Output |
|------|-------|--------|
| Resume/JD parsing | Groq LLM | structured JSON |
| Question/probe generation | Groq LLM | next utterance text |
| Clarification / hint / repeat | Groq LLM | instant spoken response |
| Grounded critique + probe decision | Groq LLM | findings + router signal |
| Report synthesis | Groq LLM | structured report |
| Rubric scoring (per turn / code quality) | **fine-tuned LoRA scorer** | rubric dimension scores |
| Turn-intent classification | small classifier (or prompt at MVP) | `answer/clarification/repeat/hint/done` |

**Why fine-tune the scorer (not the interviewer):** per-turn LLM scoring is too slow for the real-time voice loop and inconsistent run-to-run. A distilled LoRA scorer (trained on strong-LLM-teacher labels + a human-labeled validation slice) gives fast, stable rubric scores. Report agreement (Cohen's κ) and inference latency in the eval harness.

---

## 8. Scoring mechanisms (summary)

- **Per turn:** LoRA scorer → rubric dimensions (0–1) on the answer transcript, grounded against retrieved references.
- **Per round:** weighted aggregate of turn scores by competency. Coding round additionally blends approach + code (tests + quality).
- **Gates:** screening fit threshold (recorded); coding approach ≥ ~0.55 to enter live coding; round score threshold to advance (company-configurable).
- **Final report:** cross-round synthesis → overall band + per-competency (score + evidence quote) + strengths + gaps + targeted remediation.

---

## 9. Databases & storage required

| Store | Tech | Holds |
|-------|------|-------|
| Relational | PostgreSQL (Neon) | users, resumes, JDs, sessions, rounds, turns, code artifacts, reports, company profiles |
| Vector | ChromaDB | 4 corpora: question bank, concept refs, design patterns, company styles |
| Cache / live state | Redis | in-progress session state, pub/sub, rate limits |
| Object storage | Cloudflare R2 / S3 | resume/JD files, audio clips |

### 9.1 Relational schema (core tables)

```sql
users(id PK, oauth_provider, oauth_sub, email, name, created_at)            -- UNIQUE(oauth_provider, oauth_sub)
resumes(id PK, user_id FK, file_url, parsed_json, created_at)
job_descriptions(id PK, user_id FK, raw_text, file_url, parsed_json, created_at)
company_profiles(id PK, name, round_mix_json, rubric_weights_json, persona_json)   -- seed data
interview_sessions(id PK, user_id FK, resume_id FK, jd_id FK, company_profile_id FK,
                   status, config_json, fit_score, started_at, completed_at)
rounds(id PK, session_id FK, type, status, stage, score, rubric_json,
       started_at, completed_at)
turns(id PK, round_id FK, seq, speaker, transcript, intent,
      retrieval_refs_json, scores_json, audio_url, created_at)
code_artifacts(id PK, round_id FK, language, code_text, test_results_json, created_at)
reports(id PK, session_id FK, overall_band, per_competency_json,
        strengths_json, gaps_json, remediation_json, created_at)
```

Indexes: `interview_sessions(user_id, started_at)` for history; `turns(round_id, seq)`; `rounds(session_id)`.

---

## 10. Real-time / WebSocket contract (sketch)

One WSS connection per active interview. Message types:
- client→server: `audio_chunk`, `code_update`, `control` (pause/skip/repeat)
- server→client: `tts_chunk`, `interviewer_text`, `state_update`, `round_transition`, `report_ready`

Audio streams continuously both ways; barge-in cancels in-flight TTS. The LangGraph orchestrator subscribes to Redis for state changes during the session.

---

## 11. Non-goals (explicit)
- No two-sided HR/recruiter platform, no question authoring by third parties.
- No billing, no multi-tenant org management.
- No standalone MCQ theory round.
- These keep scope inside a 6–10 week solo build.
