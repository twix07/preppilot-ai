# PrepPilot AI — Folder Structure

A single repo with a clear `backend/` (FastAPI modular monolith) and `frontend/` (Next.js). Docs and infra at the root.

```
preppilot-ai/
├── README.md                     # product overview, setup, readiness formula, cost, retention
├── DEPLOYMENT.md                 # step-by-step Render + Vercel deploy guide
├── docker-compose.yml            # local: backend + frontend + postgres
├── render.yaml                   # one-click Render deploy config
├── .github/
│   └── workflows/
│       └── ci.yml                # lint, type-check, tests, build, deploy
├── docs/                         # planning artifacts (this folder)
│   ├── 01-PRD.md … 10-SPRINT-PLAN.md
│   └── reports/
│       ├── AI-EVALUATION-REPORT.md
│       ├── PILOT-REPORT.md
│       └── PRODUCT-METRICS-REPORT.md
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml            # deps: fastapi, uvicorn, sqlalchemy, alembic,
│   │                             #       pydantic, litellm, langgraph, langsmith,
│   │                             #       python-jose, passlib, pypdf, pytest
│   ├── .env.example
│   ├── alembic/                  # DB migrations
│   │   └── versions/
│   └── app/
│       ├── main.py               # FastAPI app factory, router mounting, middleware
│       ├── core/
│       │   ├── config.py         # settings (pydantic-settings)
│       │   ├── security.py       # JWT create/verify, oauth helpers
│       │   ├── logging.py
│       │   └── exceptions.py     # error types and handlers
│       ├── db/
│       │   ├── session.py        # async engine + session
│       │   └── base.py           # declarative base
│       ├── models/               # SQLAlchemy models
│       │   ├── user.py
│       │   ├── resume.py
│       │   ├── job_description.py
│       │   ├── interview_session.py
│       │   ├── question.py
│       │   ├── answer.py
│       │   ├── competency.py
│       │   ├── readiness_score.py
│       │   └── analytics.py
│       ├── schemas/              # Pydantic DTOs (request/response)
│       │   ├── auth.py
│       │   ├── resume.py
│       │   ├── jd.py
│       │   ├── interview.py
│       │   ├── dashboard.py
│       │   └── analytics.py
│       ├── repositories/         # DB access only
│       │   ├── base.py
│       │   ├── user_repo.py
│       │   ├── resume_repo.py
│       │   ├── jd_repo.py
│       │   ├── session_repo.py
│       │   ├── answer_repo.py
│       │   └── readiness_repo.py
│       ├── services/             # all business logic lives here
│       │   ├── auth_service.py
│       │   ├── resume_service.py
│       │   ├── jd_service.py
│       │   ├── interview_service.py     # orchestrates the turn state machine
│       │   ├── evaluation_service.py    # calls Evaluation Node, parses scores
│       │   ├── scoring_service.py       # readiness formula — single source of truth
│       │   ├── roadmap_service.py       # skill gap + weekly roadmap
│       │   ├── dashboard_service.py
│       │   └── usage_service.py         # daily caps + spend tracking
│       ├── ai/
│       │   ├── llm.py            # LiteLLM client wrapper (retry, cost/latency tracking)
│       │   ├── graph.py          # LangGraph: 2 nodes + deterministic edges
│       │   ├── nodes/
│       │   │   ├── interview_node.py
│       │   │   └── evaluation_node.py
│       │   ├── prompts/
│       │   │   ├── interviewer.py       # system prompt per track
│       │   │   └── evaluator.py         # structured-output scoring prompt
│       │   └── rubrics.py       # track rubrics, competency map, weights — the config core
│       ├── api/
│       │   ├── deps.py           # shared deps (current_user, db session, rate limit)
│       │   └── routers/          # thin controllers
│       │       ├── auth.py
│       │       ├── resume.py
│       │       ├── jd.py
│       │       ├── interview.py
│       │       ├── dashboard.py
│       │       ├── analytics.py
│       │       └── user.py       # DELETE /user/data
│       ├── middleware/
│       │   ├── rate_limit.py
│       │   └── request_context.py
│       └── observability/
│           └── metrics.py        # latency/token/cost/error aggregation
│   └── tests/
│       ├── unit/                 # scoring math, rubric map, services (mocked LLM)
│       ├── integration/          # API + DB, auth, caps
│       └── ai_eval/              # benchmark dataset + AI-vs-human comparison
│           ├── benchmark.jsonl
│           └── run_eval.py
│
└── frontend/
    ├── Dockerfile
    ├── package.json              # next, react, typescript, tailwind, recharts
    ├── .env.example
    ├── next.config.js
    ├── tailwind.config.ts
    └── src/
        ├── app/
        │   ├── layout.tsx        # shell, nav, auth guard
        │   ├── page.tsx          # home / sign-in
        │   ├── dashboard/page.tsx
        │   ├── interview/page.tsx
        │   ├── history/page.tsx
        │   ├── settings/page.tsx # delete-my-data
        │   └── metrics/page.tsx  # internal observability
        ├── components/
        │   ├── ui/               # shadcn primitives
        │   ├── interview/        # QuestionPanel, AnswerBox, FeedbackCard
        │   ├── dashboard/        # ReadinessGauge, TrendChart, CompetencyBars, TopFixes
        │   └── common/           # nav, empty states, loaders
        ├── lib/
        │   ├── api.ts            # typed fetch client
        │   └── auth.ts           # token handling
        ├── hooks/
        └── types/                # shared TS types mirrored from OpenAPI
```

## Conventions

**Backend:** async everywhere, type hints and Pydantic throughout, one router → one service, services never import routers, repos never contain business rules.

**Frontend:** presentation only — no AI keys, no rubric logic in the client. Types mirrored from the backend OpenAPI schema.

**The reusable core:** `backend/app/ai/rubrics.py` (rubrics, competency map, per-track weights) and `backend/app/services/scoring_service.py` (readiness math). Both are single-source-of-truth and unit-tested.

**Tests** live beside their layer. `ai_eval/` holds the benchmark and evaluation harness.
