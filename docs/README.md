# PrepPilot AI — Planning Docs

These are the planning artifacts I wrote before writing any code. They're ordered to move from *why* (product thinking) to *how* (engineering decisions).

| # | Artifact | File | What it covers |
|---|---|---|---|
| 1 | Product Requirements | [01-PRD.md](01-PRD.md) | Problem, goal, scope, readiness formula, metrics, pilot, definition of done |
| 2 | Competitive Analysis | [02-COMPETITIVE-ANALYSIS.md](02-COMPETITIVE-ANALYSIS.md) | Market landscape, positioning, one-line wedge |
| 3 | User Personas | [03-USER-PERSONAS.md](03-USER-PERSONAS.md) | Who the product is built for, jobs to be done |
| 4 | User Flows | [04-USER-FLOWS.md](04-USER-FLOWS.md) | Core loop and key flows, step by step |
| 5 | System Architecture | [05-SYSTEM-ARCHITECTURE.md](05-SYSTEM-ARCHITECTURE.md) | Modular monolith, 2-node LangGraph, request traces |
| 6 | Folder Structure | [06-FOLDER-STRUCTURE.md](06-FOLDER-STRUCTURE.md) | Monorepo layout, backend + frontend |
| 7 | Database Schema | [07-DATABASE-SCHEMA.md](07-DATABASE-SCHEMA.md) | Normalized Postgres schema, DDL, ERD |
| 8 | API Contracts | [08-API-CONTRACTS.md](08-API-CONTRACTS.md) | REST endpoints, request/response shapes, error codes |
| 9 | UI Wireframes | [09-UI-WIREFRAMES.md](09-UI-WIREFRAMES.md) | Screen-by-screen low-fi layouts |
| 10 | Sprint Plan | [10-SPRINT-PLAN.md](10-SPRINT-PLAN.md) | 6–10 week plan, phase gates, risk register, V2 roadmap |

## Core principles I held to throughout

1. **Ship the core loop first.** Resume + JD → adaptive interview → rubric evaluation → readiness update → dashboard → pilot. Everything else is cuttable.
2. **No placeholders.** A feature is done and tested, or explicitly deferred to V2 with a reason.
3. **Simpler over more tech.** When two designs were equally good, I picked the one easier to maintain and explain.
4. **No RAG, no vector DB.** Resume and JD are injected as direct context — retrieval adds complexity with no real payoff at this scale.
5. **Two LangGraph nodes only** — Interview and Evaluation. Routing is deterministic code.

## Status

Phase 1 (mandatory core) and Phase 2 (resume/job intelligence, analytics polish) are built and tested — 24 backend tests green, frontend builds, Alembic migrations round-trip. The core loop runs end-to-end.

See the root [README](../README.md) to run it locally or deploy it, and [docs/reports/](reports/) for the AI evaluation, pilot, and product-metrics deliverables.
