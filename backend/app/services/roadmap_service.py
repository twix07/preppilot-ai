"""Career intelligence: skill-gap analysis, top weaknesses, weekly learning roadmap.

Derived deterministically from rubric weaknesses (+ JD required skills when present).
No extra LLM call — cheap, explainable, and consistent.
"""
from __future__ import annotations

from datetime import date

from app.ai.rubrics import COMPETENCY_NAME_BY_KEY

# Concrete, competency-specific coaching actions.
_ACTIONS: dict[str, list[str]] = {
    "communication": [
        "Record a 90-second answer and cut every filler word on the replay.",
        "Lead each answer with a one-sentence headline before the detail.",
    ],
    "structure": [
        "Use STAR (behavioral) or SCQA (PM) as an explicit skeleton for two answers.",
        "State your framework out loud before diving into content.",
    ],
    "depth": [
        "Add one concrete metric or specific detail to every claim you make.",
        "Prepare two stories with numbers you can quote from memory.",
    ],
    "problem_solving": [
        "For each answer, name one tradeoff you considered and why you chose your path.",
        "Practice thinking aloud: assumptions → options → decision.",
    ],
    "behavioral_star": [
        "Rewrite one story so Result is quantified and ownership is first-person ('I').",
        "Separate Situation/Task from Action so the arc is obvious.",
    ],
}


def top_weaknesses(competency_breakdown: dict[str, float], n: int = 2) -> list[dict]:
    scored = [(k, v) for k, v in competency_breakdown.items() if v > 0]
    scored.sort(key=lambda kv: kv[1])
    return [
        {"competency": k, "name": COMPETENCY_NAME_BY_KEY[k], "score": round(v, 1),
         "why": _weakness_reason(k)}
        for k, v in scored[:n]
    ]


def _weakness_reason(key: str) -> str:
    return {
        "communication": "Answers were harder to follow than they need to be.",
        "structure": "Answers lacked a clear, explicit framework.",
        "depth": "Answers stayed general and missed role-specific detail.",
        "problem_solving": "Reasoning and tradeoffs were not made explicit.",
        "behavioral_star": "STAR was incomplete — often missing a measured Result.",
    }.get(key, "This competency scored lowest in recent sessions.")


def skill_gaps(competency_breakdown: dict[str, float], jd_required_skills: list[str] | None) -> dict:
    weak = [COMPETENCY_NAME_BY_KEY[k] for k, v in sorted(
        competency_breakdown.items(), key=lambda kv: kv[1]) if 0 < v < 60]
    return {
        "from_rubric": weak[:3],
        "from_jd": (jd_required_skills or [])[:5],
    }


def weekly_roadmap(competency_breakdown: dict[str, float]) -> dict:
    focus = [k for k, _ in sorted(competency_breakdown.items(), key=lambda kv: kv[1])
             if competency_breakdown[k] > 0][:2]
    actions: list[str] = []
    for key in focus:
        actions.extend(_ACTIONS.get(key, [])[:1])
    if not actions:
        actions = ["Complete your first interview to unlock a personalized roadmap."]
    return {
        "week_of": _monday().isoformat(),
        "focus": [COMPETENCY_NAME_BY_KEY[k] for k in focus],
        "actions": actions,
    }


def _monday() -> date:
    today = date.today()
    return date.fromordinal(today.toordinal() - today.weekday())
