# PrepPilot AI — User Flows

Flows are split into core (must ship) and extensions (cuttable). Each step notes the API it hits — see [08-API-CONTRACTS.md](08-API-CONTRACTS.md) for the full contracts.

---

## Flow 0 — Sign in / Onboarding

```
Land on the home page
  → "Sign in with Google"                     [Google OAuth]
  → Backend verifies token, issues JWT        [POST /auth/google]
  → First time: create User row
  → Redirect to Dashboard (empty state)
```

Empty-state dashboard shows one CTA: **"Add your resume or a job description to start your first interview."**

---

## Flow 1 — The core loop

This is the whole product in one loop. Everything else waits until this works.

```
1. Add context
   Paste resume text                    [POST /resume/upload]
   Paste JD text                        [POST /jd/upload]
        │
        ▼
2. Start interview
   Pick track: Behavioral or PM
   Confirm which resume + JD to use     [POST /interview/start]
   → Server creates a session, Interview Node returns Question 1
        │
        ▼
3. Answer loop  (×3 questions)
   Read question
   Type answer (length-capped)          [POST /interview/answer]
   → Interview Node returns one adaptive follow-up
   Answer the follow-up                 [POST /interview/answer]
   → Next question (or end after Q3)
        │
        ▼
4. Evaluation
   Evaluation Node scores each answer 1–5 per rubric dimension
   Feedback quotes the student's own words + gives recommendations
        │
        ▼
5. Readiness update
   Per-answer scores → competency scores (recency-weighted)
   → Readiness score recomputed and stored
        │
        ▼
6. Dashboard
   Interview report for this session        [GET /dashboard]
   Readiness score + band (or "Building baseline")
   Competency bars · top weaknesses · trend line · roadmap
        │
        ▼
7. Repeat → trend builds → student hits 5 sessions → band appears
```

### The interview turn state machine

```
[SESSION_CREATED]
   → Interview Node asks Q1
[AWAIT_ANSWER Q1]        ──answer──►  Interview Node asks Q1 follow-up
[AWAIT_ANSWER Q1-FU]     ──answer──►  (evaluate Q1) → Interview Node asks Q2
[AWAIT_ANSWER Q2]        ──answer──►  Q2 follow-up
[AWAIT_ANSWER Q2-FU]     ──answer──►  (evaluate Q2) → Q3
[AWAIT_ANSWER Q3]        ──answer──►  Q3 follow-up
[AWAIT_ANSWER Q3-FU]     ──answer──►  (evaluate Q3) → [SESSION_COMPLETE]
                                        └→ finalize readiness, build report
```

Important guardrails:
- One question at a time. One follow-up per question. The rubric is never shown during the interview.
- If an answer is empty or off-topic, the Interview Node asks for a real attempt. That turn doesn't count as a scored answer.
- Deterministic code (not the LLM) decides when to advance and when to trigger evaluation.

---

## Flow 2 — Returning student

```
Sign in → Dashboard shows current readiness + trend
  → "Start interview" (resume + JD pre-filled from last time, editable)
  → Core loop → readiness updates → trend extends
```

---

## Flow 3 — Skill gap and roadmap

```
After a session (or from the Dashboard):
  Rubric weaknesses (low competency scores)
  + JD required skills (if a JD is attached)
        │
        ▼
  Skill-gap list (missing or weak skills, ranked)
        │
        ▼
  Weekly learning roadmap
  ("This week: focus on Structure and Depth. Try 2 PM sessions using the SCQA opener.")
  Personalized recommendations based on specific low scores
```

---

## Flow 4 — Delete My Data

```
Settings → "Delete my data"
  → Confirmation modal (this is permanent)
  → DELETE /user/data
  → Purges resumes, JDs, sessions, answers, scores — everything
  → Signs out
```

---

## Flow E1 — Resume Intelligence (extension, cuttable)

```
Upload resume PDF                        [POST /resume/upload — multipart]
  → Validate file type and size, parse text, handle bad PDFs gracefully
  → Extract skills + generate summary    [POST /resume/analyze]
  → If JD is present: JD match %  (heuristic, labeled with caveat)
  → Improvement suggestions
```

---

## Flow E2 — Job Intelligence (extension, cuttable)

```
Add JD text + optional pasted company notes    [POST /jd/upload]
  → Extract required skills
  → Compare against resume skills
  → Company-specific prep tips generated ONLY from JD text + pasted notes
    (labeled "AI-generated from your inputs" — no external data fetched)
```

---

## Rules that apply everywhere

- **Daily caps:** every LLM-hitting step checks the per-user cap first. Over limit → friendly message ("you've hit today's practice limit — come back tomorrow").
- **Rate limiting:** per-endpoint limits return `429` with a clear message.
- **Untrusted documents:** resume and JD text go to the model as delimited data in a separate channel. Instructions inside a document are never executed.
- **No dead ends:** every error state has a recovery path and a human-readable message.
