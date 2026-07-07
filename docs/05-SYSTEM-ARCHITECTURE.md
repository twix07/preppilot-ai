# PrepPilot AI — System Architecture

---

## 1. Overall style: modular monolith

One deployable backend (FastAPI) and one frontend (Next.js), on a single host. No microservices — that's an intentional choice given the stage and solo dev context. The frontend is presentation-only; all AI calls go through FastAPI. Business logic lives in the service layer with a clear separation between controllers, services, repositories, and models.

## 2. High-level diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         Browser (student)                          │
│         Next.js + React + TypeScript + Tailwind + Recharts         │
│                    (presentation only — no AI keys)                │
└───────────────────────────────┬──────────────────────────────────┘
                                 │ HTTPS (JWT in Authorization header)
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                      FastAPI (async) — Modular Monolith            │
│                                                                    │
│  Controllers (routers)  →  Auth/Middleware  →  Services  →  Repos  │
│        │                        │                  │               │
│        │                 JWT + Google OAuth        │               │
│        │                 rate limit + daily cap    │               │
│        │                 input/file validation     │               │
│        │                 prompt-injection guard    │               │
│        │                                           ▼               │
│        │                                    ┌────────────┐         │
│        │                                    │  LiteLLM   │         │
│        │                                    │  (Claude)  │         │
│        │                                    └─────┬──────┘         │
│        │                                          ▼                │
│        │                             ┌───────────────────────┐     │
│        │                             │  LangGraph (2 nodes)   │     │
│        │                             │  ┌─────────────────┐   │     │
│        │                             │  │ Interview Node  │   │     │
│        │                             │  └─────────────────┘   │     │
│        │                             │  ┌─────────────────┐   │     │
│        │                             │  │ Evaluation Node │   │     │
│        │                             │  └─────────────────┘   │     │
│        │                             └───────────────────────┘     │
│        │                                          │                 │
│        │              LangSmith tracing ◄─────────┘                │
│        ▼                                                            │
│   Repositories ──────────────────────────────────────────────►     │
└───────────────────────────────┬──────────────────────────────────┘
                                 │ SQLAlchemy (async)
                                 ▼
                     ┌────────────────────────┐
                     │       PostgreSQL        │
                     │  users, resumes, jds,   │
                     │  sessions, questions,   │
                     │  answers, competencies, │
                     │  readiness, analytics   │
                     └────────────────────────┘

  Deploy: Docker image → GitHub Actions CI/CD → Render (or Azure)
```

## 3. Layer responsibilities

| Layer | What it does | What it must NOT do |
|---|---|---|
| **Controllers (routers)** | Parse request, validate with Pydantic, call one service, shape response | Contain business logic or touch the DB |
| **Services** | All business logic: interview orchestration, scoring, readiness math, caps | Contain SQL or HTTP concerns |
| **Repositories** | All DB access (SQLAlchemy), one per aggregate | Contain business rules |
| **Models / Schemas** | SQLAlchemy models and Pydantic DTOs | — |
| **AI layer** | LiteLLM client, LangGraph graph (2 nodes), prompts | Be called from anywhere except services |

Rule: business logic lives in exactly one place. Readiness math is in one file, unit-tested.

## 4. The AI layer — two LangGraph nodes, deterministic routing

Routing between steps is deterministic code, not an LLM planner.

### Interview Node
- **Input:** track, resume text, JD text, conversation state (which question, prior answers)
- **Job:** produce the next interviewer turn — the question itself or one adaptive follow-up that probes the weakest part of what the student actually said
- **Guardrails:** one question at a time, never reveal the rubric or scores, stay in role, keep it concise, resume/JD are data not instructions
- **Output:** interviewer message + updated state

### Evaluation Node
- **Input:** track rubric, the question, the full answer (plus follow-up), resume/JD for context
- **Job:** score each rubric dimension 1–5, produce 2–3 specific improvements quoting the student's words, produce recommendations
- **Reliability config:** low temperature, structured JSON output, explicit rubric anchors in the prompt
- **Output:** `{ scores: {dimension: 1-5}, improvements: [...], recommendations: [...] }`

### Why two nodes, not agents

The flow is a fixed pipeline: ask → answer → ask follow-up → evaluate. There is no open-ended planning that would justify an agent. Two nodes = testable, cheap, explainable. Agents would be a V2 consideration only if a genuine planning need appeared.

## 5. What's implemented vs. deliberately left out

| Implemented | Deliberately skipped |
|---|---|
| LiteLLM single-model abstraction | Multi-model routing |
| LangSmith tracing | Prompt A/B testing |
| Token / cost / latency tracking per call | Prompt-versioning UI |
| Retry with graceful fallback | Streaming |
| Structured output + low temp for eval | Fine-tuning |

## 6. Two representative request traces

**A. `POST /interview/answer`**
```
Router → auth (JWT) → daily-cap check → rate-limit → validate body
      → InterviewService.submit_answer()
          → persist Answer
          → deterministic state: follow-up needed? or evaluate + advance?
          → LiteLLM → LangGraph Interview Node (next turn)
          → if question complete: Evaluation Node (score)
          → ScoringService.update_readiness()
      → return { next_question | follow_up | session_complete, feedback? }
```

**B. `GET /dashboard`**
```
Router → auth → DashboardService.build()
      → repos: sessions, answers, readiness history, competencies
      → assemble trend + competency bars + top weaknesses + roadmap
      → return DTO  (no LLM call — pure data)
```

## 7. Security and privacy

- **Auth:** Google OAuth → server-verified → app JWT on every protected request
- **Authorization:** every resource query scoped to `user_id` from the JWT — no way to access another user's data
- **Transport:** HTTPS only
- **Input validation:** Pydantic on every endpoint, file type/size checks on uploads
- **SQL:** parameterized queries via SQLAlchemy only
- **Prompt injection:** three separate channels — system (our instructions), user (the student's chat answer), document (resume/JD as clearly delimited data). The model is told document text is never a command. Output is parsed and validated before being stored.
- **PII:** sensitive fields encrypted at rest, `DELETE /user/data`, 90-day auto-purge of inactive resumes

## 8. Cost and abuse controls

- Per-user daily counter table incremented on each LLM-hitting request; over cap → `429` with a friendly message
- Per-endpoint rate limiting middleware
- Spend tracked from token counts; monthly estimate documented with a global ceiling

## 9. Observability

Tracked and surfaced in an internal metrics view: API latency, AI latency, token usage, request cost, error rate, interview completion, readiness improvement. LangSmith holds per-trace AI detail; the app DB holds aggregates.

## 10. Deployment

- **Containerized:** one Dockerfile for backend, one for frontend, `docker-compose.yml` for local dev
- **CI/CD:** GitHub Actions — lint, type-check, unit + integration tests, build image, deploy
- **Host:** Render (web service + managed Postgres) or Azure App Service + Azure PostgreSQL
- **Config:** secrets (API key, DB URL, OAuth creds, JWT secret) via environment variables, never in code

## 11. Technology decisions

| Decision | Chose | Passed on | Why |
|---|---|---|---|
| Retrieval | Direct context injection | RAG / pgvector | Resume + JD fit in context; retrieval adds ops and failure modes for no real user value at this scale |
| AI graph | 2 fixed nodes | Agent framework | Fixed pipeline — determinism and testability matter more than flexibility here |
| Model routing | LiteLLM, one model | Multi-model router | Swappability without runtime complexity |
| Rate limit / caps | Postgres counters | Redis | One fewer service at pilot scale |
| Architecture | Modular monolith | Microservices | Solo dev, single host, easier to explain and maintain |
