# PrepPilot AI — User Personas

The core product is designed for one primary persona. A second persona validates some decisions. A third is explicitly V2 — listed so the scope stays honest.

---

## Persona 1 (primary) — Aarav, the anxious final-year student

| | |
|---|---|
| **Role** | Final-year engineering/commerce student, placement season in full swing |
| **Context** | Applying to 10–20 roles, a few PM/analyst/consulting targets in there. Gets one shot per company. |
| **Tech comfort** | High — lives on his laptop |
| **Emotional state** | Anxious, comparison-prone, genuinely unsure if he's good enough |

**What he's trying to do**
- Practice without burning a real opportunity or a mentor's limited time
- Get feedback that's specific to *his* answers and *his* target job, not generic tips
- Know concretely whether he's improving — not just feel like he is

**What frustrates him**
- Mentor mocks are scarce and feedback quality varies
- Generic AI tips don't tell him what *he* did wrong
- No idea if he's actually ready or just staying busy

**Jobs to be done**
- *When* I have an interview in two weeks, *I want to* practice against my resume and the JD and get scored, *so I can* know exactly what to fix first
- *When* I finish a session, *I want to* see my weak spots quoted back from my own answer, *so I can* trust the feedback enough to act on it
- *When* I've practiced for a while, *I want to* see a trend line, *so I can* feel — and prove — I'm improving

**What success looks like for Aarav:** he reaches "Nearly Ready" or "Interview Ready," walks into the real interview calm, and can name his top two things to fix.

The entire mandatory core is built for Aarav.

---

## Persona 2 (secondary, for validation) — Meera, the club mentor

| | |
|---|---|
| **Role** | Senior student mentor / T&P coordinator |
| **Context** | Runs mock interviews and prep sessions for a lot of students at once |
| **Tech comfort** | High |
| **Emotional state** | Stretched thin, wants leverage |

**What she's trying to do**
- Give consistent, high-quality prep to more students than she can personally reach
- Spend her limited time on high-value coaching, not first-pass mocks
- Have a shared record of who's actually ready

**What frustrates her**
- Can't scale herself — feedback quality slips when she's tired or rushed
- No way to track who's ready across the cohort

**Job to be done**
- *When* 40 students need mock interviews, *I want to* let the platform run the first-pass and score it, *so I can* focus my time where it actually matters

**How PrepPilot serves her in V1:** indirectly. She recommends PrepPilot as the "do this before you book time with me" step. A cohort admin view is V2 — student value has to land first.

---

## Persona 3 (V2 only, out of scope) — Placement Cell Admin

Wants cohort-level readiness dashboards, export to spreadsheets, and reporting visibility across all students. Explicitly deferred to V2. Listed here only to keep the scope discipline visible.

---

## What these personas force into the product

1. **Feedback must quote the user** — Aarav only trusts and acts on feedback that's specific to what he said. Hard requirement on the Evaluation Node.
2. **Trend must be visible and honest** — "Am I improving?" is Aarav's core emotional need. Readiness trend plus a small-sample guard so we don't lie early.
3. **Resume + JD as first-class inputs** — both Aarav and Meera think in terms of a specific job. Context-aware interview, not generic.
4. **Low friction** — Aarav practices between classes. Responsive UI, short sessions (3 questions).
5. **Don't over-serve the admin** — resist building cohort analytics before the student loop is working well.
