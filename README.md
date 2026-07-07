# PrepPilot AI — Career Intelligence Platform

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://preppilot-ai.vercel.app)
[![Backend API](https://img.shields.io/badge/api-render-blue)](https://preppilot-backend.onrender.com/docs)
[![CI](https://github.com/twix07/preppilot-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/twix07/preppilot-ai/actions/workflows/ci.yml)

> **[Live demo →](https://preppilot-ai.vercel.app)** · Sign in with `demo@preppilot.ai` (no password) to explore the product.

Know if you're actually interview ready. Practice against your resume and the job description, get feedback that quotes your own answers, and watch a real readiness score improve over time.

I built this because I ran mock interview sessions at our college's Training & Placement Cell and Consulting & Analytics Club (300+ members). Mentor prep doesn't scale, feedback is inconsistent, and students never really know if they're ready. PrepPilot is my attempt to fix that.

Both Phase 1 (core loop) and Phase 2 (resume/job intelligence, analytics) are built and tested — 24 backend tests green, frontend builds clean, Alembic migrations round-trip. The full loop — resume + JD → adaptive interview → rubric evaluation → readiness update → dashboard — works end-to-end.

---

## Table of contents
- [What it does](#what-it-does)
- [Readiness score formula](#readiness-score-formula)
- [Architecture](#architecture)
- [Quick start](#quick-start)
- [Deploying (Render + Vercel)](#deploying-render--vercel)
- [Running the tests](#running-the-tests)
- [AI evaluation](#ai-evaluation)
- [Cost](#cost)
- [Privacy and data retention](#privacy-and-data-retention)
- [Repo layout](#repo-layout)
- [Measuring pilot success](#measuring-pilot-success)
- [What's deferred to V2](#whats-deferred-to-v2)

---

## What it does

The core problem: students practice for weeks and still don't know what to fix. Generic AI chat has no memory, no rubric, and no idea what's on your resume or what role you're targeting.

PrepPilot's loop:
1. Add your resume and the job description
2. Do a mock interview (Behavioral or PM track) — the questions are aware of your resume and the JD
3. Get rubric-based feedback that quotes your own words
4. See your readiness score update and your trend line grow

**Jobs to be done:** *"When I have an interview in two weeks, I want to practice against my resume and the JD and get scored, so I know exactly what to fix first — and I can see I'm improving."*

**North star:** number of students reaching "Interview Ready."

**Activation:** resume uploaded (or first JD added) and first interview completed.

Full planning docs live in [`docs/`](docs/) — PRD, competitive analysis, personas, user flows, architecture, DB schema, API contracts, wireframes, sprint plan.

---

## Readiness score formula

The score is not a magic number — it's fully reconstructable from stored per-answer rubric scores.

1. **Normalize** each rubric score (1–5) → `norm = (raw - 1) / 4 * 100`
2. **Competency score (recency-weighted).** Exponentially weighted moving average, newest answers first:
   `C_k = Σ(α^age · norm) / Σ(α^age)`, default **α = 0.6** — recent practice counts more, older sessions fade but still matter
3. **Readiness** = weighted average of competency scores, weights per track:

   | Competency | Behavioral | PM |
   |---|--:|--:|
   | Communication | 0.20 | 0.20 |
   | Structure | 0.20 | 0.25 |
   | Depth / Role-Knowledge | 0.15 | 0.20 |
   | Problem-Solving | 0.15 | 0.25 |
   | Behavioral / STAR | 0.30 | 0.10 |

4. **Small-sample guard.** Below 5 sessions, show **"Building baseline (n/5)"** — no band, so nobody over-trusts a score built on one or two answers.
5. **Bands.** `<50 Building · 50–70 Developing · 70–85 Nearly Ready · 85+ Interview Ready`

*"Why is this student a 72?"* — Structure (78) and Communication (81) are strong, but Problem-Solving (61) and Depth (58) drag the PM-weighted average down. The last two sessions lifted Structure by 9 points, which is why 72 is up from 66. The score is fully auditable.

Implementation: [`scoring_service.py`](backend/app/services/scoring_service.py), tested in [`test_scoring.py`](backend/tests/unit/test_scoring.py).

---

## Architecture

Modular monolith. The frontend is presentation-only — all AI calls go through FastAPI.

```
Next.js (React / TS / Tailwind / Recharts)
   ↓ HTTPS + JWT
FastAPI  →  Auth (Google OAuth/JWT)  →  Services  →  LiteLLM  →  LangGraph (2 nodes)
   ↓                                                                │
PostgreSQL  ←──────────────────────────────────────  LangSmith tracing
```

- **Two LangGraph nodes:** `interview_node` (asks questions + one adaptive follow-up per the student's actual answer) and `evaluation_node` (rubric scoring, structured JSON output). Routing is deterministic code, not an LLM planner.
- **No RAG, no vector DB.** Resume and JD are injected as direct context.
- **LiteLLM** wraps Claude for swappability, with retry + graceful fallback and token/cost/latency tracking.
- **Mock mode:** with no `ANTHROPIC_API_KEY`, a deterministic mock LLM runs — the whole product is demoable and testable for free.

Full architecture doc: [`docs/05-SYSTEM-ARCHITECTURE.md`](docs/05-SYSTEM-ARCHITECTURE.md).

---

## Quick start

### Option A — Docker (recommended, closest to production)
```bash
# from repo root
cp backend/.env.example backend/.env   # optional — compose sets sane defaults
docker compose up --build
# Frontend: http://localhost:3000
# API docs: http://localhost:8000/docs
```
Runs in mock mode by default (free). To use live Claude:
```bash
ANTHROPIC_API_KEY=sk-ant-... docker compose up --build
```

### Option B — Local dev (SQLite, no Docker)

**Backend**
```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install .[dev]
export DATABASE_URL="sqlite+aiosqlite:///./preppilot.db"
python -m app.seed          # seeds demo sessions so the dashboard looks real
uvicorn app.main:app --reload --port 8000
```

**Frontend** (new terminal)
```bash
cd frontend
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                  # http://localhost:3000
```

Sign in with `demo@preppilot.ai` to see the seeded dashboard and trend. In production, dev login is disabled and Google OAuth takes over.

> Requires Python 3.11+ and Node 20+.

---

## Deploying (Render + Vercel)

Full step-by-step in [`DEPLOYMENT.md`](DEPLOYMENT.md). Short version:

1. Push this repo to GitHub
2. [Render](https://render.com) → New Blueprint → connect repo → Render reads `render.yaml`, provisions the backend + Postgres automatically
3. [Vercel](https://vercel.com) → Import → root directory: `frontend` → add `NEXT_PUBLIC_API_URL=https://preppilot-backend.onrender.com` → deploy
4. Set `FRONTEND_ORIGIN` on Render to your Vercel URL to wire CORS

Both free tiers. No credit card needed.

---

## Running the tests

```bash
cd backend
pip install .[dev]
pytest -q
```
Tests run against SQLite in mock mode — no API key, no Postgres needed. CI runs the same on every push (`.github/workflows/ci.yml`), plus frontend typecheck/build and Docker image builds.

---

## AI evaluation

The evaluator is the core of the product, so it's treated as a first-class deliverable:

```bash
cd backend
python -m tests.ai_eval.run_eval   # AI scores vs. human benchmark
```
- Benchmark: [`tests/ai_eval/benchmark.jsonl`](backend/tests/ai_eval/benchmark.jsonl) — human-scored answers across weak → strong
- Reports MAE, exact and within-1 agreement per competency, and self-consistency across repeated runs
- Methodology and calibration notes: [`docs/reports/AI-EVALUATION-REPORT.md`](docs/reports/AI-EVALUATION-REPORT.md)

---

## Cost

Rough estimate at pilot scale (~30 students):

| Line item | Assumption | Monthly est. |
|---|---|--:|
| Claude tokens | ~240 interviews × ~$0.08 | ~$20 |
| Render backend | Free tier | $0 |
| Render Postgres | Free tier | $0–7 |
| LangSmith | Dev tier | $0 |
| **Total** | | **~$20–27/mo** |

Controls: per-user daily caps (Postgres counters), per-endpoint rate limiting, answer-length cap (1,800 chars), per-call spend tracking at `GET /metrics`. Set a global spend ceiling before any public launch.

---

## Privacy and data retention

- Resume text is encrypted at rest (Fernet).
- Resume and JD inputs are treated as untrusted data — the model is instructed to never follow instructions inside them (system/user/document channels are kept separate).
- `DELETE /user/data` irreversibly purges everything.
- Inactive resumes are auto-purged after 90 days (`RESUME_RETENTION_DAYS`).

---

## Repo layout

```
preppilot-ai/
├── docs/              # PRD + 9 other planning artifacts, plus reports/
├── backend/           # FastAPI modular monolith (controllers/services/repos/models)
│   └── app/ai/        # rubrics.py, 2-node LangGraph, prompts, LiteLLM wrapper
├── frontend/          # Next.js app (dashboard, interview flow, history, settings)
├── docker-compose.yml # db + backend + frontend
├── render.yaml        # one-click Render deploy
└── .github/workflows/ # CI
```

---

## Measuring pilot success

Pilot target: 20–30 students from the Consulting Club and Placement Cell, running the core loop before any extension is polished.

- **Activation rate** — % who upload a resume/JD and finish one interview
- **Readiness improvement** — median Δ readiness from session 1 → session 5
- **Engagement** — interviews per user per week; % reaching ≥5 sessions
- **Quality** — average interview score; thumbs-up rate on feedback cards
- **North star** — students reaching "Nearly Ready" or "Interview Ready"
- **Qualitative** — short weekly check-ins: did the feedback feel specific to you? did you know what to fix?

Iteration loop: ship → watch activation and feedback thumbs → fix the biggest drop-off. Pilot report at [`docs/reports/PILOT-REPORT.md`](docs/reports/PILOT-REPORT.md) documents at least one change made from pilot feedback.

---

## Shipped extensions (Phase 2)

| Extension | What it does |
|---|---|
| **Resume Intelligence (E1)** | PDF upload + parse, skill extraction, professional summary, JD match % (heuristic, clearly labeled "not an ATS score"), improvement suggestions |
| **Job Intelligence (E2)** | Required-skill extraction, resume comparison, company prep tips generated only from the JD and your pasted notes — no external data fetched, labeled clearly |
| **Analytics polish** | Feedback thumbs loop wired end-to-end → feedback-trust metric at `GET /metrics` |
| **Migrations** | Full Alembic setup, round-trip verified, applied automatically on container start |

---

## What's deferred to V2

| Deferred | Why |
|---|---|
| Technical / SQL / AI-ML / Case tracks | Two tracks done well proves the loop works. Adding a track is one entry in `rubrics.py`. |
| Cohort/admin analytics | Student value has to land first. |
| RAG / vector search, streaming, multi-model, fine-tuning | Complexity without pilot-stage payoff. |

---

For PM roles: the problem → users → pilot → outcomes → tradeoffs story is the core. Architecture is in the appendix.
For AI/engineering roles: the evaluation methodology and 2-node system design are the interesting parts.
