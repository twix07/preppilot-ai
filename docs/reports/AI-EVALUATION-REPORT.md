# AI Evaluation Report

**Component under test:** the Evaluation Node — scores a candidate answer 1–5 on five rubric competencies and returns structured, quote-grounded feedback.
**Why this matters:** the readiness score is only as trustworthy as the evaluator. This report is the credibility deliverable — it shows the evaluator is *consistent, calibrated, and honest about its limits*.

> Reproduce: `cd backend && python -m tests.ai_eval.run_eval`
> Benchmark: [`backend/tests/ai_eval/benchmark.jsonl`](../../backend/tests/ai_eval/benchmark.jsonl)

---

## 1. Method

1. **Benchmark dataset.** Human-scored interview answers (behavioral + PM), spanning weak → strong, each labeled 1–5 on all five competencies. The committed starter set is 12 answers; the target for a defensible report is **30–50** (see *Limitations*).
2. **AI scoring.** Each answer is scored by the Evaluation Node with the production prompt and calibration settings.
3. **Repeated runs.** Each answer is scored **N=3** times to measure self-consistency.
4. **Metrics.**
   - **MAE** (mean absolute error vs. human) per competency, on the 1–5 scale.
   - **Exact-agreement %** and **within-1 %** (the operational bar — human raters themselves rarely agree to the exact point).
   - **Self-consistency** = mean standard deviation across the N repeated runs (0 = perfectly repeatable).

## 2. Results

Two configurations are reported.

### 2.1 Mock evaluator (deterministic, CI-runnable, free)
Run on the committed benchmark (12 answers × 3 repeats):

| Competency | n | MAE | Exact % | Within-1 % |
|---|--:|--:|--:|--:|
| communication | 12 | 0.83 | 33% | 83% |
| structure | 12 | 1.17 | 17% | 67% |
| depth | 12 | 0.75 | 33% | 92% |
| problem_solving | 12 | 0.83 | 25% | 92% |
| behavioral_star | 12 | 0.58 | 42% | 100% |

**Overall MAE ≈ 0.83 / 5.** **Self-consistency = 0.00** (the mock is deterministic by construction).

The mock exists so the product is demoable and CI-testable without spend; it is a heuristic, not the real model. Its value here is proving the *harness* works and giving a regression baseline. `structure` is its weakest dimension (MAE 1.17) because a keyword heuristic can't see framework quality — exactly the kind of judgment the real model adds.

### 2.2 Live Claude evaluator
Run `ANTHROPIC_API_KEY=... python -m tests.ai_eval.run_eval` to populate this table on the full 30–50 answer set. Report the same columns plus a short error analysis. *(Pending live run; harness and metrics identical.)*

## 3. Calibration changes made

| Change | Why | Effect |
|---|---|---|
| **Low temperature (0.2)** | Scoring should be stable, not creative | Higher self-consistency |
| **Structured JSON output** with a fixed schema | Eliminates parse ambiguity; forces a score for every competency | Robust persistence; no missing dimensions |
| **Explicit per-competency anchors** ("what a 5 looks like") in the prompt | Anchors reduce scale drift between answers | Better calibration vs. human |
| **Quote requirement** ("every improvement must cite the student's words") | Prevents generic feedback; makes feedback trustworthy and auditable | Feedback references the actual answer |
| **Coercion + neutral fallback** in code | Never crash on a malformed score; clamp to 1–5 | Production-grade robustness |

## 4. Known biases & how we watch for them

- **Verbosity bias.** Longer answers can read as "better." *Watch:* include short-but-excellent and long-but-empty answers in the benchmark; track MAE by answer length.
- **Position/leniency drift.** Scores can creep over a long session. *Watch:* anchors + independent per-answer scoring (no running context that inflates).
- **Track leakage.** PM answers shouldn't be scored by behavioral norms. *Mitigation:* the rubric + anchors are track-specific; the prompt names the track.

## 5. Strengths & weaknesses

**Strengths:** deterministic-mode reproducibility, structured output, quote-grounded feedback, fully auditable (readiness recomputable from stored per-answer scores).
**Weaknesses:** benchmark is currently small; live-model numbers pending; single human rater (no inter-rater agreement yet).

## 6. Next steps to make this bulletproof

1. Grow the benchmark to 30–50 answers with **two** human raters (report inter-rater agreement as the ceiling the AI is measured against).
2. Run the live Claude table and add an error analysis of the worst 5 disagreements.
3. Add the verbosity-bias regression (paired long/short answers) to CI.
