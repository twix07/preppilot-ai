# PrepPilot AI — UI Wireframes

Low-fidelity wireframes for all screens. Stack: Next.js + Tailwind + shadcn/ui + Recharts. Mobile-first — students practice between classes.

Screens map to routes in [06-FOLDER-STRUCTURE.md](06-FOLDER-STRUCTURE.md).

---

## S1 — Sign in (`/`)

```
┌──────────────────────────────────────────────┐
│  PrepPilot AI                                  │
│                                                │
│   Know if you're interview ready.              │
│   Practice against your resume + the job,      │
│   get scored, and watch yourself improve.      │
│                                                │
│        ┌────────────────────────────┐          │
│        │   G   Sign in with Google  │          │
│        └────────────────────────────┘          │
│                                                │
│   Behavioral · Product Management               │
└──────────────────────────────────────────────┘
```

---

## S2 — Dashboard (`/dashboard`)

```
┌───────────────────────────────────────────────────────────────┐
│ PrepPilot   [Dashboard] Interview  History  Settings     Tvisha│
├───────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────── Readiness ───────────┐   ┌──── This week ──────┐  │
│  │        ⌾  72 / 100               │   │ Focus: Structure,   │  │
│  │      NEARLY READY                │   │        Depth        │  │
│  │  (6 sessions — score is live)    │   │ • 2 PM sessions w/  │  │
│  │  ▲ +11 in last 30 days           │   │   SCQA opener       │  │
│  └──────────────────────────────────┘   │ • Add a metric to   │  │
│                                          │   every STAR answer │  │
│  ┌────────── Readiness trend ───────┐   └─────────────────────┘  │
│  │  100                             │                            │
│  │   75            ╭─╮   ╭──        │   ┌── Top weaknesses ───┐  │
│  │   50      ╭─╮╭─╯ ╰─╭─╯           │   │ Depth        58  ▁▁ │  │
│  │   25   ╭─╯ ╰╯      │             │   │ Problem-Solv 61  ▁▁▁│  │
│  │    0 ─────────────────────────►  │   │ Communication81  ▇▇ │  │
│  │      s1  s2  s3  s4  s5  s6       │   └─────────────────────┘  │
│  └──────────────────────────────────┘                            │
│                                                                  │
│  Competencies:  Comm ▇▇▇▇  Struct ▇▇▇▇  Depth ▇▇  Prob ▇▇▇ STAR ▇▇▇ │
│                                                                  │
│  [ ▶ Start interview ]      Recent: PM · 72 · Jul 5  →           │
└───────────────────────────────────────────────────────────────┘
```

Empty state (0 sessions): readiness card shows **"Building baseline (0/5)"** and one CTA: *"Add your resume or a JD and start your first interview."*

---

## S3 — Start interview (`/interview` — setup)

```
┌───────────────────────────────────────────────┐
│  Start a mock interview                         │
│                                                 │
│  Track:   ( • ) Behavioral   ( ) Product Mgmt   │
│                                                 │
│  Resume:  [ ▾ my_resume (paste)      ]  + Add   │
│  Job JD:  [ ▾ APM @ Acme (optional)  ]  + Add   │
│                                                 │
│  3 questions · 1 follow-up each · ~10 min       │
│                                                 │
│              [ Begin interview ▶ ]              │
└───────────────────────────────────────────────┘
```

"+ Add" opens a paste box (core) or PDF upload (E1). If no resume/JD is provided, the interview still runs — just generic — with a hint that adding them personalizes it.

---

## S4 — Interview turn (`/interview` — active)

```
┌───────────────────────────────────────────────────────────────┐
│  PM interview            Question 2 of 3        ● ● ○           │
├───────────────────────────────────────────────────────────────┤
│  Interviewer                                                    │
│  "Your resume mentions a 300-member club. Tell me about a       │
│   time you had to prioritize with limited resources."           │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Your answer…                                              │ │
│  │                                                           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                            1240 / 1800 chars     │
│                                        [ Submit answer → ]       │
│                                                                 │
│  (Scores are shown after the question — not during.)            │
└───────────────────────────────────────────────────────────────┘
```

After submit → loading → either a **follow-up** (same layout, interviewer text updates) or the **feedback card** (S5) then the next question.

---

## S5 — Feedback card (between questions and in the report)

```
┌──────────── Feedback · Question 1 ────────────┐
│  Structure        ●●●○○  3/5                    │
│  Communication    ●●●●○  4/5                    │
│  Behavioral/STAR  ●●○○○  2/5                    │
│                                                 │
│  Improve:                                       │
│  • You said "we improved the process" — say     │
│    what YOU did and by how much.                │
│  • Your Result had no number; add the metric    │
│    you moved.                                   │
│                                                 │
│  Try next: practice the SCQA opener.            │
│  👍 helpful   👎 not helpful                     │
└─────────────────────────────────────────────────┘
```

Feedback must always quote the student's own words — hard requirement. Thumbs feed the satisfaction metric.

---

## S6 — End of session report

```
┌───────────────────────────────────────────────┐
│  Session complete · PM · Jul 7                  │
│                                                 │
│  Readiness now: 72  (Nearly Ready)  ▲ +4        │
│                                                 │
│  Q1 ▸ Structure 3 · Comm 4 · STAR 2   [expand]  │
│  Q2 ▸ Structure 4 · Depth 3 · Prob 3  [expand]  │
│  Q3 ▸ …                                [expand]  │
│                                                 │
│  Top 2 fixes: Depth, Problem-Solving            │
│  [ Back to dashboard ]   [ Practice again ]     │
└───────────────────────────────────────────────┘
```

---

## S7 — History (`/history`)

```
┌───────────────────────────────────────────────┐
│  Interview history                              │
│  ┌───────────────────────────────────────────┐ │
│  │ Jul 7 · PM         · 72 · Nearly Ready  →  │ │
│  │ Jul 5 · Behavioral · 66 · Developing    →  │ │
│  │ Jul 2 · PM         · 61 · Developing    →  │ │
│  │ …                                          │ │
│  └───────────────────────────────────────────┘ │
└───────────────────────────────────────────────┘
```

---

## S8 — Settings (`/settings`)

```
┌───────────────────────────────────────────────┐
│  Settings                                       │
│  Account: tvisha@x.com  (Google)                │
│  Data retention: inactive resumes auto-deleted  │
│                  after 90 days.                  │
│                                                 │
│  ⚠ Delete my data  — removes everything,        │
│     permanently.            [ Delete my data ]  │
└───────────────────────────────────────────────┘
```

---

## S9 — Internal metrics (`/metrics`)

```
┌───────────────────────────────────────────────┐
│  System metrics (internal)                      │
│  API p95 latency … AI p95 latency …             │
│  Tokens today … Est. cost today … Error rate …  │
│  Interview completion % … Avg readiness Δ …      │
└───────────────────────────────────────────────┘
```

---

## Design notes

**One primary action per screen.** Dashboard → start interview. Interview → submit answer.

**Honest states.** "Building baseline (n/5)" until the guard clears — never show a fake band.

**Feedback feels personal.** Always quote the student. Scores hidden until after the question is complete.

**Mobile-first.** Single-column on phone; charts collapse to compact cards.

**shadcn/ui + Tailwind** for consistent, accessible primitives. **Recharts** for the trend line and competency bars.
