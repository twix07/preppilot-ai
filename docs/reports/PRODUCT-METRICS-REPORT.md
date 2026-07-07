# Product Metrics Report

Product metrics (user value) are tracked **separately** from system observability (latency/cost/errors, at `GET /metrics`). This report defines the metric tree, how each is instrumented, and where it surfaces.

---

## 1. Metric tree

```
North Star:  # students reaching "Interview Ready"
   ├── Activation:  resume/JD added  AND  first interview completed
   ├── Engagement:  WAU · interviews/user/week · % reaching ≥5 sessions
   ├── Quality:     avg interview score · readiness improvement (Δ) · feedback 👍 rate
   └── Retention:   % activated users returning week 2
```

## 2. Definitions & instrumentation

| Metric | Definition | Instrumented via | Surfaced at |
|---|---|---|---|
| **North Star** | Distinct users whose latest readiness band = `interview_ready` | `readiness_scores` (latest per user) | Internal report / dashboard |
| **Activation** | User with a resume or JD **and** ≥1 completed interview | `resumes`/`job_descriptions` + `interview_sessions(status=completed)` | `analytics_events` |
| **WAU** | Distinct users active in a rolling 7 days | `users.last_active_at` + events | Internal |
| **Interviews / user / week** | Completed sessions ÷ active users | `interview_sessions` | `GET /analytics` |
| **Avg interview score** | Mean session readiness | `readiness_scores.overall` | `GET /analytics` → `totals.avg_score` |
| **Readiness improvement** | Δ readiness over 30 days | `readiness_scores` history | `GET /analytics` → `readiness_change_30d` |
| **Feedback trust** | 👍 ÷ (👍+👎) on feedback cards | UI thumbs → `analytics_events` _(wire in pilot)_ | Internal |
| **Reached-5-sessions** | % activated users with ≥5 completed sessions | `interview_sessions` | Internal |

## 3. Current instrumentation status

- ✅ **Live now:** interview started/completed events, readiness snapshots + trend, `GET /analytics` totals (completed, avg score, 30-day change), per-answer scores, activation-derivable events, system metrics at `GET /metrics`.
- 🟡 **Wire during pilot:** feedback 👍/👎 (UI affordance exists; connect to `analytics_events`), cohort rollups (V2 admin view).

## 4. Worked example (seeded demo user)

From the seeded demo account (`demo@preppilot.ai`, 5 sessions, mock evaluator), the live `GET /dashboard` returns:

- **Readiness:** 70.3 → band **Nearly Ready** (guard just cleared at 5 sessions).
- **Trend:** 5 points, rising as answer quality improves across sessions (recency weighting visible).
- **Competency split:** Behavioral/STAR ~95 (STAR-heavy seed answers) vs. Communication/Structure ~50 — correctly surfaces *what to fix next*.

This demonstrates the metric pipeline end-to-end: per-answer scores → competency scores → readiness → trend → "top things to fix."

## 5. Guardrail metrics (don't win the wrong way)

- **Feedback must stay specific** — if 👍 rate falls, the quote-grounding is failing; investigate before pushing engagement.
- **Cost per active user** — from `usage_counters.est_cost_usd`; keep under the documented ceiling.
- **No score inflation** — average scores rising *without* rubric-quality rising would signal evaluator drift; cross-check against the AI evaluation benchmark.
