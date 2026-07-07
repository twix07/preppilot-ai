# PrepPilot AI — Database Schema

**Engine:** PostgreSQL. No embedding or vector tables — RAG is not used.

The design goal: store per-answer rubric scores so readiness can always be recomputed from source. Normalized (3NF); readiness is derived, never hand-entered.

---

## Entity relationships

```
users 1───∞ resumes
users 1───∞ job_descriptions
users 1───∞ interview_sessions
users 1───∞ readiness_scores
users 1───1 usage_counters

interview_sessions 1───∞ questions
questions          1───∞ answers            (question + follow-up = 2 answers)
answers            1───∞ answer_scores       (one row per rubric dimension, scored 1–5)

competencies       1───∞ answer_scores       (each dimension maps to a competency)
interview_sessions 1───∞ readiness_scores    (snapshot after each completed session)

resumes            0/1─── interview_sessions  (the resume used in that session)
job_descriptions   0/1─── interview_sessions  (the JD used in that session)

analytics_events   ∞───1 users               (append-only product and system events)
```

---

## Tables

### `users`
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| email | text unique not null | from Google OAuth |
| name | text | |
| google_sub | text unique | OAuth subject ID |
| created_at | timestamptz default now() | |
| last_active_at | timestamptz | used for retention purge |

### `resumes`
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK→users | scoped per user |
| raw_text | text (encrypted at rest) | parsed resume text |
| source | enum('paste','pdf') | |
| extracted_skills | jsonb | E1 output; null in Core |
| summary | text | E1 output; null in Core |
| created_at | timestamptz | |
| last_used_at | timestamptz | 90-day inactive purge |

### `job_descriptions`
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK→users | |
| raw_text | text | JD text (untrusted input) |
| company_notes | text | optional user-pasted notes (E2) |
| required_skills | jsonb | extracted (E2); null in Core |
| created_at | timestamptz | |

### `interview_sessions`
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK→users | |
| track | enum('behavioral','pm') | |
| resume_id | uuid FK→resumes null | context used in session |
| jd_id | uuid FK→job_descriptions null | context used in session |
| status | enum('in_progress','completed','abandoned') | |
| started_at | timestamptz | |
| completed_at | timestamptz null | |
| report | jsonb null | assembled interview report |

### `questions`
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| session_id | uuid FK→interview_sessions | |
| order_index | int | 1..3 |
| text | text | interviewer question |
| is_follow_up | bool | |
| parent_question_id | uuid null | links follow-up to its parent |
| created_at | timestamptz | |

### `answers`
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| question_id | uuid FK→questions | |
| session_id | uuid FK→interview_sessions | denormalized for fast reads |
| text | text | student's answer (length-capped at the API) |
| char_count | int | cost guardrail audit |
| feedback | jsonb | improvements (quoting the student) + recommendations |
| created_at | timestamptz | |

### `competencies`  (seed/reference table)
| column | type | notes |
|---|---|---|
| id | smallint PK | |
| key | text unique | communication, structure, depth, problem_solving, behavioral_star |
| name | text | display name |
| description | text | rubric anchor |

### `answer_scores`  (source of truth for readiness)
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| answer_id | uuid FK→answers | |
| competency_id | smallint FK→competencies | |
| dimension | text | rubric dimension label |
| raw_score | smallint check(1..5) | AI score |
| rationale | text | short explanation from the evaluator |
| created_at | timestamptz | |

Readiness is recomputable from `answer_scores` + track weights + `α`.

### `readiness_scores`  (snapshots for the trend line)
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK→users | |
| session_id | uuid FK→interview_sessions | snapshot taken after this session |
| track | enum('behavioral','pm') | |
| overall | numeric(5,2) | 0–100 |
| competency_breakdown | jsonb | {communication: 81, structure: 78, ...} |
| band | enum('building_baseline','building','developing','nearly_ready','interview_ready') | |
| session_count | int | for the small-sample guard |
| created_at | timestamptz | |

### `usage_counters`  (abuse prevention — replaces Redis)
| column | type | notes |
|---|---|---|
| user_id | uuid PK FK→users | |
| day | date PK | composite PK (user_id, day) |
| interviews_started | int default 0 | |
| llm_calls | int default 0 | |
| est_cost_usd | numeric(8,4) default 0 | spend tracking |

### `analytics_events`  (append-only)
| column | type | notes |
|---|---|---|
| id | bigserial PK | |
| user_id | uuid FK→users null | null for system events |
| type | text | 'activation', 'interview_completed', 'api_latency', etc. |
| payload | jsonb | metric-specific data |
| created_at | timestamptz | |

---

## Key DDL (illustrative — final version is in Alembic)

```sql
CREATE TABLE answer_scores (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  answer_id     uuid NOT NULL REFERENCES answers(id) ON DELETE CASCADE,
  competency_id smallint NOT NULL REFERENCES competencies(id),
  dimension     text NOT NULL,
  raw_score     smallint NOT NULL CHECK (raw_score BETWEEN 1 AND 5),
  rationale     text,
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_answer_scores_answer     ON answer_scores(answer_id);
CREATE INDEX idx_answer_scores_competency ON answer_scores(competency_id);
CREATE INDEX idx_readiness_user_created   ON readiness_scores(user_id, created_at);
CREATE INDEX idx_sessions_user_status     ON interview_sessions(user_id, status);
CREATE UNIQUE INDEX uq_usage_user_day     ON usage_counters(user_id, day);
```

---

## Integrity and privacy rules

- **Cascade delete** from `users` all the way down through resumes, JDs, sessions, questions, answers, answer_scores, and readiness_scores — this is what powers `DELETE /user/data`.
- **Encryption at rest** for `resumes.raw_text` (PII).
- **Retention:** a scheduled job purges resumes with `last_used_at < now() - 90 days`.
- Every read is scoped by `user_id` from the JWT — no cross-user access.

---

## Why this shape

- Per-dimension `answer_scores` makes readiness **auditable and recomputable** — you can answer "why is this student a 72?" and re-run the formula if weights or `α` change.
- `readiness_scores` snapshots make the **trend line** a cheap read on dashboard load, no recompute needed.
- `usage_counters` handles **daily caps and spend tracking** without Redis.
- Extension fields (`extracted_skills`, `required_skills`, `company_notes`) are **nullable** so the core ships without E1/E2 — extensions slot in without touching core table migrations.
