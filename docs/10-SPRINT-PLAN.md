# PrepPilot AI — Sprint Plan

**Cadence:** solo, part-time. Realistic to full definition of done: 6–10 weeks. Phase gates are hard — Phase 2 does not start until Phase 1 is done, deployed, and piloted.

---

## Milestones

```
Week 0        │ Planning artifacts approved ─────────────────► code begins
Weeks 1–6     │ PHASE 1 — Mandatory Core
              │   └─ Gate A: core loop deployed + pilot run + iteration documented
Weeks 7–10    │ PHASE 2 — Extensions (only after Gate A)
              │   └─ If time runs out: stop, document deferrals, finalize
```

---

## Phase 1 — Core (Weeks 1–6)

| Sprint | Focus | Key deliverables | Done when |
|---|---|---|---|
| **S1 · Wk1** | Backend foundation | FastAPI app factory, config, Postgres + SQLAlchemy + Alembic, base scaffolding, health check, Docker + docker-compose | App boots in Docker, migrations run, `/health` green |
| **S2 · Wk1–2** | Auth | Google OAuth → JWT, `current_user` dep, owner-scoping, `POST /auth/google`, `GET /auth/me` | Can sign in, protected routes reject bad JWT |
| **S3 · Wk2** | Resume & JD ingestion | `POST /resume/upload` (text), `POST /jd/upload`, validation, encrypt-at-rest, models/repos | Resume and JD stored, scoped, retrievable |
| **S4 · Wk3** | AI Interview Node | LiteLLM wrapper (retry, cost/latency capture), LangGraph graph, Interview Node + prompts, `rubrics.py`, `POST /interview/start` + `/answer` state machine, LangSmith tracing | Full 3Q + follow-up interview runs end-to-end, one question at a time, resume/JD-aware |
| **S5 · Wk3–4** | AI Evaluation Node + benchmark | Evaluation Node (structured output, low temp), feedback that quotes the student, per-answer `answer_scores`, benchmark dataset (30–50 human-scored answers) + eval script | Scores persist per dimension; AI eval report v1 (agreement, self-consistency, calibration) |
| **S6 · Wk4** | Readiness + Dashboard | `scoring_service` (recency-weighted formula, guard, bands — unit-tested), readiness snapshots, `GET /dashboard`, frontend dashboard (Recharts trend + competency bars + top fixes + roadmap) | Readiness computes correctly, trend renders, "why is this a 72?" is answerable |
| **S7 · Wk5** | Cost/abuse + security/privacy | `usage_counters` daily caps, per-endpoint rate limiting, prompt-injection channel separation, file validation, `DELETE /user/data`, 90-day purge | Over-cap returns 429, delete purges everything, docs treated as untrusted |
| **S8 · Wk5** | Deploy | GitHub Actions (lint, type-check, tests, build, deploy), Render + Postgres, secrets via env vars, HTTPS | **Public URL live**, CI green on main |
| **S9 · Wk5–6** | **Pilot** | Onboard 20–30 club/placement students, seed demo sessions, collect readiness improvement, completion rate, qualitative feedback | Pilot data collected, at least 1 iteration identified |
| **S10 · Wk6** | Tests + iteration | Unit (scoring, rubric map, services with mocked LLM) + integration (API+DB, auth, caps), apply the pilot-driven change | Tests pass in CI; iteration documented → **Gate A** |

**Gate A:** core loop deployed on a public URL, piloted with real students, at least one product change made from feedback and documented, core tests green.

---

## Phase 2 — Extensions (Weeks 7–10, only after Gate A)

| Sprint | Focus | Deliverables | Done when |
|---|---|---|---|
| **S11 · Wk7** | Resume Intelligence (E1) | PDF upload + parse, skill extraction, summary, JD match % (heuristic, with caveat), improvement suggestions | `POST /resume/analyze` works, match % is honestly labeled |
| **S12 · Wk8** | Job Intelligence (E2) | JD required-skill extraction, resume comparison, company tips from JD + pasted notes only (no external fetch) | Tips clearly labeled AI-generated from inputs |
| **S13 · Wk9** | Analytics polish | `GET /analytics`, internal `/metrics` view, product-metrics instrumentation | Metrics visible, product-metrics report drafted |
| **S14 · Wk9–10** | Test coverage | Broader unit + integration coverage, edge cases, error handling | Coverage targets met, production-grade error handling |
| **S15 · Wk10** | Docs + demo | README (formula, retention, cost), architecture docs, OpenAPI, AI eval report final, pilot report, product-metrics report | All final deliverables present |

If time runs out in Phase 2: stop, document every deferred feature and why in the V2 roadmap, and finalize. A deep, piloted core beats a broad, unfinished platform.

---

## Definition of done checklist

- [ ] Public deployment · Google OAuth + JWT · responsive UI · Docker · CI/CD
- [ ] OpenAPI docs · architecture docs · DB schema · PRD · README (formula + retention + cost)
- [ ] Unit + integration tests passing · production-grade error handling · no placeholder features
- [ ] Pilot with 20–30 users + documented iteration
- [ ] AI evaluation report · product metrics report
- [ ] Reflection + V2 roadmap (every deferred feature + reason)

---

## Risk register

| Risk | Likelihood | How to handle it |
|---|---|---|
| Scope creep into extensions before core is piloted | High | Hard Gate A; extensions are physically blocked in the plan |
| LLM scoring inconsistency | Medium | Benchmark + calibration is Phase 1 (S5), not deferred |
| Deploy friction eats time | Medium | Deploy early (S8) on a thin slice — don't save it for the end |
| Solo bandwidth slip | Medium | 6–10 week range, not 3–4; cut Phase 2 before cutting core depth |
| Cost surprise | Low | Answer caps + daily caps + spend tracking built in from S4/S7 |

---

## V2 roadmap

| Deferred | Why |
|---|---|
| Technical / SQL / AI-ML / Case interview tracks | Two tracks done well proves the loop works. Adding a track is one entry in `rubrics.py`. |
| Cohort/admin analytics | Student value has to land first. |
| RAG / vector search | No value at this scale — context injection is enough. |
| Voice interviews, mobile app | High effort, not core to the readiness thesis. |
| Multi-model routing, streaming, A/B testing, fine-tuning | Complexity without pilot-stage payoff. |
