# Praxis — Functional & Non-Functional Requirements

---

## A. Functional requirements (FR)

### Auth & session
- **FR-1** Users sign in via Google OAuth (GitHub optional). No passwords stored.
- **FR-2** A returning user lands on a dashboard listing all prior sessions with status and date.
- **FR-3** Opening a past session shows its full report and per-round breakdown.
- **FR-4** In-progress sessions can be resumed or abandoned; abandoned sessions are marked, not deleted.

### Input & setup
- **FR-5** Users upload a resume (PDF/DOCX) and provide a JD (paste or file).
- **FR-6** Resume and JD are parsed into structured JSON (skills, experience, must-haves, role level).
- **FR-7** The system produces a weighted competency map and a screening fit score with a short rationale.
- **FR-8** A company-style archetype is resolved (from JD or user choice) and parameterizes rounds, rubrics, and persona.

### Interview (rounds)
- **FR-9** The session runs the company profile's round sequence with gating between rounds.
- **FR-10** Every round is conducted over voice: TTS asks, STT captures.
- **FR-11** The candidate can interrupt (barge-in) and ask clarifying questions, request a repeat, or ask for a hint, and receive an **instant, contextual** spoken response — these are not scored as answers.
- **FR-12** Questions adapt to the candidate's running performance (coverage-aware selection, targeted follow-ups).
- **FR-13 (coding)** Approach and pseudocode are discussed by voice; live coding is gated on an approach threshold; code runs against hidden tests; the round score combines approach + code.
- **FR-14 (system design)** Scenario discussed by voice; evaluated on requirements, components, tradeoffs, scalability, data modeling.
- **FR-15 (HR)** Behavioral/motivational questions adapted to resume + company values; scored on communication, structure, specificity, fit.

### Scoring & report
- **FR-16** Each answer is scored on a per-round rubric (0–1 dimensions), grounded against retrieved references.
- **FR-17** Each round produces an aggregate score; the coding round blends approach and code.
- **FR-18** A final report gives an overall band, per-competency scores with evidence quotes, strengths, gaps, and targeted remediation.
- **FR-19** Transcripts, per-turn scores, and audio are retained for review and for the offline eval harness.

---

## B. Non-functional requirements (NFR)

> The voice loop is where this project lives or dies. These targets exist to keep it feeling human.

### Latency (the critical ones)
- **NFR-1** End-of-utterance → start of interviewer speech: **target ≤ 1.2 s, hard ceiling 2 s.** Measure and log every leg (STT finalize, retrieval, reasoning, scoring, TTS first-byte).
- **NFR-2** STT must be **streaming/partial**, not batch-after-silence; end-of-turn detected by VAD + a short silence window (tunable ~600–800 ms), not a fixed long pause.
- **NFR-3** TTS must **stream** (first audio chunk fast); do not wait for full synthesis before playback.
- **NFR-4** Barge-in: detected candidate speech **cancels in-flight TTS within ~150 ms.**
- **NFR-5** Clarification/hint/repeat responses use a lighter, faster path than full answer evaluation (no scoring, minimal retrieval) to feel instant.
- **NFR-6** Scoring must not block the conversational turn: the **fast scorer** (LoRA) runs inline; heavier qualitative critique can run async and reconcile into state.

### Quality of the voice experience
- **NFR-7** No double-talk: the system stops listening for "answer intent" while clearly speaking, but still detects barge-in.
- **NFR-8** Graceful handling of silence ("take your time") and of "can you repeat that" without penalty.
- **NFR-9** Persona/tone consistent within a round (set by company profile), natural pacing, no robotic cadence.

### Reliability & correctness
- **NFR-10** A dropped WebSocket reconnects and restores session state from Redis without losing progress.
- **NFR-11** Sandbox code execution is **isolated, time-limited, and resource-capped**; a candidate's code can never affect the host.
- **NFR-12** Scoring is deterministic enough to be defensible: the same answer scores within a tight band across runs (this is the argument for the fine-tuned scorer).
- **NFR-13** Evaluation is grounded: claims judged against retrieved references; the system should not mark a correct answer wrong due to hallucination.

### Security & privacy
- **NFR-14** OAuth-only auth; tokens in httpOnly/Secure/SameSite cookies; CSRF protection on state-changing routes.
- **NFR-15** Resume/JD/audio are user-private; access scoped to the owning user.
- **NFR-16** Secrets only in env/secret store; never in the repo or client bundle.
- **NFR-17** All provider calls behind adapters so a provider can be swapped without touching graph logic.

### Scalability & cost (right-sized for a portfolio build)
- **NFR-18** Single-node docker-compose is acceptable; design assumes one active session per connection and modest concurrency.
- **NFR-19** Local STT/TTS by default to control cost; provider swaps are config flags, not rewrites.
- **NFR-20** Vector corpora are small enough for ChromaDB on one node; no premature distributed setup.

### Observability
- **NFR-21** Structured logs per turn with the latency breakdown.
- **NFR-22** The eval harness reports: end-to-end spoken-turn latency (p50/p95), scorer agreement (Cohen's κ), retrieval hit-rate / grounding rate, sandbox pass rates. These are your resume metrics — instrument from the start.
