"""AI evaluation harness: compare the AI evaluator against human-scored answers.

Reports MAE, exact-agreement, within-1 agreement per competency, and self-consistency
across repeated runs. Works in mock mode (free) or live (set ANTHROPIC_API_KEY).

Run:  python -m tests.ai_eval.run_eval
Output: prints a summary and writes docs/reports/AI-EVALUATION-REPORT.generated.md
"""
from __future__ import annotations

import asyncio
import json
import statistics
from pathlib import Path

from app.ai.nodes.evaluation_node import evaluation_node
from app.ai.rubrics import COMPETENCY_KEYS

HERE = Path(__file__).parent
BENCH = HERE / "benchmark.jsonl"
REPORT = HERE.parents[2] / "docs" / "reports" / "AI-EVALUATION-REPORT.generated.md"


def _load() -> list[dict]:
    rows = []
    for line in BENCH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("//"):
            rows.append(json.loads(line))
    return rows


async def _ai_score(track: str, question: str, answer: str) -> dict[str, int]:
    state = {"mode": "evaluate", "track": track, "eval_question": question, "eval_answer": answer,
             "resume_text": "", "jd_text": ""}
    out = await evaluation_node(state)
    return out["evaluation"]["scores"]


async def main(repeats: int = 3) -> None:
    rows = _load()
    if not rows:
        print("No benchmark rows found.")
        return

    abs_err: dict[str, list[float]] = {k: [] for k in COMPETENCY_KEYS}
    exact: dict[str, int] = {k: 0 for k in COMPETENCY_KEYS}
    within1: dict[str, int] = {k: 0 for k in COMPETENCY_KEYS}
    n: dict[str, int] = {k: 0 for k in COMPETENCY_KEYS}
    self_consistency: list[float] = []

    for row in rows:
        runs = [await _ai_score(row["track"], row["question"], row["answer"])
                for _ in range(repeats)]
        # self-consistency = mean stdev across competencies for repeated runs
        for k in COMPETENCY_KEYS:
            vals = [r.get(k) for r in runs if r.get(k) is not None]
            if len(vals) > 1:
                self_consistency.append(statistics.pstdev(vals))
        ai = runs[0]
        human = row.get("human_scores", {})
        for k, hv in human.items():
            av = ai.get(k)
            if av is None:
                continue
            abs_err[k].append(abs(av - hv))
            exact[k] += int(av == hv)
            within1[k] += int(abs(av - hv) <= 1)
            n[k] += 1

    from app.core.config import settings

    lines = ["# AI Evaluation Report (generated)", "",
             f"Benchmark size: {len(rows)} answers · repeats/answer: {repeats}",
             f"Mode: {'mock' if settings.llm_mock_mode else 'live'} · model: {settings.llm_model}", "",
             "| Competency | n | MAE | Exact % | Within-1 % |",
             "|---|--:|--:|--:|--:|"]
    maes = []
    for k in COMPETENCY_KEYS:
        if n[k] == 0:
            continue
        mae = sum(abs_err[k]) / n[k]
        maes.append(mae)
        lines.append(
            f"| {k} | {n[k]} | {mae:.2f} | "
            f"{100*exact[k]/n[k]:.0f}% | {100*within1[k]/n[k]:.0f}% |"
        )
    overall_mae = sum(maes) / len(maes) if maes else 0.0
    sc = statistics.mean(self_consistency) if self_consistency else 0.0
    lines += ["", f"**Overall MAE:** {overall_mae:.2f} (on a 1–5 scale)",
              f"**Self-consistency (mean stdev across repeats):** {sc:.2f} "
              f"(0 = perfectly repeatable)", ""]

    report = "\n".join(lines)
    print(report)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")
    print(f"\nWrote {REPORT}")


if __name__ == "__main__":
    asyncio.run(main())
