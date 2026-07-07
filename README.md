# PrepPilot AI — Career Intelligence Platform

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://preppilot-ai-blond.vercel.app)
[![Backend API](https://img.shields.io/badge/api-render-blue)](https://preppilot-backend-x6xc.onrender.com/docs)
[![CI](https://github.com/twix07/preppilot-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/twix07/preppilot-ai/actions/workflows/ci.yml)

**[Live demo →](https://preppilot-ai-blond.vercel.app)** · Sign in with `demo@preppilot.ai` to try it.

---
<img width="1280" height="738" alt="Screenshot 2026-07-08 at 1 32 11 AM" src="https://github.com/user-attachments/assets/7640cd90-3922-4f1f-a953-93ff7d1bf790" />

<img width="1280" height="757" alt="Screenshot 2026-07-08 at 1 31 16 AM" src="https://github.com/user-attachments/assets/8bc58f7c-99a0-47bf-b97a-9edf8d4b901b" />


I used to run mock interview sessions at my college's Training & Placement Cell and a 300+ member Consulting & Analytics Club. The problem I kept running into: students would practice for weeks and still not know what to actually fix. Mentor mocks don't scale, feedback quality varies, and there's no way to track whether someone is improving.

PrepPilot is what I built to fix that. It runs resume- and JD-aware mock interviews, scores answers against a rubric, and tracks a readiness score over time — so students have a number they can actually point to and a direction they can act on.

**Tech stack:** Python / FastAPI · LangGraph · LiteLLM / Claude · PostgreSQL / SQLAlchemy / Alembic · Next.js / TypeScript / Tailwind / Recharts · Docker · Render + Vercel

---

## What it does

1. Upload your resume and paste the job description
2. Pick a track (Behavioral or PM) and start a mock interview
3. The interviewer asks questions tailored to your resume and the JD, with one adaptive follow-up per question based on what you actually said
4. After each question, get rubric-based feedback that quotes your own words
5. Your readiness score updates, the trend line grows, and the dashboard shows you exactly what to work on next

The full loop — resume + JD → adaptive interview → rubric evaluation → readiness update → dashboard — runs end-to-end with no API key needed (mock mode is free).

---

## How the readiness score works

It's not a magic number. It's reconstructable from stored per-answer rubric scores at any point.

Every answer is scored 1–5 on rubric dimensions that map to five competencies: Communication, Structure, Depth/Role-Knowledge, Problem-Solving, Behavioral/STAR.

**Recency-weighted average** per competency — recent sessions count more, older ones fade:
```
C_k = Σ(α^age · norm) / Σ(α^age)    α = 0.6 by default
```

**Readiness** = weighted average of competency scores, weights differ by track:

| Competency | Behavioral | PM |
|---|--:|--:|
| Communication | 0.20 | 0.20 |
| Structure | 0.20 | 0.25 |
| Depth / Role-Knowledge | 0.15 | 0.20 |
| Problem-Solving | 0.15 | 0.25 |
| Behavioral / STAR | 0.30 | 0.10 |

Below 5 sessions → shows "Building baseline (n/5)" instead of a band. Nobody should over-trust a score built on two answers.

Bands: `< 50 Building · 50–70 Developing · 70–85 Nearly Ready · 85+ Interview Ready`

Code: [`scoring_service.py`](backend/app/services/scoring_service.py) · Tests: [`test_scoring.py`](backend/tests/unit/test_scoring.py)

---

## Architecture

Modular monolith — one FastAPI backend, one Next.js frontend, one Postgres DB. The frontend is presentation only; all AI calls go through the backend.

```
Next.js (React / TS / Tailwind / Recharts)
   ↓ HTTPS + JWT
FastAPI → Auth → Services → LiteLLM → LangGraph (2 nodes)
   ↓                                        │
PostgreSQL ←──────────────── LangSmith tracing
```

Two LangGraph nodes, deterministic routing between them:
- `interview_node` — asks the next question or a single adaptive follow-up based on the student's actual answer
- `evaluation_node` — scores 1–5 per rubric dimension, structured JSON output, quotes the student's words in feedback

No RAG, no vector DB. Resume and JD go in as direct context. LiteLLM wraps Claude so the model is swappable without changing app code.

Mock mode: no API key → deterministic mock LLM → full product works and is testable for free.

Details: [`docs/05-SYSTEM-ARCHITECTURE.md`](docs/05-SYSTEM-ARCHITECTURE.md)

---

## Running locally

### Docker (easiest)
```bash
cp backend/.env.example backend/.env
docker compose up --build
# Frontend: http://localhost:3000
# API docs: http://localhost:8000/docs
```

### Without Docker (SQLite)

Backend:
```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install .[dev]
export DATABASE_URL="sqlite+aiosqlite:///./preppilot.db"
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

Frontend:
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Sign in with `demo@preppilot.ai` to see seeded sessions and a readiness trend.

---

## Deploying

Full guide in [`DEPLOYMENT.md`](DEPLOYMENT.md). The short version:

1. Push to GitHub
2. Render → New Blueprint → connect repo (reads `render.yaml`, provisions backend + Postgres)
3. Vercel → Import → root directory: `frontend` → add `NEXT_PUBLIC_API_URL` → deploy
4. Set `FRONTEND_ORIGIN` on Render to your Vercel URL

Both free tiers, no credit card needed.

---

## Tests

```bash
cd backend && pip install .[dev] && pytest -q
```

Runs against SQLite in mock mode — no API key or Postgres needed. Same setup runs in CI on every push.

---

## AI evaluation

```bash
cd backend && python -m tests.ai_eval.run_eval
```

Compares AI rubric scores against a human-labeled benchmark. Reports MAE, exact and within-1 agreement per competency, and self-consistency across runs. The benchmark and methodology are in [`docs/reports/AI-EVALUATION-REPORT.md`](docs/reports/AI-EVALUATION-REPORT.md).

---

## Cost at pilot scale (~30 students)

| | Monthly est. |
|---|--:|
| Claude tokens (~240 interviews × $0.08) | ~$20 |
| Render backend (free tier) | $0 |
| Render Postgres (free tier) | $0–7 |
| LangSmith (dev tier) | $0 |
| **Total** | **~$20–27/mo** |

Per-user daily caps, per-endpoint rate limiting, 1,800-char answer cap, and per-call spend tracking keep this from running away.

---

## Privacy

- Resume text encrypted at rest (Fernet)
- Resume/JD inputs treated as untrusted data — model is instructed they are data, not commands
- `DELETE /user/data` purges everything permanently
- Inactive resumes auto-deleted after 90 days

---

## Repo layout

```
preppilot-ai/
├── backend/           # FastAPI monolith — services, repos, models, AI layer
│   └── app/ai/        # LangGraph nodes, prompts, rubrics, LiteLLM wrapper
├── frontend/          # Next.js — dashboard, interview flow, history, settings
├── docs/              # PRD, architecture, DB schema, API contracts, wireframes, sprint plan
├── docker-compose.yml
├── render.yaml
└── .github/workflows/
```

---

## What's in V2

| Feature | Why it's not in V1 |
|---|---|
| More interview tracks (technical, case, SQL) | Two tracks done well proves the loop is track-agnostic |
| Cohort/admin analytics | Student value has to land first |
| RAG, streaming, multi-model routing | No pilot-stage payoff |

---

Docs in [`docs/`](docs/) cover the full product thinking — PRD, competitive analysis, personas, user flows, and sprint plan. For engineering conversations, the evaluation methodology and 2-node design are the interesting parts.
