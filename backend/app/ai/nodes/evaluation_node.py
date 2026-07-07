"""Evaluation Node — scores an answer against the rubric and returns structured feedback."""
from __future__ import annotations

from app.ai.llm import get_llm
from app.ai.prompts.evaluator import build_evaluator_system_prompt, build_evaluator_user_prompt
from app.ai.rubrics import get_rubric
from app.ai.state import InterviewState, parse_json_object, telemetry_from
from app.core.logging import get_logger

logger = get_logger("ai.evaluation_node")


def _coerce_scores(raw: dict, keys: list[str]) -> dict[str, int]:
    scores: dict[str, int] = {}
    src = raw.get("scores", {}) if isinstance(raw, dict) else {}
    for k in keys:
        try:
            v = int(round(float(src.get(k, 3))))
        except (TypeError, ValueError):
            v = 3
        scores[k] = max(1, min(5, v))
    return scores


async def evaluation_node(state: InterviewState) -> InterviewState:
    rubric = get_rubric(state["track"])
    keys = list(rubric.weights.keys())
    system = build_evaluator_system_prompt()
    user = build_evaluator_user_prompt(
        rubric,
        state["eval_question"],
        state["eval_answer"],
        state.get("resume_text", ""),
        state.get("jd_text", ""),
    )
    result = await get_llm().complete(system=system, user=user, json_mode=True, max_tokens=600)

    try:
        parsed = parse_json_object(result.text)
    except ValueError:
        logger.warning("Evaluator returned non-JSON; using neutral fallback.")
        parsed = {}

    scores = _coerce_scores(parsed, keys)
    rationales = parsed.get("rationales", {}) if isinstance(parsed, dict) else {}
    improvements = parsed.get("improvements") or [
        "Add a specific example and a measurable result to strengthen this answer."
    ]
    recommendations = parsed.get("recommendations") or [
        "Practice one structured answer (STAR/SCQA) and time it to under two minutes."
    ]

    state["evaluation"] = {
        "scores": scores,
        "rationales": {k: rationales.get(k, "") for k in keys},
        "improvements": improvements[:3],
        "recommendations": recommendations[:2],
    }
    state["llm"] = telemetry_from(result)
    return state
