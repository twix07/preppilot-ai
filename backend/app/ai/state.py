"""Shared LangGraph state + telemetry helpers for the two-node interview graph."""
from __future__ import annotations

import json
import re
from typing import Any, TypedDict


class InterviewState(TypedDict, total=False):
    # routing (deterministic — set by the service, never by the model)
    mode: str  # "interview" | "evaluate"

    # context (resume/JD injected directly — no retrieval)
    track: str
    resume_text: str
    jd_text: str

    # interview-node inputs
    phase: str  # "question" | "followup"
    question_number: int
    main_question: str
    answer_text: str

    # evaluation-node inputs
    eval_question: str
    eval_answer: str

    # outputs
    interviewer_message: str
    evaluation: dict[str, Any]

    # telemetry (token/cost/latency) captured from the LLM call
    llm: dict[str, Any]


def telemetry_from(result: Any) -> dict[str, Any]:
    return {
        "model": result.model,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "latency_ms": result.latency_ms,
        "cost_usd": result.cost_usd,
        "mock": result.mock,
    }


def parse_json_object(text: str) -> dict[str, Any]:
    """Best-effort extraction of a JSON object from model output."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.S)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    raise ValueError("Model did not return valid JSON")
