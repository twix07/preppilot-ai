"""Interview Node — conducts the interview and asks adaptive follow-ups."""
from __future__ import annotations

from app.ai.llm import get_llm
from app.ai.prompts.interviewer import (
    build_followup_instruction,
    build_interviewer_system_prompt,
    build_question_instruction,
)
from app.ai.rubrics import get_rubric
from app.ai.state import InterviewState, telemetry_from


async def interview_node(state: InterviewState) -> InterviewState:
    rubric = get_rubric(state["track"])
    system = build_interviewer_system_prompt(
        rubric, state.get("resume_text", ""), state.get("jd_text", "")
    )
    if state.get("phase") == "followup":
        user = build_followup_instruction(state["main_question"], state.get("answer_text", ""))
    else:
        user = build_question_instruction(
            state.get("question_number", 1), state["main_question"]
        )

    result = await get_llm().complete(system=system, user=user, json_mode=False, max_tokens=300)
    state["interviewer_message"] = result.text
    state["llm"] = telemetry_from(result)
    return state
