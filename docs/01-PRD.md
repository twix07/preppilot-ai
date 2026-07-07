# PrepPilot AI — Product Requirements Document

**Owner:** Tvisha Chawla (Founder / PM)
**Last updated:** July 2026

---

## 1. The problem

Students prepping for placements have no real way to know if they're actually ready for interviews. The options out there all fail in the same ways:

- **Mentor mock interviews** — the route I ran at our Training & Placement Cell and the 300+ member Consulting & Analytics Club — are genuinely helpful but don't scale. Feedback quality varies by mentor, and there's no record of where a student stands or whether they're improving.
- **Generic AI chat** can answer questions but won't run a structured interview, won't score against a rubric, has no idea what's on your resume or what role you're targeting, and forgets you after every session.
- **Paid prep platforms** are expensive, built for US tech roles, and never tie their feedback back to your specific resume and the specific JD you're applying to.

The result: a student can practice for weeks and still not know what the two things are they actually need to fix.

## 2. The questions PrepPilot answers

1. **Am I interview ready?** → A readiness score (0–100) with a confidence guard so we don't lie when there's not enough data yet.
2. **Why am I not ready?** → A competency breakdown that quotes your own answers.
3. **What should I fix first?** → Prioritized recommendations and a weekly roadmap.
4. **Which skills am I missing?** → Skill-gap analysis from rubric weaknesses plus the JD's required skills.
5. **How well does my resume match this job?** → A JD match percentage, clearly labeled as a heuristic — not an ATS score.
6. **Am I actually improving over time?** → A readiness trend line across sessions.

## 3. What we're building

An AI-native Career Intelligence Platform that turns a mentor-run prep program into something every student can access — personalized mock interviews that know your resume and target role, consistent rubric-based feedback, and a readiness signal you can actually point to and defend.

This isn't about replacing mentors. It's about making good prep available before students even get to a mentor, and giving mentors a real record to work from.

## 4. Who it's for

**Primary:** final-year students heading into placement season, sourced through the Placement Cell and Consulting & Analytics Club. The distribution is already there — this is the built-in advantage.

**Secondary:** Placement Cell and club mentors who want a readiness signal across their students (this is a V2 feature, not core).

See [03-USER-PERSONAS.md](03-USER-PERSONAS.md) for the full persona breakdown.

## 5. Scope

### 5.1 Core (ships first, everything else waits)

| # | Capability | Notes |
|---|---|---|
| C1 | **AI Interview** | Behavioral and PM tracks. Resume-aware and JD-aware. One adaptive follow-up per question. 3 questions per session. |
| C2 | **AI Evaluation** | Rubric scoring 1–5 per competency, per answer. Feedback must quote the student's own words. Recommendations included. Readiness updates after each session. |
| C3 | **Career Intelligence** | Readiness score, skill-gap analysis, weekly learning roadmap, personalized recommendations. |
| C4 | **Student Dashboard** | Interview history, readiness trend, competency scores, top weaknesses, learning progress. |

### 5.2 Extensions (only if core is done, deployed, and piloted)

| # | Capability | Notes |
|---|---|---|
| E1 | **Resume Intelligence** | PDF upload, parsing, skill extraction, resume summary, JD match %, improvement suggestions. |
| E2 | **Job Intelligence** | JD upload, required-skill extraction, resume comparison, company prep tips generated only from the JD text and user-pasted notes — no external data. |

### 5.3 Out of scope for now

Technical, SQL, AI-ML, and Case interview tracks · cohort analytics · RAG / vector search · voice interviews · mobile app · multi-model routing · streaming · prompt A/B testing. Everything here lives in the V2 roadmap with a reason for deferral.

## 6. How the readiness score works

The score is not a magic number — it's fully reconstructable from stored per-answer rubric scores.

**Inputs.** Each answer is scored 1–5 on rubric dimensions. Each dimension maps to one of five competencies:

`Communication · Structure · Depth/Role-Knowledge · Problem-Solving · Behavioral/STAR`

**Step 1 — Normalize.** Raw 1–5 score → 0–100: `norm = (raw - 1) / 4 * 100`

**Step 2 — Competency score (recency-weighted).** For each competency, an exponentially weighted moving average so recent practice counts more than old sessions:

```
C_k = Σ (w_i * norm_i) / Σ w_i,   where w_i = α^(age_i)
```

- `age_i` = how many answers ago (0 = most recent)
- Default `α = 0.6` — recent answers dominate, older ones fade but still count
- Why: a student who was weak three sessions ago but strong now should actually see that improvement in their score

