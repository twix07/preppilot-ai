# Pilot Report — Plan, Instrumentation & Results

**Status:** Plan ready to execute. The core loop is deployed-ready and instrumented; this document is the pilot instrument. Results sections are marked _[to populate post-pilot]_ and are the honest, not-yet-collected outputs.

---

## 1. Objective

Validate the **core loop** (resume/JD-aware interview → rubric evaluation → readiness) with real students *before* building any extension. Answer three questions:
1. Do students **activate** (finish a first interview)?
2. Does **readiness improve** with practice?
3. Is the **feedback trusted** (does it feel specific and actionable)?

## 2. Participants

20–30 students from the Consulting & Analytics Club / Placement Cell. Mix of tracks (Behavioral + PM). Recruited directly (built-in distribution).

## 3. Protocol (2 weeks)

- **Day 0:** onboard, sign in, paste resume + a target JD, complete interview #1 (baseline).
- **Days 1–12:** complete ≥5 interviews (crossing the small-sample guard).
- **Day 14:** exit survey + 6–8 short qualitative interviews.

## 4. What we collect (already instrumented)

| Metric | Source in the product |
|---|---|
| Activation (resume/JD + first interview) | `analytics_events`: `interview_started` / `interview_completed` |
| Readiness improvement (Δ session1→session5) | `readiness_scores` snapshots (trend) |
| Interviews completed / user / week | `interview_sessions` |
| Feedback trust (👍/👎) | Feedback-card thumbs _(UI hook present; wire to `analytics_events` for the pilot)_ |
| Per-answer scores (for audits) | `answer_scores` |
| System health (latency, cost, errors) | `GET /metrics` |

## 5. Success criteria (pre-registered)

- **Activation ≥ 70%** of onboarded students finish interview #1.
- **Median readiness Δ ≥ +8** points from session 1 → 5.
- **Feedback trust ≥ 70%** 👍 on feedback cards.
- **≥ 50%** reach 5 sessions (cross the guard).

## 6. Results _[to populate post-pilot]_

| Metric | Target | Actual |
|---|--:|--:|
| Activation | ≥70% | _[ ]_ |
| Median readiness Δ (s1→s5) | ≥+8 | _[ ]_ |
| Feedback trust (👍) | ≥70% | _[ ]_ |
| Reached 5 sessions | ≥50% | _[ ]_ |

_Attach: readiness trend distribution, drop-off funnel, top qualitative themes._

## 7. Product iteration from feedback _[to populate post-pilot]_

Document **at least one** change made because of pilot feedback. Template:

> **Observation:** _e.g._ "40% dropped off at the resume-paste step — friction too high."
> **Hypothesis:** making resume optional and prompting for it later raises activation.
> **Change shipped:** resume/JD made optional at start (already supported); reorder the setup so students can begin immediately.
> **Result after change:** activation moved from _[x]%_ → _[y]%_.

## 8. Anticipated risks & mitigations

- **Cold-start friction** → resume/JD optional; one-click start.
- **Feedback distrust** → the quote-your-words requirement is the core mitigation; measured by the thumbs metric.
- **Cost** → daily caps + spend tracking already enforced.
