# PrepPilot AI — API Contracts

**Style:** REST, JSON. FastAPI auto-generates the full OpenAPI spec at `/docs`.
**Auth:** all endpoints except `/auth/*` and `/health` require `Authorization: Bearer <JWT>`.

---

## Conventions

**Error envelope**
```json
{ "error": { "code": "RATE_LIMITED", "message": "You've hit today's practice limit. Try again tomorrow.", "details": {} } }
```

| HTTP code | When |
|---|---|
| 400 | Validation error (bad body, bad file) |
| 401 | Missing or invalid JWT |
| 403 | Not the owner of this resource |
| 404 | Resource not found |
| 409 | Invalid state transition (e.g. answering an already-completed session) |
| 413 | File or answer too large |
| 429 | Rate limit or daily cap exceeded |
| 500 | Unexpected error — safe generic message returned, details logged |
| 502 | LLM failed after retries — graceful degradation |

---

## 1. Auth

### `POST /auth/google`
Exchange a Google OAuth credential for an app JWT.
```json
// request
{ "id_token": "<google-id-token>" }

// response 200
{ "access_token": "<jwt>", "token_type": "bearer",
  "user": { "id": "uuid", "email": "a@x.com", "name": "Aarav" } }
```

### `GET /auth/me`
Returns the current user from the JWT. `401` if invalid.

---

## 2. Resume

### `POST /resume/upload`
Accepts pasted text (core) or a PDF file (E1).
```json
// request (core, JSON)
{ "raw_text": "…", "source": "paste" }

// request (E1) multipart/form-data: file=<resume.pdf>

// response 201
{ "id": "uuid", "source": "pdf", "char_count": 4210, "created_at": "…" }
```
Validation: PDF type and size (≤ 5 MB), malformed PDFs handled → `400` with a clear message.

### `POST /resume/analyze`  *(E1, cuttable)*
```json
// request
{ "resume_id": "uuid", "jd_id": "uuid|null" }

// response 200
{ "summary": "…",
  "extracted_skills": ["SQL", "Product Sense", "A/B testing"],
  "jd_match": {
    "percent": 63,
    "matched": [...],
    "missing": [...],
    "caveat": "Heuristic keyword/requirement coverage — not a real ATS result."
  },
  "suggestions": ["Quantify the impact of the analytics project…"] }
```

---

## 3. Job Description

### `POST /jd/upload`
```json
// request
{ "raw_text": "…", "company_notes": "optional pasted notes" }

// response 201
{ "id": "uuid", "created_at": "…",
  "required_skills": ["Roadmapping", "Stakeholder mgmt"] }
```
Company tips are generated only from the provided inputs — `"ai_generated_from_your_inputs": true` in the response. No external data is fetched.

---

## 4. Interview

### `POST /interview/start`
Creates a session and returns the first question. Checks the daily cap first.
```json
// request
{ "track": "behavioral" | "pm", "resume_id": "uuid|null", "jd_id": "uuid|null" }

// response 201
{ "session_id": "uuid",
  "track": "pm",
  "state": "awaiting_answer",
  "question": { "id": "uuid", "order_index": 1, "text": "…", "is_follow_up": false },
  "progress": { "question": 1, "of": 3 } }
```
`429` if over the daily interview cap.

### `POST /interview/answer`
Submit an answer; get the next turn. Server logic decides follow-up vs. advance vs. complete. Evaluation runs when a question (including its follow-up) finishes.
```json
// request
{ "session_id": "uuid", "question_id": "uuid", "text": "…(≤1800 chars)" }

// response 200 — follow-up
{ "state": "awaiting_answer",
  "question": { "id": "uuid", "is_follow_up": true, "text": "You mentioned X — how did you measure that?" },
  "progress": { "question": 1, "of": 3 } }

// response 200 — question complete, next question
{ "state": "awaiting_answer",
  "feedback": {
    "for_question_id": "uuid",
    "scores": [ { "competency": "structure", "dimension": "STAR completeness", "score": 3 }, … ],
    "improvements": [
      "You said 'we improved the process' — say what YOU did specifically and by how much.",
      "Your Result was missing a number; add the metric you moved."
    ],
    "recommendations": ["Practice the SCQA opener to tighten Structure."]
  },
  "question": { "id": "uuid", "order_index": 2, "is_follow_up": false, "text": "…" },
  "progress": { "question": 2, "of": 3 } }

// response 200 — session complete
{ "state": "completed",
  "feedback": { … },
  "session_id": "uuid",
  "readiness": { "overall": 72.0, "band": "nearly_ready" | "building_baseline", "session_count": 5 } }
```
Errors: `409` if session already completed · `413` if answer over cap · `429` daily cap · `502` if LLM fails after retries (session stays resumable).

### `GET /interview/{session_id}`
Full session report (questions, answers, per-answer scores, feedback, readiness snapshot). Owner-scoped.

---

## 5. Dashboard and Analytics

### `GET /dashboard`
Everything the student dashboard needs. No LLM call.
```json
{ "readiness": { "overall": 72.0, "band": "nearly_ready", "session_count": 6 },
  "competencies": [ { "key": "structure", "name": "Structure", "score": 78 }, … ],
  "trend": [ { "date": "2026-06-01", "overall": 58 }, … ],
  "top_weaknesses": [ { "competency": "depth", "score": 58, "why": "Answers lacked role-specific detail" }, … ],
  "roadmap": {
    "week_of": "2026-07-06",
    "focus": ["Structure", "Depth"],
    "actions": ["Do 2 PM sessions using SCQA", "Add metrics to every STAR answer"]
  },
  "recent_sessions": [ { "id": "uuid", "track": "pm", "date": "…", "overall": 72 }, … ] }
```

### `GET /analytics`
Interview history and aggregate stats.
```json
{ "sessions": [ { "id": "uuid", "track": "behavioral", "date": "…", "overall": 66, "band": "developing" }, … ],
  "totals": { "interviews_completed": 6, "avg_score": 69.4, "readiness_change_30d": 11.0 } }
```

### `GET /metrics`  *(internal observability)*
API latency, AI latency, token usage, request cost, error rate, completion rate, readiness improvement. Self/admin only.

---

## 6. Account and Privacy

### `DELETE /user/data`
Permanently purges the user's resumes, JDs, sessions, questions, answers, scores, and readiness history (cascade). Returns `204`. Only an audit tombstone is kept.

### `GET /health`
Liveness check. No auth required.

---

## 7. Cross-cutting rules

- JWT required on all routes except `/auth/*` and `/health`
- Ownership enforced on every `{id}` route (`403` if not owner)
- Daily caps checked before any LLM call
- Rate limits per endpoint (middleware) → `429`
- Pydantic validation on all inputs; file validation on uploads
- Resume/JD text passed to the model as delimited data; instructions inside are never executed; model output is parsed before storage
- `/interview/answer` rejects re-submission for an already-answered `question_id` (`409`)

## 8. OpenAPI

FastAPI serves the full spec at `/openapi.json` and Swagger UI at `/docs`. This document is the human-readable contract; the generated spec is the source of truth at build time.