**Step 3 — Readiness.** Weighted average of competency scores, per track:

| Competency | Behavioral | PM |
|---|:-:|:-:|
| Communication | 0.20 | 0.20 |
| Structure | 0.20 | 0.25 |
| Depth / Role-Knowledge | 0.15 | 0.20 |
| Problem-Solving | 0.15 | 0.25 |
| Behavioral / STAR | 0.30 | 0.10 |
| **Total** | **1.00** | **1.00** |

**Step 4 — Small-sample guard.** Below 5 completed sessions, don't show a band. Show **"Building baseline (n/5 sessions)"** with the number greyed out. This stops a student from over-trusting a score built on one or two answers.

**Step 5 — Bands.**

| Score | Band |
|---|---|
| < 50 | Building |
| 50–70 | Developing |
| 70–85 | Nearly Ready |
| 85+ | Interview Ready |

*"Why is this student a 72?"* — Structure (78) and Communication (81) are strong, but Problem-Solving (61) and Depth (58) drag the PM-weighted average down. The last two sessions improved Structure by 9 points, which is why 72 is up from 66. The score is fully auditable.

## 7. How we measure success

- **North star:** number of students reaching "Interview Ready"
- **Activation:** resume uploaded (or first JD added) and first interview completed
- **Engagement:** weekly active users; interviews per user per week
- **Quality:** average interview score; readiness improvement over time; post-session thumbs + short survey
- **Retention proxy:** % of activated users completing ≥5 sessions (crossing the small-sample guard)

Product metrics are a required deliverable. System observability (latency, token cost, error rate) is tracked separately — see [05-SYSTEM-ARCHITECTURE.md](05-SYSTEM-ARCHITECTURE.md).

## 8. The pilot

- **Who:** 20–30 students from the Consulting Club and Placement Cell
- **When:** as soon as the core loop is deployable — before polishing any extensions
- **Collect:** readiness improvement, completion rate, qualitative feedback
- **Deliverable:** a pilot report with at least one product change made because of what we heard

## 9. Cost and abuse controls

- Per-user daily caps on interviews and LLM calls (counters in Postgres)
- Per-endpoint rate limiting at the API layer
- Monthly cost estimate documented before public launch with a global spend ceiling

**Rough cost at pilot scale (~30 students):**

| Line item | Assumption | Monthly est. |
|---|---|---:|
| Claude tokens | ~240 interviews × ~$0.08/interview | ~$20 |
| App hosting | Render free → paid if needed | ~$0–13 |
| Postgres | Render free tier | ~$0–7 |
| LangSmith | Dev tier | $0 |
| **Total** | | **~$20–40/mo** |

## 10. Privacy and data

- Resumes and JDs are untrusted input — document text is data, not commands (prompt-injection defense)
- Sensitive user data is encrypted at rest
- **Delete-My-Data** endpoint (`DELETE /user/data`)
- Inactive resumes are auto-purged after 90 days

## 11. Definition of done

Public deployment · Google OAuth + JWT auth · responsive UI · Dockerized · CI/CD · OpenAPI docs · architecture docs · DB schema · this PRD · README with readiness formula, retention policy, and cost · unit + integration tests passing · production-grade error handling · no placeholder features · pilot with 20–30 users and a documented iteration · AI evaluation report · product metrics report · reflection and V2 roadmap.

## 12. What got cut and why

| Cut | Why |
|---|---|
| RAG / vector DB | Resume + JD fit in context. Retrieval adds ops burden and failure modes with no real user value at this scale. |
| More interview tracks | Two tracks done deeply beats five done shallowly. Adding a new track is one entry in `rubrics.py`. |
| Streaming / multi-model / A/B / fine-tuning | Complexity without pilot-stage payoff. LiteLLM keeps the model swappable without runtime overhead. |
| Redis | Postgres counters cover daily caps and rate limiting at pilot scale — one fewer service. |
| Cohort/admin analytics | Student value has to land first. Admin view is a fast V2 follow-on. |

## 13. Open questions

1. **Track rubric weights** — are the defaults in Section 6 the right ones, or do they need adjusting?
2. **α = 0.6** recency decay — is this the right feel for how quickly old sessions should fade?
3. **Guard at 5 sessions** — right threshold for the pilot, or lower to 3 so students see a band sooner?
4. **Answer length cap** — currently ~1,800 characters per answer for cost control. OK?
