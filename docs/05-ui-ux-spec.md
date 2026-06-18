# Praxis — Minimal UI/UX Specification

> Deliberately minimal. Goal: enough structure to build a functional product now; you'll spend 1–2 days polishing after the system works. Function over finish.

---

## Principles
- One primary action per screen. No clutter.
- The interview screen is **voice-first** — minimal on-screen reading while talking.
- Always show interview state (which round, progress, mic status) so the user is never lost.
- Neutral, calm visual tone; this is a high-pressure simulation, don't add visual stress.

---

## Screens

### 1. Sign-in
- App name + one line ("Practice real technical interviews by voice").
- "Continue with Google" (and "Continue with GitHub" if enabled). Nothing else.

### 2. Dashboard (post-login)
- Header: app name, user avatar/menu (sign out).
- Primary CTA: **"Start a new interview."**
- Below: **history list** — each prior session as a card: company archetype, date, overall band, status. Click → report.
- Empty state: a single prompt to start the first interview.

### 3. New interview setup
- Step 1: upload resume (drag/drop), paste/upload JD.
- Step 2: confirm/pick company-style archetype (2–3 options with one-line descriptions).
- Show parsed summary + fit score + the round sequence that will run, then **"Begin."**

### 4. Interview screen (the core)
Layout: voice-first, single column, calm.
- **Top bar:** current round name + round progress (e.g., "Round 2 of 3 · System Design"), elapsed/remaining time, mic indicator.
- **Center:** a single live "interviewer is speaking / listening / thinking" state indicator (waveform or simple animated dot). The current question shown as text under it (for accessibility / re-reading), nothing more.
- **Controls (minimal):** mute/unmute mic, "repeat question," "I'm done with this answer," pause. These map to control messages, not new UI flows.
- **Coding round only:** the center splits — Monaco editor on one side, the voice indicator + problem statement on the other. A language selector and a "submit for tests" button. Test results appear inline after submit.
- **Two-way interaction:** when the user asks a clarifying question, the interviewer's spoken reply plays; optionally show the reply text briefly. No modal, no interruption of flow.

### 5. Report
- Header: overall band + company archetype + date.
- Per-round sections (collapsible): round score, rubric dimensions, 1–2 evidence quotes from the transcript.
- "Strengths" and "Gaps" as short lists.
- "What to study next" (remediation) as short actionable items.
- Link to replay transcript/audio per round.
- For coding round: show the submitted code + test pass summary alongside the approach notes.

---

## Interaction & feedback rules
- Mic permission requested once, clearly, before the interview begins.
- Visible, immediate feedback when the system is listening vs speaking vs thinking (this is what makes latency feel acceptable).
- Barge-in must visibly cut off the interviewer (the waveform/indicator stops) so the user trusts they can interrupt.
- Errors (dropped connection, mic lost) surface as a small non-blocking banner with a reconnect action; never lose progress.

---

## Out of scope for MVP UI (polish later)
- Theming, animations beyond the state indicator, onboarding tour.
- Detailed analytics/visualizations of progress over time.
- Mobile-optimized layout (build desktop-first; it's a desktop activity).
- Accessibility beyond basics (keyboard focus, captions of the spoken question) — keep the basics, defer the rest.

---

## Minimal component inventory (for build)
- `AuthButton`, `DashboardHeader`, `SessionCard`, `UploadForm`, `ArchetypePicker`, `SetupSummary`, `InterviewStage` (voice indicator + question), `InterviewControls`, `CodePanel` (Monaco + tests), `ReportView`, `RoundSection`, `ConnectionBanner`.
