"""Seed demo data so the dashboard looks alive on first load.

Plays complete interviews through the REAL service (mock LLM) so every session
produces genuine questions, answers, per-answer rubric scores, and readiness
snapshots — nothing is faked. Answer quality improves across sessions so the
trend line rises (demonstrating the recency-weighted formula).

Run:  python -m app.seed
"""
from __future__ import annotations

import asyncio

from app.db.session import SessionLocal, init_db
from app.services.auth_service import AuthService
from app.services.interview_service import InterviewService

DEMO_EMAIL = "demo@preppilot.ai"

# Answer sets, weakest -> strongest, so readiness trends upward across sessions.
WEAK = "We did a project and it went okay I think."
OKAY = (
    "In my club we ran a workshop. I organized the schedule and reached out to speakers, "
    "and most people said it was useful."
)
GOOD = (
    "Situation: our 300-member club had low workshop attendance. Task: I owned turning it "
    "around. Action: I redesigned the format, personally recruited 4 alumni speakers, and "
    "ran a referral push. Result: attendance rose 60% because we matched topics to demand, "
    "which was the key tradeoff we debated."
)
STRONG = (
    "Situation: internship conversion was stuck at 20%. Task: as placement head I led the fix. "
    "Action: I built a mock-interview program, personally ran 30 sessions, and instrumented a "
    "readiness tracker. Result: conversion rose to 34% in one cycle. I chose depth over breadth "
    "because focused feedback beat generic prep — that tradeoff drove the outcome."
)

# Each session = 6 answers (3 questions x [main, follow-up]).
SESSIONS = [
    ("behavioral", [WEAK, WEAK, OKAY, WEAK, OKAY, OKAY]),
    ("behavioral", [OKAY, OKAY, GOOD, OKAY, GOOD, GOOD]),
    ("pm", [GOOD, GOOD, GOOD, OKAY, GOOD, STRONG]),
    ("pm", [GOOD, STRONG, STRONG, GOOD, STRONG, STRONG]),
    ("behavioral", [STRONG, STRONG, STRONG, STRONG, STRONG, STRONG]),
]


async def _play_session(user_id: str, track: str, answers: list[str]) -> None:
    async with SessionLocal() as db:
        svc = InterviewService(db)
        started = await svc.start(user_id, track, None, None)
        session_id = started["session_id"]
        question_id = started["question"]["id"]
        for ans in answers:
            result = await svc.submit_answer(user_id, session_id, question_id, ans)
            if result.get("state") == "completed":
                break
            question_id = result["question"]["id"]


async def main() -> None:
    await init_db()
    async with SessionLocal() as db:
        user, _ = await AuthService(db).dev_login(DEMO_EMAIL, "Demo Student")
        user_id = user.id
    for track, answers in SESSIONS:
        await _play_session(user_id, track, answers)
    print(f"Seeded {len(SESSIONS)} demo interviews for {DEMO_EMAIL}.")
    print("Sign in via dev-login with that email to see a live dashboard + trend.")


if __name__ == "__main__":
    asyncio.run(main())
